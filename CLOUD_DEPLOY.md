# Cloud deployment

This project is ready to publish the daily watchlist report with GitHub Actions and GitHub Pages.

## What it does

- Runs `python daily_watchlist_overview.py --refresh`.
- Publishes the app shell (`index.html`) as the site homepage.
- Publishes the latest CSV beside the HTML report.
- Saves each refresh into Supabase when the Supabase secrets are configured.
- Runs at 8:00am Australia/Melbourne time, including daylight saving changes.
- Can also be run manually from the GitHub Actions tab.

## One-time setup

1. Create a GitHub repository for this folder.
2. Push this project to that repository.
3. In GitHub, open `Settings -> Pages`.
4. Set `Build and deployment -> Source` to `GitHub Actions`.
5. Open the `Actions` tab and run `Daily Watchlist Pages` manually once.

## Optional Supabase history database

1. Open Supabase SQL Editor.
2. Run the SQL in `supabase_schema.sql`.
3. In GitHub, open `Settings -> Secrets and variables -> Actions`.
4. Add `SUPABASE_URL`.
5. Add `SUPABASE_SECRET_KEY` with a Supabase `sb_secret_...` key.

After that, every cloud refresh writes:

- `watchlist_snapshots`: one row per ticker per run date.
- `watchlist_behavior_history`: one row per ticker per replayed history date.

The secret key is only for GitHub Actions and server-side Vercel API routes. Do not put it into browser JavaScript.
The published app should use Vercel API routes or static fallback JSON rather than exposing Supabase query config in browser JavaScript.

After the first successful run, GitHub will show the public Pages URL in the workflow summary.

## Published files

- `index.html`: the main report page.
- `daily_watchlist_overview_latest.csv`: latest signal data.
- `history.html`: ticker behavior history viewer.
- `watchlist_behavior_history_latest.csv`: latest 30-trading-day behavior history.
- `data/latest.json`: static fallback latest watchlist data.
- `data/history.json`: static fallback ticker history data.
- `daily_watchlist_overview_failures.csv`: failed symbols, when present.
- `daily_watchlist_overview_stale_cache.csv`: cache fallback details, when present.

## Notes

GitHub Actions runners have normal outbound internet access, so Yahoo refreshes should work there even when a local Codex session has restricted network access.
