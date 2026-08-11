# CLAUDE.md

Reference for Claude Code when working in this repo. See `README.md` for a human-oriented project overview and setup instructions.

## Commands

```bash
# Run dev server
DJANGO_SETTINGS_MODULE=settings.local-development python manage.py runserver

# Run tests (Django test runner, not pytest)
DJANGO_SETTINGS_MODULE=settings.test python manage.py test

# Lint (CI-enforced). ruff.toml only excludes */migrations/; rules are ruff's defaults.
ruff check .

# Dependency vulnerability audit (CI-enforced)
pip-audit

# Static analysis for security issues (in dev-requirements.txt, not run in CI)
bandit -r .

# Migrations
python manage.py makemigrations
python manage.py migrate
```

`manage.py` defaults `DJANGO_SETTINGS_MODULE` to `settings.local-development` if unset, so `python manage.py <cmd>` works without the env var for local dev, but not for tests (see settings note below).

## Architecture

Django 6.1 monolith with HTMX (`django-htmx`) for interactivity and server-rendered templates (Bootstrap 5) — no SPA/JS framework, no REST API layer. PostgreSQL via `psycopg`.

Apps:
- `core/` — project wiring only: `urls.py` (root URLConf), `asgi.py`/`wsgi.py`. No models or views of its own.
- `common/` — cross-cutting: `BaseModel` (abstract base with `created_at`/`updated_at`/`created_by`), `Account`, `Profile`, the tenant helpers `get_profile`/`get_account`, the dashboard view, and `serve_upload` (see Uploads). Login lives in `core/urls.py` directly.
- `upkeep/` — the actual domain app: `Location`, `Item`, `Task` models, all views, forms, templatetags.
- `settings/` — see below.

**Multi-tenancy model:** `common.Account` is the tenant boundary. `Profile.account` links a `User` to an `Account`. `upkeep.Location.account` scopes locations to a tenant; `Item` and `Task` cascade down from `Location` (no direct `account`/`user` FK on them — always reach the tenant through `item.location.account`). When writing queries or views, filter through `Location`, not through `request.user` directly.

Resolve the tenant with `common.models.get_account(user)` (it tolerates a missing `Profile`) rather than `request.user.profile.account`, and decorate any view touching tenant data with `upkeep.views.account_required`. `Location.account` is nullable, so an `account=None` filter matches orphaned rows instead of matching nothing — the decorator is what stops an account-less user inheriting them.

**Active location pattern:** the app is single-active-location, not multi-select. `upkeep.context_processors.active_location` (registered in `settings/common.py`) runs on every request and injects `active_location`, `user_locations`, and `account` into template context, backed by `request.session["active_location_id"]`. Any view listing/creating `Item`/`Task` data must filter by the active location itself — the context processor does not do this for view logic, only for template globals (nav/selector). Both the context processor and the views resolve it through `upkeep.selectors.get_active_location(request)`, which validates the session id against the account and repairs a stale one; do not re-implement the fallback inline.

**Models:** new domain models should extend `common.models.BaseModel` unless there's a specific reason not to (it gives audit fields for free).

**Uploads:** user files (`Item.receipt_file`, `Profile.profile_picture`) are served by the app at `/media/<path>` via `common.views.serve_upload`, not by the reverse proxy. `django.conf.urls.static` is deliberately not used — it silently no-ops when `DEBUG` is False, which is why uploads had no URL at all in the deployed environments. `serve_upload` resolves each path back to the row that owns it and serves only files belonging to the requester's account; anything no row claims 404s, and refusals are 404 rather than 403 so the endpoint doesn't confirm which paths exist.

Adding a new `FileField`/`ImageField` therefore means adding its ownership rule to `common.views._may_access_upload` — otherwise the file is unreachable by design.

## Settings

Split by environment under `settings/`, all importing from `settings/common.py`:
- `common.py` — shared base config. Don't edit for local-only needs.
- `local-development.py` — local dev (debug, console logging).
- `test.py` — in-memory sqlite, `MD5PasswordHasher` (fast, insecure — test-only), locmem email backend. Tests must run with this settings module; `local-development`'s Postgres backend will not work with the test DB assumptions.
- `deployed.py` — shared hardening for the deployed environments (DEBUG off, proxy/TLS, HSTS, JSON logging). Not used directly.
- `stage.py`, `prod.py` — thin re-exports of `deployed.py`; put genuinely environment-specific overrides here.

Env vars are read from a root `.env` file via `django-environ` (see `settings/common.py`): `SECRET_KEY`, `MEDIA_ROOT`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST`, `DATABASE_PORT` (the DB vars have local dev defaults; `SECRET_KEY` does not).

## Testing

Django's built-in test runner, split into multiple files per app by concern rather than one `tests.py`:
- `upkeep/tests_models.py`, `tests_views.py`, `tests_tasks.py`, `tests_grouping.py`, `tests_task_form.py`, `tests_tenancy.py`, `tests_active_location.py`
- `common/tests_profiles.py`, `tests_media.py`

When adding tests for a new concern, prefer a new `tests_<concern>.py` file over growing an existing one, matching this pattern.

## CI

`.github/workflows/homelab-build-push.yml` runs on every push: `ruff check .` and `pip-audit` must pass before the multi-arch (amd64+arm64) Docker image is built and pushed. `bandit` is available in `dev-requirements.txt` but is not currently part of CI.
