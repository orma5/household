# Household

A self-hosted Django app for tracking household items and their recurring maintenance.

## What it does

- **Locations** — physical areas (e.g. a house, an apartment) that scope everything else. The app works on a single "active location" at a time, switchable from the top bar.
- **Items** — physical assets (appliances, electronics, tools) with purchase date, warranty, manuals, and status (Active/Retired/Broken).
- **Tasks** — recurring maintenance tied to an item (e.g. "replace filter" every 90 days), with completion tracking and a snooze option.
- **Households (Accounts)** — items and locations belong to an Account (household), and users belong to an Account via their Profile, so a household's data can be shared across its members.

## Tech stack

- Backend: Python 3.13, Django 5.2
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

The app is containerized (see `Dockerfile`, Python 3.13 slim + Gunicorn). `.github/workflows/homelab-build-push.yml` lints and audits every push, then builds and pushes a multi-arch image to a private registry for self-hosted deployment.
