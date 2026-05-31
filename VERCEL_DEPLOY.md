# Vercel deployment

This repo contains a static Vercel app. It intentionally has no Next.js dependency so Vercel can deploy it quickly without framework security/version gates.

## Data flow

- GitHub Actions still refreshes the scanner each day around 8:00am Australia/Melbourne.
- The refresh writes current watchlist rows and 30-day behavior history to Supabase.
- Vercel serves the interactive app and reads Supabase directly in the browser.
- Public Vercel access is read-only. It lets visitors view/filter/download browser-visible data, but it does not grant project edit access.

## Supabase browser config

The app loads the existing public browser config from:

```text
https://yubobo815.github.io/daily-watchlist-cloud/supabase-config.js
```

The Supabase anon key is public read-only because table policies only allow `select`. The Supabase service role key must not be added to Vercel. It stays only in GitHub Actions.
