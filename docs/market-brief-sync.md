# Homepage market research

## Active publication order (authorised 31 October 2026)

ChatGPT/Codex curates the market-only content. GitHub publishes it immediately
after the daily watchlist has passed verification and activated successfully.
No scanner, signal rule, trading conclusion or historical forecast is changed.

1. Read the newest completed monthly US post-close report and original embedded
   US outlook. Prepare a normal owner-authored, data-only PR **before** the
   watchlist finishes. Normal `pull_request` Quality checks run automatically.
2. `daily-watchlist-pages.yml` runs `dispatch-market-brief` immediately after
   `verify-and-activate` succeeds. It dispatches `market-brief-sync.yml` on main,
   carrying the real upstream run ID and activated publication ID. It does not
   wait for storage maintenance or a later clock slot. GitHub runner queueing
   can still delay execution; this is not a precise-time guarantee.
3. The publisher checks the trusted upstream activation, real production US
   dates, owner-authored ready PR, read-only Drive source/hash, and real PR CI.
   It renews the short-lived Google token, re-reads Drive and live data, then
   merges only the exact tested head through unchanged main protection.
4. Verify Vercel production JSON and the rendered source date and outlook.

The dispatcher is gated by `MARKET_BRIEF_SYNC_ENABLED=true`. A dispatch transport
failure must not roll back good watchlist data or rerun the scanner. The failed
step stays visible; retry only the summary publisher with the same real IDs.
The standalone publisher has no cron schedule. Keep the existing local recovery
task until a real cloud publication has passed all gates and production checks.

## Curator / ready PR contract

Use a fresh clean checkout of current main, preserving the user's dirty tree.
Branch: `codex/market-brief-ready-YYYY-MM-DD` (US session date; optional numeric
retry suffix). Author: existing owner account `yubobo815`. Exactly one commit
directly from current main, changing only `data/market-brief.json`. Never use
`GITHUB_TOKEN` to create this PR. Attach every created PR to the current chat.
Run `npm run audit:market-brief`, `npm run audit:watchlist`, syntax checks and
`npm run uat:docker`; all three real PR Quality jobs must also pass.

Prepare content even if the watchlist has not finished: readiness is enforced at
publication, not a reason to postpone curation. If the report arrives after
activation, dispatch the publisher as recovery using that successful main run
and actual live publication ID. Do not rerun a scanner/rebuild just for research.
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
The original daily filename is `YYYY-MM-DD.md`, with an optional `-vN` suffix.
Exclude weekly reports, PM/AU/Asia previews, forecast logs and unfinished files.
Verify the actual US session in the report body rather than using the Australian
filename date. It must equal `assets/market-session.js`'s latest completed US
cash-market session, including holidays, DST and early closes.

Use the **original US outlook in section 9**, not a revised row in section 10,
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

## Live gates and recovery

Require `live_access_ok=true`, status success/ok/degraded, a nonempty publication
ID and nonempty rows all carrying that ID. Every row needs a valid date and
ticker. Derive the US session from US rows, not global `latest_data_date` or
run timestamps. Explicit `.AX` rows use their own exchange date; at least one
US row must match the target and no US row may be future-dated. Older US rows
and honest partial coverage are allowed; never backdate rows or claim full
coverage. `scripts/check_market_brief_alignment.cjs` implements these gates.

On stale/missing/mismatched inputs, preserve the last valid public snapshot and
retry only the publisher after the missing input is ready. Source changes or
main changes during CI fail closed. An unchanged already-published snapshot is
a no-op only after matching current source IDs, timestamps and content. Local
recovery checks read the small production JSON and Drive metadata first; avoid
full watchlist/report reads, audits and PRs when unchanged. Routine waiting is
quiet; surface meaningful failures or required user action, deduplicated.

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
Manual/recovery `mode=sync` also requires `upstream_run_id` and
`expected_publication_id`. It will not publish from an unverified/older run.
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
