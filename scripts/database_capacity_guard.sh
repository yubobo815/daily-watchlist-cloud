#!/usr/bin/env bash
set -euo pipefail

mode="${1:-}"
: "${SUPABASE_DB_URL:?SUPABASE_DB_URL is required}"

readonly WARNING_BYTES=175000000
readonly STAGING_LIMIT_BYTES=220000000
readonly HARD_LIMIT_BYTES=250000000
readonly MAX_TICKERS=250
readonly OHLCV_BARS_PER_TICKER=400
readonly OHLCV_MAX_ROWS=100000
readonly LEARNING_SESSIONS=100
readonly BEHAVIOR_ROWS_PER_TICKER=30
readonly RUN_RETENTION_DAYS=60
readonly STAGE_TTL_HOURS=6
readonly CALIBRATION_MAX_ARTIFACTS=8
readonly CALIBRATION_MAX_BYTES=8000000
readonly SNAPSHOT_MAX_ROWS=750
readonly BEHAVIOR_MAX_ROWS=15000
readonly OUTCOME_MAX_ROWS=20000
readonly LEARNING_STATE_MAX_ROWS=1000
readonly INDICATOR_STATE_MAX_ROWS=500
readonly REFRESH_RUN_MAX_ROWS=125
readonly OHLCV_MAX_BYTES=65000000
readonly SNAPSHOT_MAX_BYTES=12000000
readonly BEHAVIOR_MAX_BYTES=65000000
readonly OUTCOME_MAX_BYTES=45000000
readonly LEARNING_STATE_MAX_BYTES=6000000
readonly INDICATOR_STATE_MAX_BYTES=4000000
readonly REFRESH_RUN_MAX_BYTES=4000000
# Conservative upper bound for one complete non-OHLCV staged publication.
readonly MAX_STAGED_PUBLICATION_BYTES=95000000
readonly LOCK_KEY=741852963

metadata_value() {
  local key="$1"
  if [ ! -f daily_watchlist_run_metadata_latest.json ]; then
    return 0
  fi
  python3 -c "import json; print(json.load(open('daily_watchlist_run_metadata_latest.json')).get('$key') or '')"
}

database_bytes() {
  psql "$SUPABASE_DB_URL" -At -v ON_ERROR_STOP=1 -c "select pg_database_size(current_database())"
}

trim_ohlcv() {
  psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 \
    -v lock_key="$LOCK_KEY" \
    -v per_ticker="$OHLCV_BARS_PER_TICKER" \
    -v max_rows="$OHLCV_MAX_ROWS" <<'SQL'
begin;
select pg_advisory_xact_lock(:lock_key);
delete from public.watchlist_ohlcv target
using (
  select ctid
  from (
    select ctid, row_number() over (partition by ticker order by data_date desc) as position
    from public.watchlist_ohlcv
  ) ranked
  where position > :per_ticker
) expired
where target.ctid = expired.ctid;
delete from public.watchlist_ohlcv target
using (
  select ctid
  from public.watchlist_ohlcv
  order by data_date desc, ticker
  offset :max_rows
) expired
where target.ctid = expired.ctid;
commit;
SQL
}

reap_incomplete_publications() {
  psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 \
    -v lock_key="$LOCK_KEY" \
    -v ttl_hours="$STAGE_TTL_HOURS" <<'SQL'
begin;
select pg_advisory_xact_lock(:lock_key);
create temporary table expired_publications on commit drop as
select publication_id
from public.watchlist_refresh_runs
where status in ('publishing', 'pending_audit', 'validated', 'sync_failed')
  and created_at < now() - make_interval(hours => :ttl_hours);
delete from public.watchlist_behavior_history using expired_publications
where watchlist_behavior_history.publication_id = expired_publications.publication_id;
delete from public.watchlist_snapshots using expired_publications
where watchlist_snapshots.publication_id = expired_publications.publication_id;
delete from public.watchlist_signal_outcomes using expired_publications
where watchlist_signal_outcomes.publication_id = expired_publications.publication_id;
delete from public.watchlist_learning_state using expired_publications
where watchlist_learning_state.publication_id = expired_publications.publication_id;
delete from public.watchlist_indicator_state using expired_publications
where watchlist_indicator_state.publication_id = expired_publications.publication_id;
delete from public.watchlist_calibration_artifacts using expired_publications
where watchlist_calibration_artifacts.source_publication_id = expired_publications.publication_id;
delete from public.watchlist_refresh_runs using expired_publications
where watchlist_refresh_runs.publication_id = expired_publications.publication_id;
commit;
SQL
}

