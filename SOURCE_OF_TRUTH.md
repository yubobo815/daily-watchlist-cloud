# Source of truth

`daily-watchlist-cloud` is the only production source for the watchlist system.

Production-owned code lives here:

- Scanner logic: `daily_watchlist_overview.py`
- Production app UI: `index.html`, `assets/app.js`, `assets/styles.css`
- Vercel API routes: `api/`
- Supabase schema and sync contract: `supabase_schema.sql`
- Scheduled refresh workflow: `.github/workflows/daily-watchlist-pages.yml`
- App and logic audits: `scripts/`

The older local scanner folder:

```text
/Users/williamyu/Documents/Codex/2026-05-28/i-have-another-pine-script-please
```

is an archive/lab workspace only. Do not make new production logic there. If useful logic is found there, migrate it into this repository first, then test and commit it here.

## Operating rules

- Make all formal scanner, app, workflow, and Supabase changes in this repository.
- Keep `BUY`, `TRENDING`, `BUILDING`, `WATCH`, `EXIT`, and `AVOID` labels aligned across Python output, app UI, and audits.
- Keep Pine/TradingView as the final chart confirmation layer; this app is a scanner and execution-support dashboard, not a trade execution authority.
- Do not commit generated market-data caches unless they are intentional static fallback artifacts under `data/`.
- Run `npm run audit:watchlist` before pushing production logic changes.
