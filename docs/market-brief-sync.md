# Homepage market research

The visible homepage section reads `data/market-brief.json` independently of the scanner and Supabase. It is a curated public summary, not a copy of the private reports. Drive permissions stay unchanged; report links require the visitor's existing access.

The homepage does not render a forecast-conditions/source disclosure or the method/calibration-sample paragraph. Keep underlying provenance, forecast conditions, method and calibration sample in the validated JSON for syncing and auditability; do not add the removed text back during daily updates. Dates, expiry and the research-outlook/not-a-trade-signal label remain visible.

v5 shows the report probabilities as one segmented Bull/Base/Bear strip, with the existing final-close ranges below. This explicitly replaces the earlier text-only presentation. Do not restore three independent progress bars or isolated large percentages; daily syncs update JSON only.

## Daily Codex sync contract

Use only the private **US Market & AI Daily Reports** folder, ID `1vFVQbX-xmbVrOSO4OXDGb1ACwZF3-oXw`, through the existing connected Drive account. Find the latest final dated daily report and its matching, separately issued forecast card. Do not mistake `forecast-log.md`, a prior forecast or an unfinished report for the current outlook.

Update only `data/market-brief.json`. Preserve the report's actual US session date, publication timestamp, source file IDs and modified timestamps. Whitelist market facts, concise interpretation, public citations and the original forecast ID, probabilities, final-close boundaries, horizon, limitations and completed calibration sample. Never publish private account details, personal positions, credentials or entire source documents. Do not add unsupported data or invent a model forecast. A changed judgement requires a new forecast ID from the source, never retrospective edits.

Identical source IDs, modification times and content are a no-op. If the source is missing, inconsistent or older than the published report, retain the last valid snapshot; never relabel it as today's report. The UI independently labels dated reports by completed US market sessions and archives forecasts after their evaluation time. No browser has access to Drive credentials, no Google sharing changes are needed and there is no added Supabase egress.

Validate with `npm run audit:market-brief` (an optional file path can be passed with `-- path/to/file.json`), then `npm run audit:watchlist` and `npm run uat:docker`. Publish through a pull request and the protected main branch's required checks; merge only the tested head SHA after all checks pass. Verify the deployed JSON and rendered section on production. Do not trigger a full scanner or weekly calibration just to publish research. GitHub Pages includes the brief on its next ordinary watchlist publication; Vercel serves it directly from the repository.

The Codex sync uses this chat's existing Drive and GitHub connections. This is a local scheduled task: the host must be available and connections must remain authorised. A schedule is not a guarantee of successful publication; source dates remain visible if a run cannot finish.

## GitHub scheduled publisher

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
