# Homepage market research

The visible homepage section reads `data/market-brief.json` independently of the scanner and Supabase. It is a curated public summary, not a copy of the private reports. Drive permissions stay unchanged; report links require the visitor's existing access.

The homepage does not render a forecast-conditions/source disclosure or the method/calibration-sample paragraph. Keep underlying provenance, forecast conditions, method and calibration sample in the validated JSON for syncing and auditability; do not add the removed text back during daily updates. Dates, expiry and the research-outlook/not-a-trade-signal label remain visible.

v5 shows the report probabilities as one segmented Bull/Base/Bear strip, with the existing final-close ranges below. This explicitly replaces the earlier text-only presentation. Do not restore three independent progress bars or isolated large percentages; daily syncs update JSON only.

## Daily Codex sync contract

This is the active publisher. GitHub scheduled publishing stays disabled
(`MARKET_BRIEF_SYNC_ENABLED=false`); do not create a publishing App, approve
workflow runs automatically, or bypass protected checks.

Publication order is completion-gated: final morning US-close report and its
original forecast saved/read back in Drive; scanner has activated its live
publication for the same US session; publish the concise summary through a tested
PR; verify production JSON and rendering. A scheduled start is not proof that
either upstream task has finished. Never use the evening AU/Asia preview as a
replacement for the morning US-close report.

## Active source selection (authorised 29 October 2026)

Use **Market Desk Reports** (Drive parent ID `1KjIqM7VurftWyjCH3kygjywSMyKZWv4d`),
under its `YYYY-MM` month folders. Discover the appropriate month dynamically,
including the previous month around month boundaries; do not permanently pin
October. The verified October folder is `1ZwBqRqDDilX7PrHrOPLjdai4XqXsJigK`.
Select the newest completed **US post-close daily report** by the US trading
session stated in its body, not its filename, upload date or Australian date.
For example, `2026-10-29.md` covers the US 28 October session.

Use the original US outlook embedded in that same report. A separately issued
forecast card is **not required** for this monthly source. Preserve its stated
probabilities, reference close, final-close boundaries, horizon, limitations and
US-only completed calibration sample. Do not splice in an older independent
forecast, a later revision, an ASX outlook or an entry from `forecast-log.md`.
If the source has no forecast ID, use a transparent source locator such as
`drive:<file-id>#us-original-outlook` in `forecast.id`; explain in `method` that
this is an archive locator, not a forecast ID assigned by the author. Never
invent an author-issued ID or an exact issue timestamp. If the report has no
precise publication time, use its verified completed Drive modification time
for `issued_at` and disclose that timestamp basis in `method`.

The public summary is US-market-only, even when the source includes an ASX
appendix. Exclude Australian stocks, XJO/ASX forecasts, RBA/AUD-only sections,
personal holdings and account details. Do not use the separate **ASX Reports**
archive as a substitute for a morning US-close report. Original Drive sharing
and files must remain unchanged.

The former `US Market & AI Daily Reports` folder is a legacy source, not the
sole discovery scope or an automatic fallback to an older session. Existing
published snapshots keep their original provenance. The disabled GitHub
publisher prototype below retains its separate-card contract and must remain
disabled; it does not define the active Codex source selection.

The existing morning producer is scheduled at 10:00 Melbourne, Monday through
Saturday. Tuesday–Saturday normally cover the preceding completed US session,
including Friday's US close on Saturday. The ASX calendar gates only the AU
opening-preview section, never the US-close report. Monday retains the AU
weekend/next-open analysis and reuses Friday's already archived US sources;
do not duplicate reports, relabel a session or manufacture another forecast.

The existing local heartbeat checks every 15 minutes from 11:00 through 23:45
Melbourne. This replaces the hourly cadence and extends the recovery window
when GitHub starts a scanner hours late. It is bounded polling, **not** a
GitHub-completion webhook or a guarantee of immediate/precise execution.
The machine, app and connections must be available. Once both inputs pass the
gates, complete the publication in that run rather than waiting for another slot.
At each check use the latest completed US session from `assets/market-session.js`,
not the Melbourne run date. Run
`node scripts/check_market_brief_alignment.cjs --candidate path/to/candidate.json`
before creating a publishing PR, and again immediately before merging its exact
tested head. Exit 2 means wait for a later check; exit 1 means an invalid or
unavailable input. Preserve the last valid summary in either case. Partial
coverage is allowed when honestly disclosed; never turn it into claimed full
coverage. A mixed publication identity is not allowed. For this US-market brief,
derive the US session date from the live US ticker rows: an explicitly identified
ASX ticker ending in `.AX` may have a different local session date and must not
set the US date. Require valid dates and identity for every row, at least one
US row at the completed session, and no future-dated US rows. Do not alter
the original row dates or pretend partial coverage is complete.

The alignment CLI retries explicit fallback/transport/HTTP 5xx failures at most
three total attempts, with 1-second and 3-second pauses and a 15-second request
timeout. A valid but old publication, malformed JSON, a permissions error, or
any failed date/identity gate is never turned into permission to publish.
Persistent fallback remains a wait/failure; do not claim recovery or repeat the
full scanner. An unchanged completed snapshot still exits before any full
watchlist fetch, checkout, audit or PR work.

