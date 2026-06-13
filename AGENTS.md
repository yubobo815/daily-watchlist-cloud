# Agent Instructions

This repository is the only production source for the daily watchlist app, scanner, Supabase schema, and refresh workflow.

- Do not treat `/Users/williamyu/Documents/Codex/2026-05-28/i-have-another-pine-script-please` as a production repo. It is archive/lab material only.
- If code or logic from the archive/lab folder is useful, migrate it into this repository and verify it here before committing.
- Keep user-facing action labels synchronized: `BUY`, `TRENDING`, `BUILDING`, `WATCH`, `EXIT`, `AVOID`.
- Before pushing production logic changes, run `npm run audit:watchlist` and syntax checks for touched Python or JavaScript files.
- Preserve the product boundary: scanner output supports decision-making; `BUY` candidates still require TradingView/Pine chart confirmation before acting.
