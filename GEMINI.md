# Household Management Application

## Project Overview

This is a Django-based application designed for household management. It allows users to track:
*   **Locations:** Physical areas (e.g., rooms, properties) where items are stored. The app functions on a "Single Active Location" paradigm, where the user selects a context (e.g., "Main House") and manages items/tasks specifically for that location.
*   **Items:** Physical assets (appliances, electronics, tools) with details like purchase date, warranty status, and manuals.
*   **Tasks:** Recurring maintenance tasks associated with items (e.g., changing filters, servicing).

The project uses **Django 5.2** on the backend and **HTMX** for frontend interactivity, creating a modern SPA-like feel without a heavy JavaScript framework. The frontend is designed to be fully responsive. It uses **PostgreSQL** as the database.

## Architecture

The project follows a standard Django project structure with a modular settings configuration:

### Key Directories

*   `core/`: Project-level configuration (ASGI/WSGI entry points, root URL config).
*   `common/`: Shared utilities and base classes (e.g., `BaseModel`).
*   `upkeep/`: The main application logic containing models for `Location`, `Item`, and `Task`.
*   `settings/`: Modular settings configuration.
    *   `common.py`: Base settings shared across environments.
    *   `local-development.py`: Settings for local development (debug mode, console logging).
    *   `prod.py`: Production settings.
*   `templates/`: HTML templates (Django + HTMX).
*   `static/`: Static assets (CSS, images).

### Key Technologies

*   **Backend:** Python 3.13, Django 5.2
*   **Frontend:** Django Templates, HTMX, CSS (Bootstrap 5)
*   **Database:** PostgreSQL (`psycopg` driver)
*   **Server:** Gunicorn (production), Django development server (local)
*   **Containerization:** Docker

## Functional Modules

### 1. Locations
*   **Active Location:** The application maintains an `active_location` in the user's session.
*   **Context Processor:** A global context processor (`upkeep/context_processors.py`) ensures the active location is available to all templates (e.g., for the top bar selector).
*   **Switching:** Users can switch their active location via the top bar. This persists across their session.
*   **Management:** Locations can be added, edited, or deleted via the Settings page.

### 2. Item Inventory
*   **Filtering:** The Item List view filters items to show *only* those belonging to the currently active location.
*   **Creation:** When creating a new item, it defaults to the currently active location.
*   **Status:** Items track status (Active, Retired, Broken) and details like warranty and purchase info.

### 3. Task Management
*   **Filtering:** Maintenance tasks are filtered to show only tasks linked to items in the active location.
*   **Grouping:** Tasks can be grouped by:
    *   **Item:** (Default) Grouped by the specific item they belong to.
    *   **Frequency:** Grouped by how often they occur (e.g., Monthly, Yearly).
    *   **None:** A flat list.
*   **Logic:** Tasks automatically calculate their `next_due_date` based on the `last_performed` date and `frequency`.

## Getting Started

### Prerequisites

*   Python 3.13+
*   PostgreSQL (or configured via Docker)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd household
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Setup:**
    Create a `.env` file in the project root. Refer to `settings/common.py` for required variables.
    
    **Required Variables:**
    *   `SECRET_KEY`
    *   `DATABASE_NAME`
    *   `DATABASE_USER`
    *   `DATABASE_PASSWORD`
    *   `DATABASE_HOST`
    *   `DATABASE_PORT`

5.  **Database Migration:**
    Set the environment variable to use the local settings and run migrations.
    ```bash
    export DJANGO_SETTINGS_MODULE=settings.local-development
    python manage.py migrate
    ```

6.  **Run the Development Server:**
    ```bash
    python manage.py runserver
    ```

## Development Workflow

### Key Commands

*   **Run Server:** `python manage.py runserver`
*   **Make Migrations:** `python manage.py makemigrations`
*   **Apply Migrations:** `python manage.py migrate`
*   **Run Tests:** `python manage.py test`
*   **Collect Static Files:** `python manage.py collectstatic`

### Conventions

*   **Models:** Defined in `upkeep/models.py`. Use `BaseModel` from `common.models` for shared fields if applicable.
*   **Settings:** Do not modify `settings/common.py` for local needs; use `settings/local-development.py` or a custom settings file.
*   **Frontend:** HTMX attributes are used in templates for dynamic interactions.

## Deployment

The application is containerized using Docker.

*   **Dockerfile:** Defines the build process (Python 3.13 slim, installs requirements, runs Gunicorn).
*   **CI/CD:** GitHub Actions (`.github/workflows/homelab-build-push.yml`) builds and pushes the Docker image to a private registry on push.