# Cloud deployment

This project is ready to publish the daily watchlist report with GitHub Actions and GitHub Pages.

## What it does

- Runs `python daily_watchlist_overview.py --refresh`.
- Publishes `daily_watchlist_overview_latest.html` as the site homepage.
- Publishes the latest CSV beside the HTML report.
- Runs at 8:00am Australia/Melbourne time, including daylight saving changes.
- Can also be run manually from the GitHub Actions tab.

## One-time setup

1. Create a GitHub repository for this folder.
2. Push this project to that repository.
3. In GitHub, open `Settings -> Pages`.
4. Set `Build and deployment -> Source` to `GitHub Actions`.
5. Open the `Actions` tab and run `Daily Watchlist Pages` manually once.

After the first successful run, GitHub will show the public Pages URL in the workflow summary.

## Published files

- `index.html`: the main report page.
- `daily_watchlist_overview_latest.html`: same report page, explicit filename.
- `daily_watchlist_overview_latest.csv`: latest signal data.
- `daily_watchlist_overview_failures.csv`: failed symbols, when present.
- `daily_watchlist_overview_stale_cache.csv`: cache fallback details, when present.

## Notes

GitHub Actions runners have normal outbound internet access, so Yahoo refreshes should work there even when a local Codex session has restricted network access.
