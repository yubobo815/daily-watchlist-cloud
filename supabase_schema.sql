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
do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.watchlist_signal_outcomes'::regclass and contype = 'p'
  ) then
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
do $$
begin
  if not exists (select 1 from pg_constraint where conrelid = 'public.watchlist_snapshots'::regclass and contype = 'p') then
    alter table public.watchlist_snapshots add primary key (publication_id, ticker);
  end if;
  if not exists (select 1 from pg_constraint where conrelid = 'public.watchlist_behavior_history'::regclass and contype = 'p') then
    alter table public.watchlist_behavior_history add primary key (publication_id, ticker, history_date);
  end if;
  if not exists (select 1 from pg_constraint where conrelid = 'public.watchlist_refresh_runs'::regclass and contype = 'p') then
    alter table public.watchlist_refresh_runs add primary key (publication_id);
  end if;
end $$;
drop index if exists public.focus_tickers_list_idx;
drop index if exists public.watchlist_snapshots_publication_idx;
drop index if exists public.watchlist_behavior_history_publication_idx;
create index if not exists watchlist_refresh_runs_validated_idx
  on public.watchlist_refresh_runs (run_date desc, status, updated_at desc);

alter table public.watchlist_snapshots enable row level security;
alter table public.watchlist_behavior_history enable row level security;
alter table public.watchlist_signal_outcomes enable row level security;
alter table public.watchlist_refresh_runs enable row level security;
alter table public.focus_tickers enable row level security;

revoke all on public.watchlist_snapshots from anon, authenticated;
revoke all on public.watchlist_behavior_history from anon, authenticated;
revoke all on public.watchlist_signal_outcomes from anon, authenticated;
revoke all on public.watchlist_refresh_runs from anon, authenticated;
revoke all on public.focus_tickers from anon, authenticated;

grant select on public.watchlist_snapshots to anon, authenticated;
grant select on public.watchlist_behavior_history to anon, authenticated;
grant select on public.watchlist_refresh_runs to anon, authenticated;
grant select, insert, update, delete on public.watchlist_snapshots to service_role;
grant select, insert, update, delete on public.watchlist_behavior_history to service_role;
grant select, insert, update, delete on public.watchlist_signal_outcomes to service_role;
grant select, insert, update, delete on public.watchlist_refresh_runs to service_role;
grant select, insert, update, delete on public.focus_tickers to service_role;

drop policy if exists "Public read watchlist snapshots" on public.watchlist_snapshots;
create policy "Public read watchlist snapshots"
  on public.watchlist_snapshots for select
  using (true);

drop policy if exists "Public read behavior history" on public.watchlist_behavior_history;
create policy "Public read behavior history"
  on public.watchlist_behavior_history for select
  using (true);

drop policy if exists "Public read signal outcomes" on public.watchlist_signal_outcomes;

drop policy if exists "Public read refresh runs" on public.watchlist_refresh_runs;
create policy "Public read refresh runs"
  on public.watchlist_refresh_runs for select
  using (true);

drop policy if exists "Public read focus tickers" on public.focus_tickers;
drop policy if exists "Public write focus tickers" on public.focus_tickers;
drop policy if exists "Server API read focus tickers" on public.focus_tickers;
drop policy if exists "Server API write focus tickers" on public.focus_tickers;

select pg_notify('pgrst', 'reload schema');
