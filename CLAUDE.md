# CLAUDE.md

Reference for Claude Code when working in this repo. See `README.md` for a human-oriented project overview and setup instructions.

## Commands

```bash
# Run dev server
DJANGO_SETTINGS_MODULE=settings.local-development python manage.py runserver

# Run tests (Django test runner, not pytest)
DJANGO_SETTINGS_MODULE=settings.test python manage.py test

# Lint (CI-enforced, zero-config — no pyproject.toml/ruff.toml)
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

Django 5.2 monolith with HTMX (`django-htmx`) for interactivity and server-rendered templates (Bootstrap 5) — no SPA/JS framework, no REST API layer. PostgreSQL via `psycopg`.

Apps:
- `core/` — project wiring only: `urls.py` (root URLConf), `asgi.py`/`wsgi.py`. No models or views of its own.
- `common/` — cross-cutting: `BaseModel` (abstract base with `created_at`/`updated_at`/`created_by`), `Account`, `Profile`, auth-adjacent views/urls (login lives in `core/urls.py` directly).
- `upkeep/` — the actual domain app: `Location`, `Item`, `Task` models, all views, forms, templatetags.
- `settings/` — see below.

**Multi-tenancy model:** `common.Account` is the tenant boundary. `Profile.account` links a `User` to an `Account`. `upkeep.Location.account` scopes locations to a tenant; `Item` and `Task` cascade down from `Location` (no direct `account`/`user` FK on them — always reach the tenant through `item.location.account`). When writing queries or views, filter through `Location`, not through `request.user` directly.

**Active location pattern:** the app is single-active-location, not multi-select. `upkeep.context_processors.active_location` (registered in `settings/common.py`) runs on every request and injects `active_location`, `user_locations`, and `account` into template context, backed by `request.session["active_location_id"]`. Any view listing/creating `Item`/`Task` data must filter by the active location itself — the context processor does not do this for view logic, only for template globals (nav/selector).

**Models:** new domain models should extend `common.models.BaseModel` unless there's a specific reason not to (it gives audit fields for free).

## Settings

Split by environment under `settings/`, all importing from `settings/common.py`:
- `common.py` — shared base config. Don't edit for local-only needs.
- `local-development.py` — local dev (debug, console logging).
- `test.py` — in-memory sqlite, `MD5PasswordHasher` (fast, insecure — test-only), locmem email backend. Tests must run with this settings module; `local-development`'s Postgres backend will not work with the test DB assumptions.
- `stage.py`, `prod.py` — deployed environments.

Env vars are read from a root `.env` file via `django-environ` (see `settings/common.py`): `SECRET_KEY`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST`, `DATABASE_PORT` (the DB vars have local dev defaults; `SECRET_KEY` does not).

## Testing

Django's built-in test runner, split into multiple files per app by concern rather than one `tests.py`:
- `upkeep/tests_models.py`, `tests_views.py`, `tests_tasks.py`, `tests_grouping.py`, `tests_task_form.py`
- `common/tests_profiles.py`

When adding tests for a new concern, prefer a new `tests_<concern>.py` file over growing an existing one, matching this pattern.

## CI

`.github/workflows/homelab-build-push.yml` runs on every push: `ruff check .` and `pip-audit` must pass before the multi-arch (amd64+arm64) Docker image is built and pushed. `bandit` is available in `dev-requirements.txt` but is not currently part of CI.
