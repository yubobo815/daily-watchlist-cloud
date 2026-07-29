-- Raw OHLCV is intentionally compact: one canonical row per ticker/session.
-- Indicators and signal payloads are derived at runtime and never stored here.
create table if not exists public.watchlist_ohlcv (
  ticker text not null,
  data_date date not null,
  open double precision not null,
  high double precision not null,
  low double precision not null,
  close double precision not null,
  adjclose double precision,
  volume double precision not null,
  data_provider text,
  updated_at timestamptz not null default now(),
  primary key (ticker, data_date)
);

create index if not exists watchlist_ohlcv_data_date_idx
  on public.watchlist_ohlcv (data_date);

grant select, insert, update, delete on public.watchlist_ohlcv to service_role;

create table if not exists public.watchlist_snapshots (
  publication_id text not null,
  run_date date not null,
  ticker text not null,
  name text,
  data_date date,
  action text,
  setup text,
  adaptive_mode text,
  psychology text,
  score numeric,
  open numeric,
  high numeric,
  low numeric,
  close numeric,
  day_change_pct numeric,
  entry_est numeric,
  stop_est numeric,
  target_est numeric,
  notes text,
  signal_stage text,
  transition_label text,
  transition_score numeric,
  signal_age_days integer,
  price_progress_since_signal_pct numeric,
  freshness_penalty numeric,
  adjusted_score numeric,
  distance_from_ref_zone_pct numeric,
  extension_state text,
  next_day_bias text,
  next_day_bias_score numeric,
  next_day_plan text,
  emotion_score numeric,
  trend_location_score numeric,
  setup_context_score numeric,
  transition_edge_score numeric,
  personality_weight_label text,
  personality_weight_emotion numeric,
  personality_weight_transition numeric,
  personality_weight_setup numeric,
  personality_weight_trend numeric,
  operator_pressure text,
  operator_pressure_score numeric,
  operator_plan text,
  operator_state text,
  operator_state_score numeric,
  operator_state_plan text,
  demand_control_score numeric,
  bull_trap_score numeric,
  bear_trap_score numeric,
  distribution_score numeric,
  absorption_score numeric,
  short_pressure_proxy numeric,
  squeeze_watch text,
  anti_signal_score numeric,
  anti_signal_level text,
  anti_signal_plan text,
  last_outcome_label text,
  last_outcome_score numeric,
  last_outcome_reason text,
  last_outcome_return_pct numeric,
  learning_sample_count integer,
  learning_working_rate numeric,
  learning_failed_rate numeric,
  learning_trap_avoided_rate numeric,
  learning_avg_score numeric,
  learning_adjustment numeric,
  learning_scope text,
  learning_key_used text,
  learning_plan text,
  learning_model_version text,
  learning_distinct_ticker_count integer,
  learning_evaluation_date_count integer,
  learning_evaluation_date_min date,
  learning_evaluation_date_max date,
  learning_window_start date,
  learning_window_end date,
  learning_promotion_eligible boolean,
  learning_reporting_only boolean,
  learning_promotion_state text,
  prediction_horizon_sessions integer,
  prediction_upside_probability numeric,
  prediction_downside_probability numeric,
  prediction_no_edge_probability numeric,
  prediction_confidence numeric,
  prediction_model_version text,
  prediction_state text,
  data_provider text,
  data_provider_status text,
  data_provider_latency_ms numeric,
  data_provider_error text,
  data_age_days integer,
  freshness_status text,
  freshness_block text,
  freshness_plan text,
  buy_tier text,
  execution_priority integer,
  execution_plan text,
  feedback_window_days integer,
  feedback_return_pct numeric,
  feedback_max_drawdown_pct numeric,
  feedback_stop_hit text,
  feedback_quality text,
  feedback_plan text,
  reason_codes jsonb not null default '[]'::jsonb,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (publication_id, ticker)
);

create table if not exists public.watchlist_behavior_history (
  publication_id text not null,
  run_date date not null,
  ticker text not null,
  history_date date not null,
  action text,
  setup text,
  adaptive_mode text,
  psychology text,
  score numeric,
  open numeric,
  high numeric,
  low numeric,
  close numeric,
  day_change_pct numeric,
  entry_est numeric,
  stop_est numeric,
  target_est numeric,
  notes text,
  signal_stage text,
  transition_label text,
  transition_score numeric,
  signal_age_days integer,
  price_progress_since_signal_pct numeric,
  freshness_penalty numeric,
  adjusted_score numeric,
  distance_from_ref_zone_pct numeric,
  extension_state text,
  next_day_bias text,
  next_day_bias_score numeric,
  next_day_plan text,
  emotion_score numeric,
  trend_location_score numeric,
  setup_context_score numeric,
  transition_edge_score numeric,
  personality_weight_label text,
  personality_weight_emotion numeric,
  personality_weight_transition numeric,
  personality_weight_setup numeric,
  personality_weight_trend numeric,
  operator_pressure text,
  operator_pressure_score numeric,
  operator_plan text,
  operator_state text,
  operator_state_score numeric,
  operator_state_plan text,
  demand_control_score numeric,
  bull_trap_score numeric,
  bear_trap_score numeric,
  distribution_score numeric,
  absorption_score numeric,
  short_pressure_proxy numeric,
  squeeze_watch text,
  anti_signal_score numeric,
  anti_signal_level text,
  anti_signal_plan text,
  last_outcome_label text,
  last_outcome_score numeric,
  last_outcome_reason text,
  last_outcome_return_pct numeric,
  learning_sample_count integer,
  learning_working_rate numeric,
  learning_failed_rate numeric,
  learning_trap_avoided_rate numeric,
  learning_avg_score numeric,
  learning_adjustment numeric,
  learning_scope text,
  learning_key_used text,
  learning_plan text,
  learning_model_version text,
  learning_distinct_ticker_count integer,
  learning_evaluation_date_count integer,
  learning_evaluation_date_min date,
  learning_evaluation_date_max date,
  learning_window_start date,
  learning_window_end date,
  learning_promotion_eligible boolean,
  learning_reporting_only boolean,
  learning_promotion_state text,
  prediction_horizon_sessions integer,
  prediction_upside_probability numeric,
  prediction_downside_probability numeric,
  prediction_no_edge_probability numeric,
  prediction_confidence numeric,
  prediction_model_version text,
  prediction_state text,
  data_provider text,
  data_provider_status text,
  data_provider_latency_ms numeric,
  data_provider_error text,
  data_age_days integer,
  freshness_status text,
  freshness_block text,
  freshness_plan text,
  buy_tier text,
  execution_priority integer,
  execution_plan text,
  feedback_window_days integer,
  feedback_return_pct numeric,
  feedback_max_drawdown_pct numeric,
  feedback_stop_hit text,
  feedback_quality text,
  feedback_plan text,
  reason_codes jsonb not null default '[]'::jsonb,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (publication_id, ticker, history_date)
);

