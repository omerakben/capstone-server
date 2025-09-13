# DEADLINE API (Backend)

[![Django](https://img.shields.io/badge/Django-5.1.x-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![DRF](https://img.shields.io/badge/DRF-REST%20Framework-ff1709?logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![Firebase](https://img.shields.io/badge/Firebase-Auth-FFCA28?logo=firebase&logoColor=black)](https://firebase.google.com/)

Unified developer command center API: secure workspace‑scoped management of environment variables, prompts, and documentation links.

## Overview

DEADLINE provides a structured backend for organizing developer knowledge and configuration artifacts across multiple workspaces and environments (e.g. Development / Staging / Production). The API is protected via Firebase-issued ID tokens validated server‑side with the Admin SDK.

## Core Features

- Workspace isolation with owner scoping
- Polymorphic artifact model (ENV_VAR | PROMPT | DOC_LINK)
- Environment‑aware uniqueness constraints
- Global search & environment‑filtered listing endpoints
- OpenAPI 3 schema + Swagger UI via drf-spectacular
- Strict Firebase authentication (no dev bypass in code)

## Tech Stack

- Django + DRF
- Firebase Admin Authentication
- SQLite (local) — can be swapped for Postgres in production
- python‑decouple for configuration
- drf-spectacular for schema + docs

## Repository Layout

```text
deadline_api/      # Django project settings & root URLConf
workspaces/        # Workspace & environment models + endpoints
artifacts/         # Artifact models (through validation & constraints)
auth_firebase/     # Firebase auth backend & permission logic
my-docs/           # Ancillary documentation (kept optional)
```

## Quick Start (Local Development)

```bash
git clone <repo-url>
cd capstone-server
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Visit:

- Swagger UI: <http://127.0.0.1:8000/api/docs/>
- OpenAPI JSON: <http://127.0.0.1:8000/api/schema/>

## Environment Variables

| Variable                  | Purpose                      | Required   | Notes                           |
| ------------------------- | ---------------------------- | ---------- | ------------------------------- |
| SECRET_KEY                | Django cryptographic key     | Yes (prod) | Auto default only for local dev |
| DEBUG                     | Enable Django debug mode     | No         | Must be `False` in production   |
| ALLOWED_HOSTS             | Comma list of hostnames      | Yes (prod) | `localhost,127.0.0.1` for dev   |
| FIREBASE_CREDENTIALS_FILE | Path to service account JSON | Yes (prod) | Preferred credential method     |
| FIREBASE_*                | Individual Firebase fields   | Alt        | Fallback if file not used       |

The application logs warnings (not prints) if Firebase credentials are absent while `DEBUG=True`.

## Authentication Flow

Clients obtain Firebase ID tokens via the frontend Firebase SDK and send them as `Authorization: Bearer <token>` headers. The backend:

1. Verifies the token using Firebase Admin
2. Attaches a lightweight user object with `uid`
3. Applies workspace ownership filtering & permissions

## Key Models

Workspace:

- `name`, `description`, `owner_uid`

Artifact:

- `workspace` FK
- `kind` choice (ENV_VAR, PROMPT, DOC_LINK)
- Uniqueness constraints on `(workspace, kind, key)` and `(workspace, kind, title)` where fields are applicable
- Type‑specific validation in serializer / model clean

## API Surface (Representative)

```http
GET /api/v1/workspaces/
POST /api/v1/workspaces/
GET /api/v1/workspaces/{id}/
GET /api/v1/workspaces/{id}/artifacts/?kind=ENV_VAR
POST /api/v1/workspaces/{id}/artifacts/
GET /api/v1/search/artifacts/?q=...
```

All endpoints (except potential future health-check) require valid Firebase authentication.

## Running Tests

The project contains a comprehensive Django test suite. Run tests with:

```bash
python manage.py test -v 2
```

## Production Hardening Checklist

- Set `DEBUG=False`
- Provide strong `SECRET_KEY`
- Configure `ALLOWED_HOSTS`
- Supply Firebase service account JSON via `FIREBASE_CREDENTIALS_FILE`
- Enforce HTTPS at the reverse proxy (e.g. Nginx / Cloud Load Balancer)
- Add database (PostgreSQL) & run migrations
- Enable structured logging (configure LOGGING dict)
- Add monitoring (health endpoint + metrics)

## Deployment (Example Outline)

1. Build image (containerize Django app)
2. Run migrations on release
3. Start application with WSGI server (gunicorn / uwsgi)
4. Serve static files via CDN / reverse proxy
5. Apply Django checks: `python manage.py check --deploy`

Example gunicorn invocation:

```bash
gunicorn deadline_api.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --timeout 60
```

## Logging

All runtime warnings (Firebase init, etc.) use the standard logging API. Configure `LOGGING` in `deadline_api/settings.py` or via an environment‑specific module. Example minimal config:

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
```

## Security Notes

- No plaintext secrets should be committed (sample `.env.example` provided)
- All authentication enforced server‑side; no dev bypass logic present
- ENV_VAR values are masked in standard responses; a dedicated action returns the unmasked value for owners

## Data Model Highlights

- Workspace ↔ EnvironmentType Many‑to‑Many via `WorkspaceEnvironment` join
- Artifact ↔ Tag Many‑to‑Many via explicit through model `ArtifactTag`
- Query performance: `select_related` / `prefetch_related` used in viewsets

## Roadmap (High-Level)

| Area          | Next Targets                                        |
| ------------- | --------------------------------------------------- |
| Artifacts     | Bulk import/export, masking strategy                |
| Search        | Cross-field partial + relevance ranking             |
| Auth          | Token revocation cache / short-lived session tokens |
| Observability | Structured audit log for artifact changes           |

## License

Add your chosen license (MIT, Apache-2.0, etc.).

## Maintainers

Provide contact or team identity here.

---

"DEADLINE API" – Foundational layer for a unified developer operations hub.
