# Vercel deployment

This repo contains a static Vercel app. It intentionally has no Next.js dependency so Vercel can deploy it quickly without framework security/version gates.

## Data flow

- GitHub Actions still refreshes the scanner each day around 8:00am Australia/Melbourne.
- The refresh writes current watchlist rows and 30-day behavior history to Supabase.
- Vercel serves the interactive app and reads Supabase through app API routes.
- `/api/watchlist/latest` returns latest rows, previous rows, and run health in one response.
- `/api/ticker/[ticker]` returns ticker history, latest snapshot, company profile, and run health in one response.
- Public Vercel access is read-only. It lets visitors view/filter/download browser-visible data, but it does not grant project edit access.

## Supabase config

Set these Vercel environment variables:

```text
SUPABASE_URL
SUPABASE_SECRET_KEY
```

The Vercel app reads Supabase through narrow app APIs, so the frontend does not receive the Supabase project URL, secret key, or table-query details.

Prefer `SUPABASE_SECRET_KEY` with a Supabase `sb_secret_...` key. The legacy `SUPABASE_SERVICE_ROLE_KEY` still works as a fallback, but do not expose either key in browser JavaScript.
