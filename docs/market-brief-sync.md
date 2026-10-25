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

## GitHub migration: read-only authorization stage

`market-brief-sync.yml` currently provides a **manual authorization probe only**,
not a scheduled publisher. The existing Codex sync remains active until the
curated structured-summary producer and protected-PR publishing path have both
passed an end-to-end production check. Do not claim the migration is complete
because this probe succeeds.

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

Run **Market brief Drive access** manually on `main`. It checks that the folder
cannot be edited or receive new children, verifies both already-published source
files are in that folder, and reads their text without printing or uploading it.
It has no repository write permission, does not update the public snapshot, and
does not run the scanner or calibration rebuild. Run
`npm run audit:market-brief-drive` for the isolated permission/safety regressions.
