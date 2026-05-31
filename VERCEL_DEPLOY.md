# Vercel deployment

This repo now contains a Next.js app for Vercel.

## Data flow

- GitHub Actions still refreshes the scanner each day around 8:00am Australia/Melbourne.
- The refresh writes current watchlist rows and 30-day behavior history to Supabase.
- Vercel serves the interactive app and reads Supabase directly in the browser.

## Vercel environment variables

Set these in the Vercel project if you want the app to be self-contained:

```text
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
```

If these are not set, the app tries to load the existing public browser config from:

```text
https://yubobo815.github.io/daily-watchlist-cloud/supabase-config.js
```

The Supabase service role key must not be added to Vercel. It stays only in GitHub Actions.
