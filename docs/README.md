# Docs directory

This repository exposes a small docs split to balance convenience and security.

- `docs/public/` — static files served publicly at `/docs/` by the Flask app. Place non-sensitive documentation here.
- `docs/private/` — files that should not be publicly mounted. Protected pages (for admins) are served explicitly from this folder by guarded Flask routes, for example `/admin/audit-logs/viewer`.

Admin UI
- Use `/admin/dashboard` to open the admin dashboard.
- Sign in with `/admin/login` (username/password for an admin account); the dashboard uses a secure session cookie and CSRF token for admin actions.
- `/admin/logout` clears the admin session.

Security notes
- Keep sensitive HTML/JS in `docs/private/` and ensure server-side routes enforce admin auth.
- For production, host static files behind a hardened web server and avoid serving secret-backed files directly from the app repository.
- Set `FLASK_ENV=production` or `ENABLE_SECURITY_HARDENING=true` to enable secure cookies and HSTS for admin routes.