rollback_publication() {
  local publication_id="$1"
  [ -n "$publication_id" ] || return 0
  psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 \
    -v lock_key="$LOCK_KEY" \
    -v publication_id="$publication_id" <<'SQL'
begin;
select pg_advisory_xact_lock(:lock_key);
create temporary table rollback_publication on commit drop as
select :'publication_id'::text as publication_id
where not exists (
  select 1
  from public.watchlist_publication_control
  where control_key = 'active' and active_publication_id = :'publication_id'
);
delete from public.watchlist_behavior_history using rollback_publication
where watchlist_behavior_history.publication_id = rollback_publication.publication_id;
delete from public.watchlist_snapshots using rollback_publication
where watchlist_snapshots.publication_id = rollback_publication.publication_id;
delete from public.watchlist_signal_outcomes using rollback_publication
where watchlist_signal_outcomes.publication_id = rollback_publication.publication_id;
delete from public.watchlist_learning_state using rollback_publication
where watchlist_learning_state.publication_id = rollback_publication.publication_id;
delete from public.watchlist_indicator_state using rollback_publication
where watchlist_indicator_state.publication_id = rollback_publication.publication_id;
delete from public.watchlist_calibration_artifacts using rollback_publication
where watchlist_calibration_artifacts.source_publication_id = rollback_publication.publication_id;
delete from public.watchlist_refresh_runs using rollback_publication
where watchlist_refresh_runs.publication_id = rollback_publication.publication_id;
commit;
SQL
}

