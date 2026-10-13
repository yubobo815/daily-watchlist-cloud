# Security

Report suspected vulnerabilities through GitHub's [private vulnerability reporting](https://github.com/yubobo815/daily-watchlist-cloud/security/advisories/new) for this repository. Do not post credentials, private Focus List contents or exploit details in public issues or pull requests.

Use the current `main` branch when reporting an issue and include the affected route or component, reproduction steps and impact. Remove credentials and personal information from examples and logs.

Supabase secret/service-role keys, database connection strings and Focus List PINs belong in GitHub Actions secrets or server-side environment variables. They must not be exposed in browser code, committed environment files or container images.

The Focus List API requires its configured PIN. Shared PIN access is not a multi-user authentication system. Deployment owners are responsible for choosing and maintaining appropriate credentials.
