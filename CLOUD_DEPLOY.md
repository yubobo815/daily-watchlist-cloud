# Cloud deployment

GitHub Actions refreshes the scanner, stages data in Supabase and publishes an immutable GitHub Pages bundle. This repository is the production source of truth; see [README.md](README.md) for the overview and [SOURCE_OF_TRUTH.md](SOURCE_OF_TRUTH.md) for ownership rules.

## Setup

1. Enable GitHub Actions for the repository.
2. In **Settings → Pages**, set **Build and deployment → Source** to **GitHub Actions**.
3. In **Settings → Secrets and variables → Actions**, configure `SUPABASE_URL`, `SUPABASE_SECRET_KEY` and `SUPABASE_DB_URL`. The production workflow requires the database URL and applies `supabase_schema.sql` before refreshing.
4. Configure `MASSIVE_API_KEY` or `POLYGON_API_KEY` for the primary provider. `TWELVE_DATA_API_KEY` is an optional additional provider. The configured fallback order is `polygon,twelvedata,stooq,yahoo`.
5. In **Actions → Daily Watchlist Pages → Run workflow**, initialise a new database with `refresh_mode=weekly_rebuild` and `allow_calibration_bootstrap=true`. For an existing compatible installation, use `refresh_mode=daily` and leave bootstrap disabled.

An explicit bootstrap replaces calibration state; use it for initialisation or an intentional migration, rather than as a generic retry switch.

## Schedule and manual recovery

Daily refreshes are registered for Tuesday–Saturday at 11:17 Australia/Melbourne, with guarded recovery attempts at 14:17 and 17:17. The inactive AEST/AEDT UTC marker skips. GitHub may delay starts; the schedule is not a completion-time guarantee.

The weekly rebuild is Saturday 15:47 UTC, with a guarded retry at Saturday 22:47 UTC. Both are Sunday morning in Melbourne. It reuses stored OHLCV and retains parity validation.

For manual recovery, choose `daily`. Set `use_stored_ohlcv=true` only after checking that the stored market-data date is current. The authoritative schedule and inputs are in [the workflow](.github/workflows/daily-watchlist-pages.yml).

## Publication and health

The workflow stages a new publication, checks database health and capacity, uploads the Pages bundle, verifies the deployed publication identifier, then activates the matching Supabase publication. Failed builds or activation retain rollback protection. Final cleanup bounds persistent storage.

Published files include the dashboard pages, latest CSV, `data/manifest.json`, run metadata and publication-specific latest/ticker JSON. Read the manifest to identify the active immutable bundle.

Check the report date, market-data date, failed symbols and stale execution blocks after each refresh. A successful run can publish a `degraded` report when some symbols are unavailable.

Retention is table-specific: scanner defaults are 14 days for snapshots, 120 days for outcomes and 60 days for run metadata; the workflow's capacity guard also bounds active/rollback publications and row counts. OHLCV retains 400 bars per ticker and display history retains 30 trading days. The obsolete `SUPABASE_RETENTION_DAYS` setting is not used.

Monitor organisation egress separately from database size. Storage checks do not impose a monthly bandwidth budget, and repeated historical reads still consume egress when publication fails.

Keep secret keys and encoded database connection strings in server-side secrets. Never put them in browser code, committed environment files or container build contexts.
