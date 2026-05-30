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
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (run_date, ticker, history_date)
);

create index if not exists watchlist_snapshots_ticker_run_date_idx
  on public.watchlist_snapshots (ticker, run_date desc);

create index if not exists watchlist_snapshots_action_score_idx
  on public.watchlist_snapshots (run_date desc, action, score desc);

create index if not exists watchlist_behavior_history_ticker_date_idx
  on public.watchlist_behavior_history (ticker, history_date desc);

alter table public.watchlist_snapshots enable row level security;
alter table public.watchlist_behavior_history enable row level security;

drop policy if exists "Public read watchlist snapshots" on public.watchlist_snapshots;
create policy "Public read watchlist snapshots"
  on public.watchlist_snapshots for select
  using (true);

drop policy if exists "Public read behavior history" on public.watchlist_behavior_history;
create policy "Public read behavior history"
  on public.watchlist_behavior_history for select
  using (true);