assert_capacity() {
  local ceiling="$1"
  local phase="$2"
  local bytes tickers ohlcv_rows calibration_bytes
  bytes="$(database_bytes)"
  tickers="$(psql "$SUPABASE_DB_URL" -At -v ON_ERROR_STOP=1 -c "select count(distinct ticker) from public.watchlist_ohlcv")"
  ohlcv_rows="$(psql "$SUPABASE_DB_URL" -At -v ON_ERROR_STOP=1 -c "select count(*) from public.watchlist_ohlcv")"
  echo "Database capacity [$phase]: bytes=$bytes ceiling=$ceiling tickers=$tickers ohlcv_rows=$ohlcv_rows"
  if [ "$tickers" -gt "$MAX_TICKERS" ]; then
    echo "Ticker capacity exceeded: $tickers > $MAX_TICKERS"
    return 1
  fi
  if [ "$ohlcv_rows" -gt "$OHLCV_MAX_ROWS" ]; then
    echo "OHLCV row capacity exceeded: $ohlcv_rows > $OHLCV_MAX_ROWS"
    return 1
  fi
  local snapshots behavior outcomes learning_state indicator_state refresh_runs
  snapshots="$(psql "$SUPABASE_DB_URL" -At -v ON_ERROR_STOP=1 -c "select count(*) from public.watchlist_snapshots")"
  behavior="$(psql "$SUPABASE_DB_URL" -At -v ON_ERROR_STOP=1 -c "select count(*) from public.watchlist_behavior_history")"
  outcomes="$(psql "$SUPABASE_DB_URL" -At -v ON_ERROR_STOP=1 -c "select count(*) from public.watchlist_signal_outcomes")"
  learning_state="$(psql "$SUPABASE_DB_URL" -At -v ON_ERROR_STOP=1 -c "select count(*) from public.watchlist_learning_state")"
  indicator_state="$(psql "$SUPABASE_DB_URL" -At -v ON_ERROR_STOP=1 -c "select count(*) from public.watchlist_indicator_state")"
  refresh_runs="$(psql "$SUPABASE_DB_URL" -At -v ON_ERROR_STOP=1 -c "select count(*) from public.watchlist_refresh_runs")"
  [ "$snapshots" -le "$SNAPSHOT_MAX_ROWS" ] || { echo "Snapshot row capacity exceeded: $snapshots > $SNAPSHOT_MAX_ROWS"; return 1; }
  [ "$behavior" -le "$BEHAVIOR_MAX_ROWS" ] || { echo "Behavior row capacity exceeded: $behavior > $BEHAVIOR_MAX_ROWS"; return 1; }
  [ "$outcomes" -le "$OUTCOME_MAX_ROWS" ] || { echo "Outcome row capacity exceeded: $outcomes > $OUTCOME_MAX_ROWS"; return 1; }
  [ "$learning_state" -le "$LEARNING_STATE_MAX_ROWS" ] || { echo "Learning-state row capacity exceeded: $learning_state > $LEARNING_STATE_MAX_ROWS"; return 1; }
  [ "$indicator_state" -le "$INDICATOR_STATE_MAX_ROWS" ] || { echo "Indicator-state row capacity exceeded: $indicator_state > $INDICATOR_STATE_MAX_ROWS"; return 1; }
  [ "$refresh_runs" -le "$REFRESH_RUN_MAX_ROWS" ] || { echo "Refresh-run row capacity exceeded: $refresh_runs > $REFRESH_RUN_MAX_ROWS"; return 1; }
  local ohlcv_bytes snapshot_bytes behavior_bytes outcome_bytes learning_bytes indicator_bytes refresh_bytes
  ohlcv_bytes="$(psql "$SUPABASE_DB_URL" -At -v ON_ERROR_STOP=1 -c "select pg_total_relation_size('public.watchlist_ohlcv')")"
  snapshot_bytes="$(psql "$SUPABASE_DB_URL" -At -v ON_ERROR_STOP=1 -c "select pg_total_relation_size('public.watchlist_snapshots')")"
  behavior_bytes="$(psql "$SUPABASE_DB_URL" -At -v ON_ERROR_STOP=1 -c "select pg_total_relation_size('public.watchlist_behavior_history')")"
  outcome_bytes="$(psql "$SUPABASE_DB_URL" -At -v ON_ERROR_STOP=1 -c "select pg_total_relation_size('public.watchlist_signal_outcomes')")"
  learning_bytes="$(psql "$SUPABASE_DB_URL" -At -v ON_ERROR_STOP=1 -c "select pg_total_relation_size('public.watchlist_learning_state')")"
  indicator_bytes="$(psql "$SUPABASE_DB_URL" -At -v ON_ERROR_STOP=1 -c "select pg_total_relation_size('public.watchlist_indicator_state')")"
  refresh_bytes="$(psql "$SUPABASE_DB_URL" -At -v ON_ERROR_STOP=1 -c "select pg_total_relation_size('public.watchlist_refresh_runs')")"
  if [ "$phase" = "preflight" ]; then
    local ohlcv_growth_reserve=$((OHLCV_MAX_BYTES - ohlcv_bytes))
    [ "$ohlcv_growth_reserve" -ge 0 ] || ohlcv_growth_reserve=0
    if [ $((bytes + ohlcv_growth_reserve + MAX_STAGED_PUBLICATION_BYTES)) -ge "$HARD_LIMIT_BYTES" ]; then
      echo "Insufficient reserved headroom: database=$bytes ohlcv_growth=$ohlcv_growth_reserve staged=$MAX_STAGED_PUBLICATION_BYTES hard_limit=$HARD_LIMIT_BYTES"
      return 1
    fi
  fi
  [ "$ohlcv_bytes" -le "$OHLCV_MAX_BYTES" ] || { echo "OHLCV byte capacity exceeded"; return 1; }
  [ "$snapshot_bytes" -le "$SNAPSHOT_MAX_BYTES" ] || { echo "Snapshot byte capacity exceeded"; return 1; }
  [ "$behavior_bytes" -le "$BEHAVIOR_MAX_BYTES" ] || { echo "Behavior byte capacity exceeded: $behavior_bytes > $BEHAVIOR_MAX_BYTES"; return 1; }
  [ "$outcome_bytes" -le "$OUTCOME_MAX_BYTES" ] || { echo "Outcome byte capacity exceeded"; return 1; }
  [ "$learning_bytes" -le "$LEARNING_STATE_MAX_BYTES" ] || { echo "Learning-state byte capacity exceeded"; return 1; }
  [ "$indicator_bytes" -le "$INDICATOR_STATE_MAX_BYTES" ] || { echo "Indicator-state byte capacity exceeded"; return 1; }
  [ "$refresh_bytes" -le "$REFRESH_RUN_MAX_BYTES" ] || { echo "Refresh-run byte capacity exceeded"; return 1; }
  calibration_bytes="$(psql "$SUPABASE_DB_URL" -At -v ON_ERROR_STOP=1 -c "select pg_total_relation_size('public.watchlist_calibration_artifacts')")"
  if [ "$calibration_bytes" -ge "$CALIBRATION_MAX_BYTES" ]; then
    echo "Calibration artifact capacity exceeded: $calibration_bytes >= $CALIBRATION_MAX_BYTES"
    return 1
  fi
  if [ "$bytes" -ge "$ceiling" ] || [ "$bytes" -ge "$HARD_LIMIT_BYTES" ]; then
    echo "Database capacity exceeded during $phase: $bytes bytes"
    return 1
  fi
}

