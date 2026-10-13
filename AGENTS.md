# Agent Instructions

This repository is the only production source for the daily watchlist app, scanner, Supabase schema, and refresh workflow.

- Older scanner checkouts and archive/lab folders are reference material, not production sources.
- If code or logic from the archive/lab folder is useful, migrate it into this repository and verify it here before committing.
- Keep user-facing action labels synchronized: `BUY`, `TRENDING`, `BUILDING`, `WATCH`, `EXIT`, `AVOID`.
- Before pushing production logic changes, run `npm run audit:watchlist` and syntax checks for touched Python or JavaScript files.
- Preserve the product boundary: scanner output supports decision-making; `BUY` candidates still require TradingView/Pine chart confirmation before acting.
