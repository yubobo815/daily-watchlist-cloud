# Homepage market research

The visible homepage section reads `data/market-brief.json` independently of the scanner and Supabase. It is a curated public summary, not a copy of the private reports. Drive permissions stay unchanged; report links require the visitor's existing access.

The homepage does not render a forecast-conditions/source disclosure. Keep the underlying provenance and forecast conditions in the validated JSON for syncing and auditability; do not add the removed disclosure back during daily updates. Dates, expiry and the uncertainty note remain visible.

## Daily Codex sync contract

Use only the private **US Market & AI Daily Reports** folder, ID `1vFVQbX-xmbVrOSO4OXDGb1ACwZF3-oXw`, through the existing connected Drive account. Find the latest final dated daily report and its matching, separately issued forecast card. Do not mistake `forecast-log.md`, a prior forecast or an unfinished report for the current outlook.

Update only `data/market-brief.json`. Preserve the report's actual US session date, publication timestamp, source file IDs and modified timestamps. Whitelist market facts, concise interpretation, public citations and the original forecast ID, probabilities, final-close boundaries, horizon, limitations and completed calibration sample. Never publish private account details, personal positions, credentials or entire source documents. Do not add unsupported data or invent a model forecast. A changed judgement requires a new forecast ID from the source, never retrospective edits.

Identical source IDs, modification times and content are a no-op. If the source is missing, inconsistent or older than the published report, retain the last valid snapshot; never relabel it as today's report. The UI independently labels dated reports by completed US market sessions and archives forecasts after their evaluation time. No browser has access to Drive credentials, no Google sharing changes are needed and there is no added Supabase egress.

Validate with `npm run audit:market-brief` (an optional file path can be passed with `-- path/to/file.json`), then `npm run audit:watchlist` and `npm run uat:docker`. Publish through a pull request and the protected main branch's required checks; merge only the tested head SHA after all checks pass. Verify the deployed JSON and rendered section on production. Do not trigger a full scanner or weekly calibration just to publish research. GitHub Pages includes the brief on its next ordinary watchlist publication; Vercel serves it directly from the repository.

The Codex sync uses this chat's existing Drive and GitHub connections. This is a local scheduled task: the host must be available and connections must remain authorised. A schedule is not a guarantee of successful publication; source dates remain visible if a run cannot finish.