record_storage_metrics() {
  local publication_id="$1"
  [ -n "$publication_id" ] || return 0
  psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -v publication_id="$publication_id" <<'SQL'
with relation_metrics as (
  select jsonb_object_agg(
    relation_name,
    jsonb_build_object(
      'total_bytes', pg_total_relation_size(format('public.%I', relation_name)::regclass),
      'table_bytes', pg_relation_size(format('public.%I', relation_name)::regclass),
      'index_bytes', pg_indexes_size(format('public.%I', relation_name)::regclass)
    )
  ) as relations
  from (values
    ('watchlist_ohlcv'),
    ('watchlist_snapshots'),
    ('watchlist_behavior_history'),
    ('watchlist_signal_outcomes'),
    ('watchlist_learning_state'),
    ('watchlist_indicator_state'),
    ('watchlist_calibration_artifacts'),
    ('watchlist_refresh_runs'),
    ('watchlist_publication_control')
  ) tables(relation_name)
), row_metrics as (
  select jsonb_build_object(
    'ohlcv', (select count(*) from public.watchlist_ohlcv),
    'snapshots', (select count(*) from public.watchlist_snapshots),
    'behavior_history', (select count(*) from public.watchlist_behavior_history),
    'signal_outcomes', (select count(*) from public.watchlist_signal_outcomes),
    'learning_state', (select count(*) from public.watchlist_learning_state),
    'indicator_state', (select count(*) from public.watchlist_indicator_state),
    'calibration_artifacts', (select count(*) from public.watchlist_calibration_artifacts),
    'refresh_runs', (select count(*) from public.watchlist_refresh_runs),
    'publication_control', (select count(*) from public.watchlist_publication_control)
  ) as rows
)
update public.watchlist_refresh_runs
set payload = coalesce(payload, '{}'::jsonb) || jsonb_build_object(
  'storage', jsonb_build_object(
    'database_bytes', pg_database_size(current_database()),
    'warning_bytes', 175000000,
    'staging_limit_bytes', 220000000,
    'hard_limit_bytes', 250000000,
    'headroom_bytes', 250000000 - pg_database_size(current_database()),
    'measured_at', now(),
    'rows', row_metrics.rows,
    'relations', relation_metrics.relations
  )
)
from relation_metrics, row_metrics
where publication_id = :'publication_id';
SQL
}

