# Homepage market research

## Active publication order

The curator prepares the brief from the completed monthly Drive report. Dispatch
`market-brief-sync.yml` on main with `mode=sync` after preparing the owner-authored
ready PR. Daily Brief publication is independent of watchlist builds and activation.
The publisher verifies the live Drive source and exact PR Quality checks, rechecks
the completed US session, and merges only through unchanged branch protection.
Verify the live JSON and rendered homepage after publication.

## Curator / ready PR contract

Use a fresh clean checkout of current main, preserving the user's dirty tree.
Branch: `codex/market-brief-ready-YYYY-MM-DD` (US session date; optional numeric
retry suffix). Author: existing owner account `yubobo815`. Exactly one commit
directly from current main, changing only `data/market-brief.json`. Never use
`GITHUB_TOKEN` to create this PR. Attach every created PR to the current chat.
Run `npm run audit:market-brief`, `npm run audit:watchlist`, syntax checks and
`npm run uat:docker`; all three real PR Quality jobs must also pass.

If main advances, refresh the data-only commit against current main and retest.
Never replace required PR checks with `workflow_dispatch` tests, fake statuses,
automatic approval, an admin bypass, a new GitHub App or a stored PAT.

Include `provenance.report` and `provenance.forecast`, each exactly
`{id, modified_at, sha256}`. For the embedded outlook both identify the **same
original file**, with a SHA-256 of its exact downloaded bytes. Read metadata
before and after the full original read; reject changing/incomplete uploads.
Keep private raw reports outside the repository and out of workflow artifacts
and logs. Only the concise public JSON is committed.

## Monthly source selection

Use **Market Desk Reports**, parent `1KjIqM7VurftWyjCH3kygjywSMyKZWv4d`, through
the existing connected Drive account. Discover current and previous `YYYY-MM`
folders dynamically, including month rollover; never permanently pin October.
The original daily filename is `YYYY-MM-DD.md`, with an optional `-vN` suffix,
or `US_AI_Daily_<publication-date>_US-<session-date>_v1.md` in its publication month.
Exclude weekly reports, PM/AU/Asia previews, forecast logs and unfinished files.
Verify the actual US session in the report body rather than using the Australian
filename date. It must equal `assets/market-session.js`'s latest completed US
cash-market session, including holidays, DST and early closes.

Use the **original US outlook in section 9**, or the approved newer
**section 4 "新美股展望" three-way paragraph layout**, or the original AM report's
**section 3.1 NEW forecast block** or **section 6.2 New Forecast Card** with
its verified report issue time and section 6.3 scored sample, not a revised row in section 10,
an older independent card, or an ASX outlook. Preserve probabilities, reference
close, final-close boundaries, horizon, limitations and US completed sample.
If no author-issued forecast ID exists, use
`drive:<original-file-id>#us-original-outlook` and disclose that it is an archive
locator in `method`. If exact original issue time is absent, use the completed
Drive modification time for `issued_at` and disclose that timestamp basis.
Never invent an author ID, market figure or forecast, or revise an old forecast.

The summary is **US-market-only**. Exclude Australian stocks, XJO/ASX/RBA/AUD-only
content, personal positions and account details. Do not use the ASX Reports
archive or the old `US Market & AI Daily Reports` folder as an older fallback.
Do not copy complete private reports or alter Drive originals or public sharing.

## Recovery

Preserve the last valid public snapshot when the source, session, main or CI
does not match. Retry only the brief publisher after the issue is resolved.
Never run or wait for a watchlist scan to publish the brief.

## Read-only cloud identity

The dedicated service account has Viewer access to Market Desk Reports; General
access stays **Restricted**. Use existing Google Workload Identity Federation
bound to this repository, main and `market-brief-sync.yml`; no new private keys,
project roles or paid services. OAuth scope is `drive.readonly`, lifetime ten
minutes, renewed after CI. Non-secret variables:

- `GOOGLE_WORKLOAD_IDENTITY_PROVIDER`
- `GOOGLE_DRIVE_SERVICE_ACCOUNT`
- `MARKET_REPORTS_DRIVE_FOLDER_ID` = the monthly archive parent above

Manual `mode=verify` reads the monthly archive without content logs or writes.
Manual/recovery `mode=sync` has no watchlist inputs.
The former bot-created-PR/manual-CI prototype is retained in legacy scripts for
audit history only; its workflow is replaced and must not be reinstated.

## UI contract

The homepage reads `data/market-brief.json` independently of scanning. Preserve
the segmented Bull/Base/Bear strip, original ranges, visible source/session
dates and not-a-trade-signal label. Do not restore removed conditions/source
panels, calibration/method paragraphs or version labels in the UI; retain this
metadata in JSON for auditability. Vercel serves the repository brief; Pages
includes it at the next ordinary watchlist publication. No browser gets Drive
credentials and no extra Supabase polling is added by the curator.