Normal upstream waiting stays quiet. At the final 23:45 check, surface an
actionable failure if the newest completed session is still blocked, including
the expected/report/watchlist dates and which input is missing. An already
published unchanged snapshot is always a no-op. Repeated daily failures should
be deduplicated unless their cause or required action changes. This is bounded
polling, not an event-driven dependency or an availability guarantee; the host
and connected accounts must be available.

Avoid repeated full-watchlist reads: check the small published brief and Drive
metadata first. If the latest completed session is already published with the
same source IDs/modification times, return immediately without full report or
watchlist downloads, audits or PR creation. Fetch the watchlist only for a new
or changed candidate awaiting publication.

Use the monthly **Market Desk Reports** source above through the existing connected Drive account. Verify the final report's metadata and completed text readback, including the original US outlook within that file. Do not mistake `forecast-log.md`, a prior forecast, a revision or an unfinished report for the current original outlook.

For routine content syncs update only `data/market-brief.json`. Preserve the report's actual US session date, publication timestamp (or explicitly disclosed completed-upload timestamp), source file ID and modified timestamp. Whitelist market facts, concise interpretation, public citations and the original forecast ID (or explicitly disclosed source locator), probabilities, final-close boundaries, horizon, limitations and completed US calibration sample. Never publish private account details, personal positions, credentials or entire source documents. Do not add unsupported data or invent a model forecast. Preserve original forecasts; a changed judgement must be separately identified, never a retrospective edit.

Only a report ID, modification time and meaningful content matching the currently deployed snapshot is a no-op; an unchanged source across unsuccessful readiness checks is still pending, not published. Re-evaluate that pending report against the watchlist on the next check and publish when ready. No second card is needed for an embedded outlook. If the source is missing, inconsistent or older than the published report, retain the last valid snapshot; never relabel it as today's report. The UI independently labels dated reports by completed US market sessions and archives forecasts after their evaluation time. No browser has access to Drive credentials, no Google sharing changes are needed and there is no added Supabase egress.

Validate with `npm run audit:market-brief` (an optional file path can be passed with `-- path/to/file.json`), then `npm run audit:watchlist` and `npm run uat:docker`. Publish through a pull request and the protected main branch's required checks; merge only the tested head SHA after all checks pass. Verify the deployed JSON and rendered section on production. Do not trigger a full scanner or weekly calibration just to publish research. GitHub Pages includes the brief on its next ordinary watchlist publication; Vercel serves it directly from the repository.

The Codex sync uses this chat's existing Drive and GitHub connections. This is a local scheduled task: the host must be available and connections must remain authorised. A schedule is not a guarantee of successful publication; source dates remain visible if a run cannot finish.

## Disabled GitHub publisher prototype

This prototype is retained for audit/history, not used for daily publishing.
Its live test failed closed: `workflow_dispatch` Quality checks do not satisfy
GitHub PR required-check rules, even when the jobs pass. Do not enable the
schedule or treat successful manually dispatched CI as merge eligibility.
The user chose to retain the ChatGPT/Codex publisher; no new GitHub App or
automatic approval is authorised. The description below records the prototype,
not a verified operational publishing path.

`market-brief-sync.yml` supports manual `verify` and `sync` modes. Scheduled sync
is gated by repository variable `MARKET_BRIEF_SYNC_ENABLED=true`. The schedule
uses `Australia/Melbourne`: primary 10:45, recovery 12:45. GitHub may delay a
scheduled run; unchanged source data remains a no-op. Never label old research
as current to conceal a missed run.

The dedicated Google service account has no project-level roles or private keys.
Share only the reports folder with it as **Viewer**; keep General access
**Restricted**. GitHub uses Workload Identity Federation, bound to the immutable
repository and owner IDs, the `main` branch, and this exact workflow path. No
fork or pull-request run should be able to request the Drive identity.

Configure these non-secret repository variables:

- `GOOGLE_WORKLOAD_IDENTITY_PROVIDER`: the full Google provider resource name.
- `GOOGLE_DRIVE_SERVICE_ACCOUNT`: the dedicated reader service account email.
- `MARKET_REPORTS_DRIVE_FOLDER_ID`: the authorized reports folder ID.

Enable the Google Drive API and IAM Service Account Credentials API in the
identity project. Use only the `drive.readonly` OAuth scope and a ten-minute
access token. Do not export service account keys or broaden project IAM roles.

Run **Market brief sync** with mode `verify` manually on `main`. It checks that the folder
cannot be edited or receive new children, verifies both already-published source
files are in that folder, and reads their text without printing or uploading it.
This mode does not write repository data or run the scanner/rebuild. Run
`npm run audit:market-brief-drive` for the isolated permission/safety regressions.

