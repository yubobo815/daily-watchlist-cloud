create table if not exists public.watchlist_snapshots (
  run_date date not null,
  ticker text not null,
  name text,
  data_date date,
  action text,
  setup text,
  adaptive_mode text,
  psychology text,
  score numeric,
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
  reason_codes jsonb not null default '[]'::jsonb,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (run_date, ticker)
);

create table if not exists public.watchlist_behavior_history (
  run_date date not null,
  ticker text not null,
  history_date date not null,
  action text,
  setup text,
  adaptive_mode text,
  psychology text,
  score numeric,
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
  reason_codes jsonb not null default '[]'::jsonb,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (run_date, ticker, history_date)
);

create table if not exists public.watchlist_refresh_runs (
  run_date date primary key,
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
  scanner_version text,
  notes text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
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

create index if not exists watchlist_refresh_runs_status_idx
  on public.watchlist_refresh_runs (run_date desc, status);

create index if not exists focus_tickers_list_idx
  on public.focus_tickers (list_id, ticker);

alter table public.watchlist_snapshots add column if not exists signal_stage text;
alter table public.watchlist_snapshots add column if not exists transition_label text;
alter table public.watchlist_snapshots add column if not exists transition_score numeric;
alter table public.watchlist_snapshots add column if not exists signal_age_days integer;
alter table public.watchlist_snapshots add column if not exists price_progress_since_signal_pct numeric;
alter table public.watchlist_snapshots add column if not exists freshness_penalty numeric;
alter table public.watchlist_snapshots add column if not exists adjusted_score numeric;
alter table public.watchlist_snapshots add column if not exists distance_from_ref_zone_pct numeric;
alter table public.watchlist_snapshots add column if not exists extension_state text;
alter table public.watchlist_snapshots add column if not exists reason_codes jsonb not null default '[]'::jsonb;

alter table public.watchlist_behavior_history add column if not exists signal_stage text;
alter table public.watchlist_behavior_history add column if not exists transition_label text;
alter table public.watchlist_behavior_history add column if not exists transition_score numeric;
alter table public.watchlist_behavior_history add column if not exists signal_age_days integer;
alter table public.watchlist_behavior_history add column if not exists price_progress_since_signal_pct numeric;
alter table public.watchlist_behavior_history add column if not exists freshness_penalty numeric;
alter table public.watchlist_behavior_history add column if not exists adjusted_score numeric;
alter table public.watchlist_behavior_history add column if not exists distance_from_ref_zone_pct numeric;
alter table public.watchlist_behavior_history add column if not exists extension_state text;
alter table public.watchlist_behavior_history add column if not exists reason_codes jsonb not null default '[]'::jsonb;

alter table public.watchlist_snapshots enable row level security;
alter table public.watchlist_behavior_history enable row level security;
alter table public.watchlist_refresh_runs enable row level security;
alter table public.focus_tickers enable row level security;

revoke all on public.watchlist_snapshots from anon, authenticated;
revoke all on public.watchlist_behavior_history from anon, authenticated;
revoke all on public.watchlist_refresh_runs from anon, authenticated;
revoke all on public.focus_tickers from anon, authenticated;

grant select on public.watchlist_snapshots to anon, authenticated;
grant select on public.watchlist_behavior_history to anon, authenticated;
grant select on public.watchlist_refresh_runs to anon, authenticated;

drop policy if exists "Public read watchlist snapshots" on public.watchlist_snapshots;
create policy "Public read watchlist snapshots"
  on public.watchlist_snapshots for select
  using (true);

drop policy if exists "Public read behavior history" on public.watchlist_behavior_history;
create policy "Public read behavior history"
  on public.watchlist_behavior_history for select
  using (true);

drop policy if exists "Public read refresh runs" on public.watchlist_refresh_runs;
create policy "Public read refresh runs"
  on public.watchlist_refresh_runs for select
  using (true);

drop policy if exists "Public read focus tickers" on public.focus_tickers;
drop policy if exists "Public write focus tickers" on public.focus_tickers;
