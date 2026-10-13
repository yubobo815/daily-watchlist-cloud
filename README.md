# Daily Trade Copilot

[![Quality](https://github.com/yubobo815/daily-watchlist-cloud/actions/workflows/quality.yml/badge.svg)](https://github.com/yubobo815/daily-watchlist-cloud/actions/workflows/quality.yml)

A stock and ETF watchlist scanner with an interactive dashboard, ticker history and daily market-data refreshes. Python produces the reports, Supabase stores publication-bound data, and Vercel and GitHub Pages serve the dashboard.

- [Live dashboard](https://dailytradingcopilot.vercel.app/)
- [GitHub Pages dashboard](https://yubobo815.github.io/daily-watchlist-cloud/)
- [Refresh runs](https://github.com/yubobo815/daily-watchlist-cloud/actions/workflows/daily-watchlist-pages.yml)

The app supports research and trade planning. Candidates still require chart confirmation in TradingView/Pine before acting; the app does not execute trades.

## Features

- Configurable stock and ETF universe in `daily_watchlist.txt`.
- Technical signals, market context, execution plans and historical signal evaluation.
- Daily incremental updates and a separate weekly calibration rebuild.
- Data-freshness gates, missing-symbol reporting and explicit blocking of stale execution candidates.
- Ticker detail and behaviour-history views, CSV output and static fallback data.
- Validated publication activation and rollback protection.

## How it works

1. GitHub Actions runs the Python scanner against configured market-data providers or stored OHLCV.
2. The scanner stages snapshots, behaviour history, learning outcomes and indicator state in Supabase.
3. Health and storage checks validate the staged publication.
4. GitHub Pages publishes an immutable data bundle. The workflow verifies it before activating the matching Supabase publication.
5. Vercel serves the interactive app and reads the active publication through server-side API routes.

The dashboard can fall back to published JSON when live database reads are unavailable. A page loading successfully does not guarantee fresh data: check its report date, market-data date and health status.

## Local setup

Use Python 3.11 or later, Node.js and npm.

```bash
git clone https://github.com/yubobo815/daily-watchlist-cloud.git
cd daily-watchlist-cloud
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
npm ci
```

Inspect the scanner options and run the project audits:

```bash
python daily_watchlist_overview.py --help
npm run audit:watchlist
```

Preview the static app:

```bash
python -m http.server 8000
```

Open `http://localhost:8000`. This previews the frontend and its fallback behaviour; Python's static server does not run the Vercel API routes or trigger a market-data refresh.

For container-based audits and browser UAT, install Docker with Compose and run:

```bash
npm run uat:docker
```

## Configure cloud refreshes

Enable GitHub Actions and set **Settings → Pages → Source** to **GitHub Actions**.

Configure these repository Actions secrets:

| Secret | Purpose |
| --- | --- |
| `SUPABASE_URL` | Supabase project API URL. |
| `SUPABASE_SECRET_KEY` | Server-side secret key for scanner reads and writes. `SUPABASE_SERVICE_ROLE_KEY` is supported as a legacy fallback. |
| `SUPABASE_DB_URL` | PostgreSQL connection string for schema application and publishing-capacity checks; required by the production workflow. |
| `MASSIVE_API_KEY` or `POLYGON_API_KEY` | Credentials for the primary configured market-data provider. |
| `TWELVE_DATA_API_KEY` | Optional additional provider. |

The workflow's provider priority is `polygon,twelvedata,stooq,yahoo`; Massive credentials are supported by the Polygon provider integration. Provider availability, entitlement and rate limits can affect refreshes.

Import this repository into Vercel using `vercel.json`. Configure `SUPABASE_URL` and `SUPABASE_SECRET_KEY` as server-side environment variables. Set `FOCUS_LIST_PIN` to use the PIN-protected personal cloud Focus List.

Keep credentials in GitHub Actions secrets or server-side environment variables. Do not commit keys, connection strings, PINs, local environment files or virtual environments, and do not expose secret keys in browser JavaScript.

## Run a refresh

In **Actions → Daily Watchlist Pages → Run workflow**, choose:

| Input | Normal setting | Meaning |
| --- | --- | --- |
| `refresh_mode` | `daily` | Incremental report refresh. `weekly_rebuild` replays the bounded learning window and recalibrates. |
| `allow_calibration_bootstrap` | `false` | Explicitly replaces missing or incompatible calibration state. Reserve this for initialisation or an intentional state migration. |
| `use_stored_ohlcv` | `false` | Fetches current provider data. Set to `true` to reuse stored OHLCV, after verifying its market-data date. |

With GitHub CLI authentication configured, the normal daily refresh is:

```bash
gh workflow run daily-watchlist-pages.yml \
  --repo yubobo815/daily-watchlist-cloud \
  --ref main \
  -f refresh_mode=daily \
  -f allow_calibration_bootstrap=false \
  -f use_stored_ohlcv=false
```

A daily refresh requires compatible existing incremental state. A fresh installation needs an explicit calibration bootstrap; the scanner does not silently bypass that check.

### Schedule

The current workflow registers daily refreshes for Tuesday–Saturday at **11:17 Australia/Melbourne**, with guarded recovery attempts at **14:17** and **17:17**. Seasonal UTC markers handle AEST/AEDT, and the inactive seasonal marker skips. These are scheduled trigger times, not guaranteed start or completion times.

The weekly rebuild is scheduled for **Saturday 15:47 UTC**, with a guarded retry at **Saturday 22:47 UTC**. These fall on Sunday morning in Melbourne. Weekly rebuilds normally reuse stored OHLCV and retain calibration parity checks.

The authoritative schedule and inputs are in [the workflow](.github/workflows/daily-watchlist-pages.yml).

## Check refresh health

After a run, verify the workflow result, active publication, report date and latest market-data date. A `degraded` report can contain valid current rows alongside missing symbols or stale, execution-blocked rows. Do not treat workflow success as proof that every symbol has fresh data.

Storage is bounded with table-specific retention, a 400-bar OHLCV store and compact payloads. Monitor Supabase organisation egress separately from database size: repeated rebuilds and historical reads consume bandwidth even when publication later fails.

## Project layout

| Path | Responsibility |
| --- | --- |
| `daily_watchlist_overview.py` | Scanner, learning calculations, report generation and Supabase sync. |
| `execution_plan_state.py` | Execution-plan lifecycle state. |
| `daily_watchlist.txt` | Watchlist universe. |
| `index.html`, `history.html`, `ticker.html`, `assets/` | Dashboard frontend. |
| `api/` | Vercel API routes and server-side database access. |
| `supabase_schema.sql` | Database schema and publication contract. |
| `.github/workflows/daily-watchlist-pages.yml` | Refresh, validation, deployment, activation and cleanup. |
| `scripts/` | Audits, UAT and publication/storage utilities. |
| `data/` | Committed static fallback assets; not a guarantee of current market data. |

This repository is the production source of truth. See [SOURCE_OF_TRUTH.md](SOURCE_OF_TRUTH.md). Before changing production logic, run `npm run audit:watchlist` and syntax checks for the Python or JavaScript files you change.

The Quality workflow runs syntax checks and regression audits on Python 3.11/3.12, followed by Docker desktop/mobile browser UAT, for every pull request and push to `main`. It does not require production secrets or refresh market data. Dependencies are pinned, and Dependabot proposes Python and GitHub Actions updates weekly.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the development checklist and [SECURITY.md](SECURITY.md) for vulnerability reporting.