final_retention() {
  local publication_id="$1"
  local run_date="$2"
  psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 \
    -v lock_key="$LOCK_KEY" \
    -v publication_id="$publication_id" \
    -v run_date="$run_date" \
    -v learning_sessions="$LEARNING_SESSIONS" \
    -v behavior_rows="$BEHAVIOR_ROWS_PER_TICKER" \
    -v calibration_artifacts="$CALIBRATION_MAX_ARTIFACTS" \
    -v run_days="$RUN_RETENTION_DAYS" <<'SQL'
begin;
select pg_advisory_xact_lock(:lock_key);
select 1 / count(*)
from public.watchlist_publication_control
where control_key = 'active' and active_publication_id = :'publication_id';

delete from public.watchlist_behavior_history
where publication_id <> :'publication_id';
delete from public.watchlist_behavior_history target
using (
  select ctid
  from (
    select ctid, row_number() over (partition by ticker order by history_date desc) as position
    from public.watchlist_behavior_history
    where publication_id = :'publication_id'
  ) ranked
  where position > :behavior_rows
) expired
where target.ctid = expired.ctid;

delete from public.watchlist_signal_outcomes
where publication_id <> :'publication_id';
delete from public.watchlist_signal_outcomes
where publication_id = :'publication_id'
  and evaluation_run_date not in (
    select evaluation_run_date
    from public.watchlist_signal_outcomes
    where publication_id = :'publication_id'
    group by evaluation_run_date
    order by evaluation_run_date desc
    limit :learning_sessions
  );

delete from public.watchlist_learning_state
where publication_id <> :'publication_id';
delete from public.watchlist_indicator_state
where publication_id <> :'publication_id';

delete from public.watchlist_calibration_artifacts
where state in ('staged', 'rejected')
  and created_at < now() - make_interval(hours => 6);
delete from public.watchlist_calibration_artifacts target
using (
  select artifact_id
  from public.watchlist_calibration_artifacts
  where state = 'validated'
  order by cutoff_date desc, created_at desc
  offset :calibration_artifacts
) expired
where target.artifact_id = expired.artifact_id;

create temporary table retained_snapshots on commit drop as
select publication_id
from public.watchlist_publication_control control
cross join lateral unnest(array[control.active_publication_id, control.previous_publication_id]) publication_id
where control.control_key = 'active' and publication_id is not null;
delete from public.watchlist_snapshots
where publication_id not in (select publication_id from retained_snapshots);

delete from public.watchlist_refresh_runs
where run_date < :'run_date'::date - :run_days
  and publication_id not in (select publication_id from retained_snapshots)
  and publication_id not in (
    select source_publication_id from public.watchlist_calibration_artifacts
  )
  and publication_id <> :'publication_id';
commit;
SQL
  trim_ohlcv
  psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -c "vacuum (analyze) public.watchlist_ohlcv, public.watchlist_snapshots, public.watchlist_behavior_history, public.watchlist_signal_outcomes, public.watchlist_learning_state, public.watchlist_indicator_state, public.watchlist_calibration_artifacts, public.watchlist_refresh_runs"
}

reconcile_active_retention() {
  local active_publication_id active_run_date
  active_publication_id="$(psql "$SUPABASE_DB_URL" -At -v ON_ERROR_STOP=1 -c \
    "select active_publication_id from public.watchlist_publication_control where control_key = 'active'")"
  [ -n "$active_publication_id" ] || return 0
  active_run_date="$(psql "$SUPABASE_DB_URL" -At -v ON_ERROR_STOP=1 \
    -v publication_id="$active_publication_id" <<'SQL'
select run_date
from public.watchlist_refresh_runs
where publication_id = :'publication_id'
limit 1;
SQL
)"
  [ -n "$active_run_date" ] || {
    echo "Active publication $active_publication_id has no refresh-run metadata."
    return 1
  }
  final_retention "$active_publication_id" "$active_run_date"
}

publication_id="$(metadata_value publication_id)"
run_date="$(metadata_value run_date)"

case "$mode" in
  prepare)
    reap_incomplete_publications
    reconcile_active_retention
    trim_ohlcv
    psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -c "vacuum (analyze) public.watchlist_ohlcv, public.watchlist_snapshots, public.watchlist_behavior_history, public.watchlist_signal_outcomes, public.watchlist_learning_state, public.watchlist_indicator_state, public.watchlist_calibration_artifacts, public.watchlist_refresh_runs"
    assert_capacity "$WARNING_BYTES" "preflight"
    ;;
  staged)
    trim_ohlcv
    if ! assert_capacity "$STAGING_LIMIT_BYTES" "staged"; then
      rollback_publication "$publication_id"
      exit 1
    fi
    record_storage_metrics "$publication_id"
    ;;
  finalize)
    final_retention "$publication_id" "$run_date"
    assert_capacity "$STAGING_LIMIT_BYTES" "finalized"
    record_storage_metrics "$publication_id"
    ;;
  rollback)
    rollback_publication "$publication_id"
    reap_incomplete_publications
    trim_ohlcv
    psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -c "vacuum (analyze) public.watchlist_ohlcv, public.watchlist_snapshots, public.watchlist_behavior_history, public.watchlist_signal_outcomes, public.watchlist_learning_state, public.watchlist_indicator_state, public.watchlist_calibration_artifacts, public.watchlist_refresh_runs"
    assert_capacity "$HARD_LIMIT_BYTES" "rollback"
    ;;
  *)
    echo "Usage: $0 {prepare|staged|finalize|rollback}" >&2
    exit 2
    ;;
esac