create table if not exists public.watchlist_refresh_runs (
  publication_id text primary key,
  run_date date not null,
  status text not null default 'ok',
  live_access_ok boolean,
  live_access_message text,
  earliest_data_date date,
  latest_data_date date,
  symbols_total integer,
  symbols_analyzed integer,
  symbols_failed integer,
  symbols_stale_cache integer,
  snapshot_rows integer,
  history_rows integer,
  learning_history_rows integer,
  scanner_version text,
  notes text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.watchlist_publication_control (
  control_key text primary key default 'active' check (control_key = 'active'),
  active_publication_id text,
  previous_publication_id text,
  generation bigint not null default 0,
  activated_at timestamptz,
  updated_at timestamptz not null default now()
);

drop function if exists public.activate_watchlist_publication(text);
create or replace function public.activate_watchlist_publication(
  p_publication_id text,
  p_expected_generation bigint
)
returns table(active_publication_id text, generation bigint)
language plpgsql
security definer
set search_path = ''
as $$
declare
  prior_publication_id text;
  final_status text;
begin
  perform pg_advisory_xact_lock(741852963);
  if coalesce((
    select control.generation
    from public.watchlist_publication_control control
    where control.control_key = 'active'
  ), 0) <> p_expected_generation then
    raise exception 'Publication generation changed; expected %', p_expected_generation;
  end if;
  select payload->>'scanner_status'
    into final_status
  from public.watchlist_refresh_runs
  where publication_id = p_publication_id
    and status = 'validated'
    and payload->>'sync_state' = 'complete'
  for update;
  if final_status is null or final_status not in ('ok', 'degraded') then
    raise exception 'Publication % is not validated for activation', p_publication_id;
  end if;

  select control.active_publication_id
    into prior_publication_id
  from public.watchlist_publication_control control
  where control.control_key = 'active'
  for update;

  update public.watchlist_refresh_runs
  set status = final_status, updated_at = now()
  where publication_id = p_publication_id;

  insert into public.watchlist_publication_control (
    control_key, active_publication_id, previous_publication_id,
    generation, activated_at, updated_at
  ) values (
    'active', p_publication_id, prior_publication_id, 1, now(), now()
  )
  on conflict (control_key) do update set
    previous_publication_id = public.watchlist_publication_control.active_publication_id,
    active_publication_id = excluded.active_publication_id,
    generation = public.watchlist_publication_control.generation + 1,
    activated_at = now(),
    updated_at = now();

  return query
  select control.active_publication_id, control.generation
  from public.watchlist_publication_control control
  where control.control_key = 'active';
end;
$$;

revoke all on function public.activate_watchlist_publication(text, bigint) from public, anon, authenticated;
grant execute on function public.activate_watchlist_publication(text, bigint) to service_role;

create table if not exists public.watchlist_signal_outcomes (
  publication_id text not null,
  signal_run_date date not null,
  evaluation_run_date date not null,
  ticker text not null,
  prior_action text,
  prior_setup text,
  prior_buy_tier text,
  prior_operator_state text,
  prior_anti_signal_level text,
  prior_prediction_upside_probability numeric,
  prior_prediction_downside_probability numeric,
  prior_prediction_no_edge_probability numeric,
  prior_prediction_confidence numeric,
  prior_prediction_state text,
  prior_prediction_key text,
  prior_prediction_scope text,
  prior_close numeric,
  entry_model_version text,
  entry_eligible boolean,
  entry_filled boolean,
  forecast_learnable boolean,
  entry_fill_est numeric,
  current_action text,
  current_operator_state text,
  current_close numeric,
  close_return_pct numeric,
  outcome_label text,
  outcome_score numeric,
  outcome_reason text,
  learning_key text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (publication_id, signal_run_date, evaluation_run_date, ticker)
);

create table if not exists public.focus_tickers (
  list_id text not null default 'default',
  ticker text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (list_id, ticker)
);

create index if not exists watchlist_snapshots_ticker_run_date_idx
  on public.watchlist_snapshots (ticker, run_date desc);

create index if not exists watchlist_snapshots_action_score_idx
  on public.watchlist_snapshots (run_date desc, action, score desc);

create index if not exists watchlist_behavior_history_ticker_date_idx
  on public.watchlist_behavior_history (ticker, history_date desc);

create index if not exists watchlist_behavior_history_ticker_run_date_idx
  on public.watchlist_behavior_history (ticker, run_date desc);

create index if not exists watchlist_refresh_runs_status_idx
  on public.watchlist_refresh_runs (run_date desc, status);

create index if not exists watchlist_signal_outcomes_eval_idx
  on public.watchlist_signal_outcomes (evaluation_run_date desc, outcome_label);

create index if not exists watchlist_signal_outcomes_ticker_idx
  on public.watchlist_signal_outcomes (ticker, evaluation_run_date desc);

-- Publication-scoped aggregates are cheap to replace atomically each day.
-- Canonical outcomes remain the source of truth; this table is the serving
-- state used to audit that only newly settled samples changed the window.
create table if not exists public.watchlist_learning_state (
  publication_id text not null,
  run_date date not null,
  learning_key text not null,
  scope text not null,
  model_version text not null,
  horizon_sessions integer not null,
  sample_count integer not null default 0,
  working_rate numeric,
  failed_rate numeric,
  trap_avoided_rate numeric,
  distinct_ticker_count integer not null default 0,
  evaluation_date_count integer not null default 0,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (publication_id, learning_key, scope),
  check (horizon_sessions > 0),
  check (sample_count >= 0)
);

create index if not exists watchlist_learning_state_run_idx
  on public.watchlist_learning_state (run_date desc, model_version, horizon_sessions);

create table if not exists public.watchlist_indicator_state (
  publication_id text not null,
  ticker text not null,
  data_date date not null,
  state_version text not null,
  scanner_version text not null,
  raw_window_hash text not null,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (publication_id, ticker)
);

create index if not exists watchlist_indicator_state_date_idx
  on public.watchlist_indicator_state (data_date desc, ticker);

-- Weekly rebuilds write immutable fitted bundles. A daily scan may consume an
-- artifact only when its source publication is also committed ok/degraded.
create table if not exists public.watchlist_calibration_artifacts (
  artifact_id text primary key,
  source_publication_id text not null,
  cutoff_date date not null,
  artifact_version text not null,
  scanner_version text not null,
  learning_model_version text not null,
  directional_model_version text not null,
  content_hash text not null,
  state text not null default 'staged',
  payload_bytes integer not null,
  payload jsonb not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (state in ('staged', 'validated', 'rejected')),
  check (payload_bytes > 0 and payload_bytes <= 2097152),
  unique (content_hash)
);

-- Bound new JSON payloads before they can consume the reserved staging budget.
-- NOT VALID keeps legacy rows deployable while still enforcing every new write.
do $$
declare
  item record;
begin
  for item in select * from (values
    ('watchlist_snapshots', 'watchlist_snapshots_payload_bytes', 16384),
    ('watchlist_behavior_history', 'watchlist_behavior_payload_bytes', 12288),
    ('watchlist_signal_outcomes', 'watchlist_outcomes_payload_bytes', 8192),
    ('watchlist_learning_state', 'watchlist_learning_payload_bytes', 65536),
    ('watchlist_indicator_state', 'watchlist_indicator_payload_bytes', 32768),
    ('watchlist_refresh_runs', 'watchlist_refresh_payload_bytes', 262144),
    ('watchlist_calibration_artifacts', 'watchlist_calibration_payload_bytes', 2097152)
  ) limits(table_name, constraint_name, max_bytes)
  loop
    if not exists (
      select 1 from pg_constraint where conname = item.constraint_name
        and conrelid = format('public.%I', item.table_name)::regclass
    ) then
      execute format(
        'alter table public.%I add constraint %I check (octet_length(payload::text) <= %s) not valid',
        item.table_name, item.constraint_name, item.max_bytes
      );
    end if;
  end loop;
end $$;

create index if not exists watchlist_calibration_artifacts_cutoff_idx
  on public.watchlist_calibration_artifacts (state, cutoff_date desc, created_at desc);

alter table public.watchlist_learning_state enable row level security;
alter table public.watchlist_indicator_state enable row level security;
alter table public.watchlist_calibration_artifacts enable row level security;
revoke all on public.watchlist_learning_state from anon, authenticated;
revoke all on public.watchlist_indicator_state from anon, authenticated;
revoke all on public.watchlist_calibration_artifacts from anon, authenticated;
grant select, insert, update, delete on public.watchlist_learning_state to service_role;
grant select, insert, update, delete on public.watchlist_indicator_state to service_role;
grant select, insert, update, delete on public.watchlist_calibration_artifacts to service_role;

alter table public.watchlist_snapshots add column if not exists signal_stage text;
alter table public.watchlist_snapshots add column if not exists open numeric;
alter table public.watchlist_snapshots add column if not exists high numeric;
alter table public.watchlist_snapshots add column if not exists low numeric;
alter table public.watchlist_snapshots add column if not exists transition_label text;
alter table public.watchlist_snapshots add column if not exists transition_score numeric;
alter table public.watchlist_snapshots add column if not exists signal_age_days integer;
alter table public.watchlist_snapshots add column if not exists price_progress_since_signal_pct numeric;
alter table public.watchlist_snapshots add column if not exists freshness_penalty numeric;
alter table public.watchlist_snapshots add column if not exists adjusted_score numeric;
alter table public.watchlist_snapshots add column if not exists distance_from_ref_zone_pct numeric;
alter table public.watchlist_snapshots add column if not exists extension_state text;
alter table public.watchlist_snapshots add column if not exists next_day_bias text;
alter table public.watchlist_snapshots add column if not exists next_day_bias_score numeric;
alter table public.watchlist_snapshots add column if not exists next_day_plan text;
alter table public.watchlist_snapshots add column if not exists emotion_score numeric;
alter table public.watchlist_snapshots add column if not exists trend_location_score numeric;
alter table public.watchlist_snapshots add column if not exists setup_context_score numeric;
alter table public.watchlist_snapshots add column if not exists transition_edge_score numeric;
alter table public.watchlist_snapshots add column if not exists personality_weight_label text;
alter table public.watchlist_snapshots add column if not exists personality_weight_emotion numeric;
alter table public.watchlist_snapshots add column if not exists personality_weight_transition numeric;
alter table public.watchlist_snapshots add column if not exists personality_weight_setup numeric;
alter table public.watchlist_snapshots add column if not exists personality_weight_trend numeric;
alter table public.watchlist_snapshots add column if not exists operator_pressure text;
alter table public.watchlist_snapshots add column if not exists operator_pressure_score numeric;
alter table public.watchlist_snapshots add column if not exists operator_plan text;
alter table public.watchlist_snapshots add column if not exists operator_state text;
alter table public.watchlist_snapshots add column if not exists operator_state_score numeric;
alter table public.watchlist_snapshots add column if not exists operator_state_plan text;
alter table public.watchlist_snapshots add column if not exists demand_control_score numeric;
alter table public.watchlist_snapshots add column if not exists bull_trap_score numeric;
alter table public.watchlist_snapshots add column if not exists bear_trap_score numeric;
alter table public.watchlist_snapshots add column if not exists distribution_score numeric;
alter table public.watchlist_snapshots add column if not exists absorption_score numeric;
alter table public.watchlist_snapshots add column if not exists short_pressure_proxy numeric;
alter table public.watchlist_snapshots add column if not exists squeeze_watch text;
alter table public.watchlist_snapshots add column if not exists anti_signal_score numeric;
alter table public.watchlist_snapshots add column if not exists anti_signal_level text;
alter table public.watchlist_snapshots add column if not exists anti_signal_plan text;
alter table public.watchlist_snapshots add column if not exists last_outcome_label text;
alter table public.watchlist_snapshots add column if not exists last_outcome_score numeric;
alter table public.watchlist_snapshots add column if not exists last_outcome_reason text;
alter table public.watchlist_snapshots add column if not exists last_outcome_return_pct numeric;
alter table public.watchlist_snapshots add column if not exists learning_sample_count integer;
alter table public.watchlist_snapshots add column if not exists learning_working_rate numeric;
alter table public.watchlist_snapshots add column if not exists learning_failed_rate numeric;
alter table public.watchlist_snapshots add column if not exists learning_trap_avoided_rate numeric;
alter table public.watchlist_snapshots add column if not exists learning_avg_score numeric;
alter table public.watchlist_snapshots add column if not exists learning_adjustment numeric;
alter table public.watchlist_snapshots add column if not exists learning_scope text;
alter table public.watchlist_snapshots add column if not exists learning_key_used text;
alter table public.watchlist_snapshots add column if not exists learning_plan text;
alter table public.watchlist_snapshots add column if not exists learning_model_version text;
alter table public.watchlist_snapshots add column if not exists learning_distinct_ticker_count integer;
alter table public.watchlist_snapshots add column if not exists learning_evaluation_date_count integer;
alter table public.watchlist_snapshots add column if not exists learning_evaluation_date_min date;
alter table public.watchlist_snapshots add column if not exists learning_evaluation_date_max date;
alter table public.watchlist_snapshots add column if not exists learning_window_start date;
alter table public.watchlist_snapshots add column if not exists learning_window_end date;
alter table public.watchlist_snapshots add column if not exists learning_promotion_eligible boolean;
alter table public.watchlist_snapshots add column if not exists learning_reporting_only boolean;
alter table public.watchlist_snapshots add column if not exists learning_promotion_state text;
alter table public.watchlist_snapshots add column if not exists prediction_horizon_sessions integer;
alter table public.watchlist_snapshots add column if not exists prediction_upside_probability numeric;
alter table public.watchlist_snapshots add column if not exists prediction_downside_probability numeric;
alter table public.watchlist_snapshots add column if not exists prediction_no_edge_probability numeric;
alter table public.watchlist_snapshots add column if not exists prediction_confidence numeric;
alter table public.watchlist_snapshots add column if not exists prediction_model_version text;
alter table public.watchlist_snapshots add column if not exists prediction_state text;
alter table public.watchlist_snapshots add column if not exists contextual_overlay text;
alter table public.watchlist_snapshots add column if not exists contextual_score_adjustment numeric;
alter table public.watchlist_snapshots add column if not exists contextual_plan text;
alter table public.watchlist_snapshots add column if not exists execution_block text;
alter table public.watchlist_snapshots add column if not exists data_provider text;
alter table public.watchlist_snapshots add column if not exists data_provider_status text;
alter table public.watchlist_snapshots add column if not exists data_provider_latency_ms numeric;
alter table public.watchlist_snapshots add column if not exists data_provider_error text;
alter table public.watchlist_snapshots add column if not exists data_age_days integer;
alter table public.watchlist_snapshots add column if not exists freshness_status text;
alter table public.watchlist_snapshots add column if not exists freshness_block text;
alter table public.watchlist_snapshots add column if not exists freshness_plan text;
alter table public.watchlist_snapshots add column if not exists buy_tier text;
alter table public.watchlist_snapshots add column if not exists execution_priority integer;
alter table public.watchlist_snapshots add column if not exists execution_plan text;
alter table public.watchlist_snapshots add column if not exists feedback_window_days integer;
alter table public.watchlist_snapshots add column if not exists feedback_return_pct numeric;
alter table public.watchlist_snapshots add column if not exists feedback_max_drawdown_pct numeric;
alter table public.watchlist_snapshots add column if not exists feedback_stop_hit text;
alter table public.watchlist_snapshots add column if not exists feedback_quality text;
alter table public.watchlist_snapshots add column if not exists feedback_plan text;
alter table public.watchlist_snapshots add column if not exists reason_codes jsonb not null default '[]'::jsonb;

alter table public.watchlist_behavior_history add column if not exists signal_stage text;
alter table public.watchlist_behavior_history add column if not exists open numeric;
alter table public.watchlist_behavior_history add column if not exists high numeric;
alter table public.watchlist_behavior_history add column if not exists low numeric;
alter table public.watchlist_behavior_history add column if not exists transition_label text;
alter table public.watchlist_behavior_history add column if not exists transition_score numeric;
alter table public.watchlist_behavior_history add column if not exists signal_age_days integer;
alter table public.watchlist_behavior_history add column if not exists price_progress_since_signal_pct numeric;
alter table public.watchlist_behavior_history add column if not exists freshness_penalty numeric;
alter table public.watchlist_behavior_history add column if not exists adjusted_score numeric;
alter table public.watchlist_behavior_history add column if not exists distance_from_ref_zone_pct numeric;
alter table public.watchlist_behavior_history add column if not exists extension_state text;
alter table public.watchlist_behavior_history add column if not exists next_day_bias text;
alter table public.watchlist_behavior_history add column if not exists next_day_bias_score numeric;
alter table public.watchlist_behavior_history add column if not exists next_day_plan text;
alter table public.watchlist_behavior_history add column if not exists emotion_score numeric;
alter table public.watchlist_behavior_history add column if not exists trend_location_score numeric;
alter table public.watchlist_behavior_history add column if not exists setup_context_score numeric;
alter table public.watchlist_behavior_history add column if not exists transition_edge_score numeric;
alter table public.watchlist_behavior_history add column if not exists personality_weight_label text;
alter table public.watchlist_behavior_history add column if not exists personality_weight_emotion numeric;
alter table public.watchlist_behavior_history add column if not exists personality_weight_transition numeric;
alter table public.watchlist_behavior_history add column if not exists personality_weight_setup numeric;
alter table public.watchlist_behavior_history add column if not exists personality_weight_trend numeric;
alter table public.watchlist_behavior_history add column if not exists operator_pressure text;
alter table public.watchlist_behavior_history add column if not exists operator_pressure_score numeric;
alter table public.watchlist_behavior_history add column if not exists operator_plan text;
alter table public.watchlist_behavior_history add column if not exists operator_state text;
alter table public.watchlist_behavior_history add column if not exists operator_state_score numeric;
alter table public.watchlist_behavior_history add column if not exists operator_state_plan text;
alter table public.watchlist_behavior_history add column if not exists demand_control_score numeric;
alter table public.watchlist_behavior_history add column if not exists bull_trap_score numeric;
alter table public.watchlist_behavior_history add column if not exists bear_trap_score numeric;
alter table public.watchlist_behavior_history add column if not exists distribution_score numeric;
alter table public.watchlist_behavior_history add column if not exists absorption_score numeric;
alter table public.watchlist_behavior_history add column if not exists short_pressure_proxy numeric;
alter table public.watchlist_behavior_history add column if not exists squeeze_watch text;
alter table public.watchlist_behavior_history add column if not exists anti_signal_score numeric;
alter table public.watchlist_behavior_history add column if not exists anti_signal_level text;
alter table public.watchlist_behavior_history add column if not exists anti_signal_plan text;
alter table public.watchlist_behavior_history add column if not exists last_outcome_label text;
alter table public.watchlist_behavior_history add column if not exists last_outcome_score numeric;
alter table public.watchlist_behavior_history add column if not exists last_outcome_reason text;
alter table public.watchlist_behavior_history add column if not exists last_outcome_return_pct numeric;
alter table public.watchlist_behavior_history add column if not exists learning_sample_count integer;
alter table public.watchlist_behavior_history add column if not exists learning_working_rate numeric;
alter table public.watchlist_behavior_history add column if not exists learning_failed_rate numeric;
alter table public.watchlist_behavior_history add column if not exists learning_trap_avoided_rate numeric;
alter table public.watchlist_behavior_history add column if not exists learning_avg_score numeric;
alter table public.watchlist_behavior_history add column if not exists learning_adjustment numeric;
alter table public.watchlist_behavior_history add column if not exists learning_scope text;
alter table public.watchlist_behavior_history add column if not exists learning_key_used text;
alter table public.watchlist_behavior_history add column if not exists learning_plan text;
alter table public.watchlist_behavior_history add column if not exists learning_model_version text;
alter table public.watchlist_behavior_history add column if not exists learning_distinct_ticker_count integer;
alter table public.watchlist_behavior_history add column if not exists learning_evaluation_date_count integer;
alter table public.watchlist_behavior_history add column if not exists learning_evaluation_date_min date;
alter table public.watchlist_behavior_history add column if not exists learning_evaluation_date_max date;
alter table public.watchlist_behavior_history add column if not exists learning_window_start date;
alter table public.watchlist_behavior_history add column if not exists learning_window_end date;
alter table public.watchlist_behavior_history add column if not exists learning_promotion_eligible boolean;
alter table public.watchlist_behavior_history add column if not exists learning_reporting_only boolean;
alter table public.watchlist_behavior_history add column if not exists learning_promotion_state text;
alter table public.watchlist_behavior_history add column if not exists prediction_horizon_sessions integer;
alter table public.watchlist_behavior_history add column if not exists prediction_upside_probability numeric;
alter table public.watchlist_behavior_history add column if not exists prediction_downside_probability numeric;
alter table public.watchlist_behavior_history add column if not exists prediction_no_edge_probability numeric;
alter table public.watchlist_behavior_history add column if not exists prediction_confidence numeric;
alter table public.watchlist_behavior_history add column if not exists prediction_model_version text;
alter table public.watchlist_behavior_history add column if not exists prediction_state text;
alter table public.watchlist_behavior_history add column if not exists contextual_overlay text;
alter table public.watchlist_behavior_history add column if not exists contextual_score_adjustment numeric;
alter table public.watchlist_behavior_history add column if not exists contextual_plan text;
alter table public.watchlist_behavior_history add column if not exists execution_block text;
alter table public.watchlist_behavior_history add column if not exists data_provider text;
alter table public.watchlist_behavior_history add column if not exists data_provider_status text;
alter table public.watchlist_behavior_history add column if not exists data_provider_latency_ms numeric;
alter table public.watchlist_behavior_history add column if not exists data_provider_error text;
alter table public.watchlist_behavior_history add column if not exists data_age_days integer;
alter table public.watchlist_behavior_history add column if not exists freshness_status text;
alter table public.watchlist_behavior_history add column if not exists freshness_block text;
alter table public.watchlist_behavior_history add column if not exists freshness_plan text;
alter table public.watchlist_behavior_history add column if not exists buy_tier text;
alter table public.watchlist_behavior_history add column if not exists execution_priority integer;
alter table public.watchlist_behavior_history add column if not exists execution_plan text;
alter table public.watchlist_behavior_history add column if not exists feedback_window_days integer;
alter table public.watchlist_behavior_history add column if not exists feedback_return_pct numeric;
alter table public.watchlist_behavior_history add column if not exists feedback_max_drawdown_pct numeric;
alter table public.watchlist_behavior_history add column if not exists feedback_stop_hit text;
alter table public.watchlist_behavior_history add column if not exists feedback_quality text;
alter table public.watchlist_behavior_history add column if not exists feedback_plan text;
alter table public.watchlist_behavior_history add column if not exists reason_codes jsonb not null default '[]'::jsonb;

alter table public.watchlist_refresh_runs add column if not exists learning_history_rows integer;
alter table public.watchlist_snapshots add column if not exists publication_id text;
alter table public.watchlist_behavior_history add column if not exists publication_id text;
alter table public.watchlist_refresh_runs add column if not exists publication_id text;
alter table public.watchlist_signal_outcomes add column if not exists entry_model_version text;
alter table public.watchlist_signal_outcomes add column if not exists publication_id text;
alter table public.watchlist_signal_outcomes add column if not exists entry_eligible boolean;
alter table public.watchlist_signal_outcomes add column if not exists entry_filled boolean;
alter table public.watchlist_signal_outcomes add column if not exists entry_fill_est numeric;
alter table public.watchlist_signal_outcomes add column if not exists forecast_learnable boolean;
alter table public.watchlist_signal_outcomes add column if not exists prior_prediction_upside_probability numeric;
alter table public.watchlist_signal_outcomes add column if not exists prior_prediction_downside_probability numeric;
alter table public.watchlist_signal_outcomes add column if not exists prior_prediction_no_edge_probability numeric;
alter table public.watchlist_signal_outcomes add column if not exists prior_prediction_confidence numeric;
alter table public.watchlist_signal_outcomes add column if not exists prior_prediction_state text;
alter table public.watchlist_signal_outcomes add column if not exists prior_prediction_key text;
alter table public.watchlist_signal_outcomes add column if not exists prior_prediction_scope text;

update public.watchlist_signal_outcomes
set publication_id = coalesce(
  nullif(payload->>'publication_id', ''),
  'legacy-' || signal_run_date::text || '-' || evaluation_run_date::text
)
where publication_id is null or publication_id = '';

alter table public.watchlist_signal_outcomes alter column publication_id set not null;
delete from public.watchlist_signal_outcomes target
using (
  select ctid from (
    select ctid, row_number() over (
      partition by publication_id, signal_run_date, evaluation_run_date, ticker order by ctid desc
    ) position
    from public.watchlist_signal_outcomes
  ) ranked where position > 1
) duplicate
where target.ctid = duplicate.ctid;
do $$
declare
  primary_key_name text;
  primary_key_columns text[];
begin
  select constraint_row.conname, array_agg(attribute.attname order by key_column.position)
  into primary_key_name, primary_key_columns
  from pg_constraint constraint_row
  cross join lateral unnest(constraint_row.conkey) with ordinality key_column(attnum, position)
  join pg_attribute attribute on attribute.attrelid = constraint_row.conrelid and attribute.attnum = key_column.attnum
  where constraint_row.conrelid = 'public.watchlist_signal_outcomes'::regclass and constraint_row.contype = 'p'
  group by constraint_row.conname;
  if primary_key_name is not null and primary_key_columns <> array['publication_id', 'signal_run_date', 'evaluation_run_date', 'ticker'] then
    execute format('alter table public.watchlist_signal_outcomes drop constraint %I', primary_key_name);
    primary_key_name := null;
  end if;
  if primary_key_name is null then
    alter table public.watchlist_signal_outcomes
      add primary key (publication_id, signal_run_date, evaluation_run_date, ticker);
  end if;
end $$;
create index if not exists watchlist_signal_outcomes_publication_idx
  on public.watchlist_signal_outcomes (publication_id, evaluation_run_date desc);

update public.watchlist_snapshots
set publication_id = coalesce(nullif(payload->>'publication_id', ''), 'legacy-' || run_date::text)
where publication_id is null or publication_id = '';
update public.watchlist_behavior_history
set publication_id = coalesce(nullif(payload->>'publication_id', ''), 'legacy-' || run_date::text)
where publication_id is null or publication_id = '';
update public.watchlist_refresh_runs
set publication_id = coalesce(nullif(payload->>'publication_id', ''), 'legacy-' || run_date::text)
where publication_id is null or publication_id = '';

alter table public.watchlist_snapshots alter column publication_id set not null;
alter table public.watchlist_behavior_history alter column publication_id set not null;
alter table public.watchlist_refresh_runs alter column publication_id set not null;
delete from public.watchlist_snapshots target using (
  select ctid from (
    select ctid, row_number() over (partition by publication_id, ticker order by ctid desc) position
    from public.watchlist_snapshots
  ) ranked where position > 1
) duplicate where target.ctid = duplicate.ctid;
delete from public.watchlist_behavior_history target using (
  select ctid from (
    select ctid, row_number() over (partition by publication_id, ticker, history_date order by ctid desc) position
    from public.watchlist_behavior_history
  ) ranked where position > 1
) duplicate where target.ctid = duplicate.ctid;
delete from public.watchlist_refresh_runs target using (
  select ctid from (
    select ctid, row_number() over (partition by publication_id order by created_at desc, ctid desc) position
    from public.watchlist_refresh_runs
  ) ranked where position > 1
) duplicate where target.ctid = duplicate.ctid;
do $$
declare
  item record;
  primary_key_name text;
  primary_key_columns text[];
begin
  for item in select * from (values
    ('watchlist_snapshots', array['publication_id', 'ticker']),
    ('watchlist_behavior_history', array['publication_id', 'ticker', 'history_date']),
    ('watchlist_refresh_runs', array['publication_id'])
  ) definitions(table_name, expected_columns)
  loop
    primary_key_name := null;
    primary_key_columns := null;
    select constraint_row.conname, array_agg(attribute.attname order by key_column.position)
    into primary_key_name, primary_key_columns
    from pg_constraint constraint_row
    cross join lateral unnest(constraint_row.conkey) with ordinality key_column(attnum, position)
    join pg_attribute attribute on attribute.attrelid = constraint_row.conrelid and attribute.attnum = key_column.attnum
    where constraint_row.conrelid = format('public.%I', item.table_name)::regclass and constraint_row.contype = 'p'
    group by constraint_row.conname;
    if primary_key_name is not null and primary_key_columns <> item.expected_columns then
      execute format('alter table public.%I drop constraint %I', item.table_name, primary_key_name);
      primary_key_name := null;
    end if;
    if primary_key_name is null then
      execute format(
        'alter table public.%I add primary key (%s)',
        item.table_name,
        (select string_agg(format('%I', column_name), ', ') from unnest(item.expected_columns) column_name)
      );
    end if;
  end loop;
end $$;
drop index if exists public.focus_tickers_list_idx;
drop index if exists public.watchlist_snapshots_publication_idx;
drop index if exists public.watchlist_behavior_history_publication_idx;
create index if not exists watchlist_refresh_runs_validated_idx
  on public.watchlist_refresh_runs (run_date desc, status, updated_at desc);

-- Remove hidden partial writes from pre-pointer releases before enforcing the
-- publication parent contract. These rows were never safe for readers.
delete from public.watchlist_snapshots child
where not exists (select 1 from public.watchlist_refresh_runs parent where parent.publication_id = child.publication_id);
delete from public.watchlist_behavior_history child
where not exists (select 1 from public.watchlist_refresh_runs parent where parent.publication_id = child.publication_id);
delete from public.watchlist_signal_outcomes child
where not exists (select 1 from public.watchlist_refresh_runs parent where parent.publication_id = child.publication_id);
delete from public.watchlist_learning_state child
where not exists (select 1 from public.watchlist_refresh_runs parent where parent.publication_id = child.publication_id);
delete from public.watchlist_indicator_state child
where not exists (select 1 from public.watchlist_refresh_runs parent where parent.publication_id = child.publication_id);
delete from public.watchlist_calibration_artifacts child
where not exists (select 1 from public.watchlist_refresh_runs parent where parent.publication_id = child.source_publication_id);

insert into public.watchlist_publication_control (
  control_key, active_publication_id, previous_publication_id, generation, activated_at
)
select
  'active',
  latest.publication_id,
  previous.publication_id,
  1,
  now()
from lateral (
  select publication_id
  from public.watchlist_refresh_runs
  where status in ('ok', 'degraded')
  order by run_date desc, created_at desc
  limit 1
) latest
left join lateral (
  select publication_id
  from public.watchlist_refresh_runs
  where status in ('ok', 'degraded') and publication_id <> latest.publication_id
  order by run_date desc, created_at desc
  limit 1
) previous on true
on conflict (control_key) do nothing;

do $$
declare
  item record;
  foreign_key_oid oid;
begin
  for item in select * from (values
    ('watchlist_snapshots', 'publication_id', 'watchlist_snapshots_publication_fk', 'c', 'cascade'),
    ('watchlist_behavior_history', 'publication_id', 'watchlist_behavior_history_publication_fk', 'c', 'cascade'),
    ('watchlist_signal_outcomes', 'publication_id', 'watchlist_signal_outcomes_publication_fk', 'c', 'cascade'),
    ('watchlist_learning_state', 'publication_id', 'watchlist_learning_state_publication_fk', 'c', 'cascade'),
    ('watchlist_indicator_state', 'publication_id', 'watchlist_indicator_state_publication_fk', 'c', 'cascade'),
    ('watchlist_calibration_artifacts', 'source_publication_id', 'watchlist_calibration_artifacts_publication_fk', 'c', 'cascade'),
    ('watchlist_publication_control', 'active_publication_id', 'watchlist_publication_control_active_fk', 'r', 'restrict'),
    ('watchlist_publication_control', 'previous_publication_id', 'watchlist_publication_control_previous_fk', 'n', 'set null')
  ) definitions(table_name, column_name, constraint_name, delete_code, delete_action)
  loop
    select constraint_row.oid into foreign_key_oid
    from pg_constraint constraint_row
    where constraint_row.conname = item.constraint_name
      and constraint_row.conrelid = format('public.%I', item.table_name)::regclass;
    if foreign_key_oid is not null and not exists (
      select 1
      from pg_constraint constraint_row
      join pg_attribute child_attribute on child_attribute.attrelid = constraint_row.conrelid and child_attribute.attnum = constraint_row.conkey[1]
      join pg_attribute parent_attribute on parent_attribute.attrelid = constraint_row.confrelid and parent_attribute.attnum = constraint_row.confkey[1]
      where constraint_row.oid = foreign_key_oid
        and constraint_row.contype = 'f'
        and constraint_row.confrelid = 'public.watchlist_refresh_runs'::regclass
        and array_length(constraint_row.conkey, 1) = 1
        and child_attribute.attname = item.column_name
        and parent_attribute.attname = 'publication_id'
        and constraint_row.confdeltype = item.delete_code
    ) then
      execute format('alter table public.%I drop constraint %I', item.table_name, item.constraint_name);
      foreign_key_oid := null;
    end if;
    if foreign_key_oid is null then
      execute format(
        'alter table public.%I add constraint %I foreign key (%I) references public.watchlist_refresh_runs(publication_id) on delete %s',
        item.table_name, item.constraint_name, item.column_name, item.delete_action
      );
    end if;
  end loop;
end $$;

alter table public.watchlist_snapshots enable row level security;
alter table public.watchlist_behavior_history enable row level security;
alter table public.watchlist_signal_outcomes enable row level security;
alter table public.watchlist_refresh_runs enable row level security;
alter table public.watchlist_publication_control enable row level security;
alter table public.focus_tickers enable row level security;

revoke all on public.watchlist_snapshots from anon, authenticated;
revoke all on public.watchlist_behavior_history from anon, authenticated;
revoke all on public.watchlist_signal_outcomes from anon, authenticated;
revoke all on public.watchlist_refresh_runs from anon, authenticated;
revoke all on public.watchlist_publication_control from anon, authenticated;
revoke all on public.focus_tickers from anon, authenticated;

grant select on public.watchlist_snapshots to anon, authenticated;
grant select on public.watchlist_behavior_history to anon, authenticated;
grant select on public.watchlist_refresh_runs to anon, authenticated;
grant select on public.watchlist_publication_control to anon, authenticated;
grant select, insert, update, delete on public.watchlist_snapshots to service_role;
grant select, insert, update, delete on public.watchlist_behavior_history to service_role;
grant select, insert, update, delete on public.watchlist_signal_outcomes to service_role;
grant select, insert, update, delete on public.watchlist_refresh_runs to service_role;
grant select, insert, update, delete on public.watchlist_publication_control to service_role;
grant select, insert, update, delete on public.focus_tickers to service_role;

drop policy if exists "Public read watchlist snapshots" on public.watchlist_snapshots;
create policy "Public read watchlist snapshots"
  on public.watchlist_snapshots for select
  using (publication_id in (
    select active_publication_id from public.watchlist_publication_control where control_key = 'active'
    union all
    select previous_publication_id from public.watchlist_publication_control where control_key = 'active'
  ));

drop policy if exists "Public read behavior history" on public.watchlist_behavior_history;
create policy "Public read behavior history"
  on public.watchlist_behavior_history for select
  using (publication_id = (
    select active_publication_id from public.watchlist_publication_control where control_key = 'active'
  ));

drop policy if exists "Public read signal outcomes" on public.watchlist_signal_outcomes;

drop policy if exists "Public read refresh runs" on public.watchlist_refresh_runs;
create policy "Public read refresh runs"
  on public.watchlist_refresh_runs for select
  using (publication_id in (
    select active_publication_id from public.watchlist_publication_control where control_key = 'active'
    union all
    select previous_publication_id from public.watchlist_publication_control where control_key = 'active'
  ));

drop policy if exists "Public read publication control" on public.watchlist_publication_control;
create policy "Public read publication control"
  on public.watchlist_publication_control for select
  using (control_key = 'active');

drop policy if exists "Public read focus tickers" on public.focus_tickers;
drop policy if exists "Public write focus tickers" on public.focus_tickers;
drop policy if exists "Server API read focus tickers" on public.focus_tickers;
drop policy if exists "Server API write focus tickers" on public.focus_tickers;

select pg_notify('pgrst', 'reload schema');
