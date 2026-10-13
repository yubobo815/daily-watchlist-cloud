# Contributing

Use the setup instructions in [README.md](README.md). Development and CI use Python 3.11 or later and Node.js 24; install the pinned Python requirements and run `npm ci`.

## Before opening a pull request

- Keep changes focused and explain the user-visible behaviour they improve.
- Run `npm run audit:watchlist` and syntax checks for changed Python/JavaScript files.
- For frontend or execution-plan changes, run `npm run uat:docker` with Docker running. This exercises frozen-plan behaviour on desktop and mobile.
- Add regression coverage for reproducible bugs. Use fixtures or mocks rather than production database writes or live market-data dependencies.
- Do not commit environment files, credentials, local caches, generated reports or QA artefacts. `.env.example` documents configuration without credentials.
- Preserve publication validation, freshness gates, execution blocking, calibration parity and rollback protection.
- Keep the user-facing labels `BUY`, `TRENDING`, `BUILDING`, `WATCH`, `EXIT` and `AVOID` consistent across the scanner, API and frontend.

The Quality workflow checks pull requests and pushes to `main`. A passing quality run validates code and fixtures; production refresh health and market-data freshness still need their own verification.

Large changes to scanner rules or learning behaviour should include their assumptions and validation evidence. TradingView/Pine remains the final chart-confirmation layer.

For a suspected vulnerability, follow [SECURITY.md](SECURITY.md) rather than posting credentials or sensitive details in a public issue.
