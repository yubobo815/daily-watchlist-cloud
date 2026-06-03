# Vercel deployment

This repo contains a static Vercel app. It intentionally has no Next.js dependency so Vercel can deploy it quickly without framework security/version gates.

## Data flow

- GitHub Actions still refreshes the scanner each day around 8:00am Australia/Melbourne.
- The refresh writes current watchlist rows and 30-day behavior history to Supabase.
- Vercel serves the interactive app and reads Supabase directly in the browser.
- Public Vercel access is read-only. It lets visitors view/filter/download browser-visible data, but it does not grant project edit access.

## Supabase config

Set these Vercel environment variables:

```text
SUPABASE_URL
SUPABASE_ANON_KEY
```

The Vercel app reads Supabase through `/api/supabase`, so the committed frontend code does not need a hardcoded project URL or anon key.

Do not add `SUPABASE_SERVICE_ROLE_KEY` to Vercel. The service-role key is only for GitHub Actions refresh jobs.
