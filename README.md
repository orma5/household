# Household

A self-hosted Django app for tracking household items and their recurring maintenance.

## What it does

- **Locations** — physical areas (e.g. a house, an apartment) that scope everything else. The app works on a single "active location" at a time, switchable from the top bar.
- **Items** — physical assets (appliances, electronics, tools) with purchase date, warranty, manuals, and status (Active/Retired/Broken).
- **Tasks** — recurring maintenance tied to an item (e.g. "replace filter" every 90 days), with completion tracking and a snooze option.
- **Households (Accounts)** — items and locations belong to an Account (household), and users belong to an Account via their Profile, so a household's data can be shared across its members.

## Tech stack

- Backend: Python 3.13, Django 6.1
- Frontend: Django templates + HTMX, Bootstrap 5 (no JS framework, no SPA)
- Database: PostgreSQL (`psycopg`)
- Server: Gunicorn (prod), Django dev server (local)
- Containerized with Docker; CI builds a multi-arch (amd64/arm64) image for self-hosted deployment

## Getting started

**Prerequisites:** Python 3.13+, PostgreSQL (or use the Dockerfile).

```bash
git clone <repository_url>
cd household

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file in the project root with:

```
SECRET_KEY=<your-secret-key>
DATABASE_NAME=<db-name>
DATABASE_USER=<db-user>
DATABASE_PASSWORD=<db-password>
DATABASE_HOST=<db-host>
DATABASE_PORT=<db-port>
```

Then set up the database and run the app:

```bash
DJANGO_SETTINGS_MODULE=settings.local-development python manage.py migrate
python manage.py runserver
```

## Development

```bash
python manage.py runserver          # run dev server
python manage.py makemigrations     # create migrations
python manage.py migrate            # apply migrations

DJANGO_SETTINGS_MODULE=settings.test python manage.py test   # run tests

ruff check .                        # lint
pip-audit                           # dependency vulnerability check
```

For working conventions and architecture notes aimed at AI coding agents, see [`CLAUDE.md`](./CLAUDE.md) — it's kept accurate and is a good place to start even as a human contributor.

## Deployment

The app is containerized (see `Dockerfile`, Python 3.13 slim + Gunicorn). `.github/workflows/homelab-build-push.yml` lints, tests and audits every push, then builds and pushes a multi-arch image to a private registry for self-hosted deployment.

### What the container expects

**Runs as an unprivileged user** (`appuser`, uid 10001), so any directory it writes to must be writable by that uid.

**Two volumes**, both of which the container writes to:

| Mount | Holds | Notes |
|---|---|---|
| `/app/assets` | collected static files | `STATIC_ROOT`. Share with the reverse proxy if it serves `/static/` itself. |
| `/app/media` | user uploads (receipts, profile pictures) | `MEDIA_ROOT`. Without it, uploads are lost on every redeploy. |

`collectstatic` runs **on every container start**, not only at build. When `/app/assets` is a volume, the volume is mounted over the image's copy of that directory, and Docker only seeds a volume from the image when the volume is empty — so a build-time-only collect would leave an existing volume frozen on its old contents.

A volume created fresh inherits `appuser` ownership from the image. A volume that predates the switch to a non-privileged user is still owned by root and must be handed over once, or the container will fail to start:

```bash
docker run --rm -v <volume_name>:/v alpine chown -R 10001:10001 /v
```

**Environment:** `SECRET_KEY` and the `DATABASE_*` vars are required; `DJANGO_SETTINGS_MODULE` defaults to `settings.prod` in the image. `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` and `MEDIA_ROOT` are optional overrides.

**Uploads are served by the app**, not the reverse proxy — `/media/` is access-controlled per account, so don't add a proxy rule that bypasses it. Migrations are not run automatically:

```bash
docker exec <container> python manage.py migrate
```