Mode `sync` reads the latest completed dated report and its matching approved
curation file, validates the original forecast card, timestamps and byte hashes,
then creates a PR changing **only** `data/market-brief.json`. It uses native
`GITHUB_TOKEN` permissions only in this trusted main-branch workflow; no stored
PAT or GitHub App private key is required. The repository setting allowing
Actions to create PRs must be enabled, while default workflow permissions remain
read-only. No approval API or administrator bypass is used.

Because default-token events do not automatically execute trusted PR checks,
the publisher explicitly dispatches the existing `quality.yml` on the exact
candidate commit. Both Python audit jobs and Browser UAT must really pass. It
then renews its read-only Google token, re-reads Drive to reject a superseded
candidate, verifies main and the PR head have not moved, checks the protected
statuses, and requests a squash merge with that exact head SHA. A main update,
changed source, additional changed file, failed check or merge refusal fails
closed. A rerun creates a new run-specific branch; it never force-pushes a user
branch. Failed PRs are left for inspection rather than silently discarded.

After merge, the workflow verifies the production JSON against the whole tested
snapshot and uses a real browser to check its rendered US session, outlook and
probabilities. It never runs the watchlist scanner or weekly rebuild.

The initial migration adds `provenance` containing verified report/card IDs,
modification times and SHA-256 hashes, without changing the source dates,
research text or forecast. Re-uploading identical curation must not produce
subsequent commits. Private report bodies are never logged, uploaded as CI
artifacts or copied into the public repository.

Keep the old Codex sync until the source producer confirms future JSON output
and the GitHub publisher has completed a real protected merge plus production
verification. Only then enable the schedule and retire the old local publisher.

## Required output from the existing report producer

The report-generation task, not GitHub CI, owns market judgement and the short
public summary. No paid language-model API is called by the publisher. In the
same authorized Drive folder, upload in this order:

1. Final Markdown report: `YYYY-MM-DD.md` or
   `YYYY-MM-DD-independent-us-market-ai-report-vN.md`.
2. Separately issued, immutable forecast card: `<forecast-id>.md`.
3. Last, the approved public companion:
   `market-brief-YYYY-MM-DD-vN.json` (N starts at 1).

The report date is the actual completed US market session, not the upload date.
Do not manufacture a new US session on weekends or holidays. Preserve original
forecasts; a changed judgement requires a newly issued ID and card. Do not edit
`forecast-log.md` to supply a missing card.

The companion is at most 32 KB and has exactly this envelope:

```json
{
  "schema_version": 1,
  "status": "FINAL",
  "approved_for_publication": true,
  "source_report": {"id": "ORIGINAL_REPORT_FILE_ID", "modified_at": "ORIGINAL_DRIVE_MODIFIED_TIME", "sha256": "64_LOWERCASE_HEX_DIGITS"},
  "source_forecast": {"id": "ORIGINAL_FORECAST_FILE_ID", "modified_at": "ORIGINAL_DRIVE_MODIFIED_TIME", "sha256": "64_LOWERCASE_HEX_DIGITS"},
  "brief": {}
}
```

`brief` follows `data/market-brief.json` schema version 1, excluding the computed
`provenance` field. Its only root fields are `schema_version`, `session_date`,
`issued_at`, `headline`, `summary`, `metrics`, `highlights`, `forecast`,
`limitations`, and `sources`. Preserve the full forecast schema, including
subjective probabilities, final-close boundaries, horizon, method, limitations
and completed calibration sample, even where the UI hides explanatory fields.

- `headline`: at most 180 characters; summary/limitations at most 650 each.
- One to five market-only highlights, each with a title (100 characters max)
  and text (500 characters max). No personal holdings, account details,
  credentials, complete reports or unrelated personal news.
- Exactly four metric labels in this order: `S&P 500`, `Nasdaq Composite`,
  `US 10-year yield`, `Brent futures`. Each has `label`, `value`, `detail`.
  Keep original units and a signed reported change. Unverified observations
  must be labelled unavailable, never guessed.
- Both private source links must use the original canonical
  `https://drive.google.com/file/d/ID/view` URL and include `modified_at` from
  Google metadata. Do not expose signed download URLs. Other sources are
  public HTTPS citations, without credentials in their URLs.
- Calculate each source SHA-256 from the exact uploaded bytes, not a rewritten,
  whitespace-normalized or exported approximation. Read back metadata after
  uploading the report and card; produce the companion last.
- `issued_at` is the original report publication timestamp, not the companion
  upload time. `evaluates_at` is the original forecast's official NYSE session
  close, including daylight saving and early-close treatment.

For deterministic cross-checking, the separately issued English forecast card
must state `Reference S&P 500: <number>` and
`Final official close <weekday> <day> <month> [year] is ...`. Its outcome table
must have `Bull | N% | Greater than <upper>`, `Base | N% | ...`, and
`Bear | N% | Less than <lower>` rows; retain a documented `n=<completed_sample>`.
This is a format requirement for **future cards**, not permission to rewrite
historical ones. The current 23 October card already meets it.

The newest report without a matching complete companion/card is an actionable
failure, not a reason to silently choose an older report. Ambiguous duplicates,
unexpected fields, privacy markers, stale dates, forecast revisions or changed
source bytes all preserve the last valid public snapshot and stop publishing.
