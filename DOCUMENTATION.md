# DEADLINE API Documentation

## 1. Project Overview

**DEADLINE** is a web-based command center for developers that provides a unified platform to manage environment variables, code prompts, and documentation links across multiple development environments (Development, Staging, Production).

The core philosophy of DEADLINE is to centralize and streamline developer workflows by providing a single source of truth for critical project artifacts, reducing configuration fragmentation, and improving team collaboration.

### 1.1. Key Features

- **Workspace Management**: Organize your projects into workspaces. Each workspace acts as a container for your artifacts.
- **Polymorphic Artifacts**: Store different types of developer artifacts in a single, unified system:
  - **Environment Variables (ENV_VAR)**: Manage sensitive keys and configuration variables with built-in value masking.
  - **Code/AI Prompts (PROMPT)**: Save and reuse useful code snippets or AI prompts.
  - **Documentation Links (DOC_LINK)**: Keep a centralized repository of important documentation links.
- **Environment-Specific Artifacts**: Associate artifacts with specific environments (DEV, STAGING, PROD) to ensure proper configuration in different deployment stages.
- **Secure Authentication**: User authentication is handled through Firebase, with JWT-based authorization for all API endpoints.
- **RESTful API**: A comprehensive RESTful API for programmatic access to all features.
- **Bulk Operations**: Efficiently manage artifacts with bulk create and delete operations.

### 1.2. Technology Stack

- **Backend**: Django 5.1.x & Django REST Framework 3.16+
- **Authentication**: Firebase Admin SDK (JWT validation)
- **Database**: SQLite (for local development), PostgreSQL (for production)
- **API Documentation**: `drf-spectacular` for Swagger UI generation.

## 2. Architecture

### 2.1. Data Models

The application revolves around two primary models: `Workspace` and `Artifact`.

#### 2.1.1. Workspace Model

A `Workspace` is a container for artifacts, owned by a user.

| Field        | Type            | Description                                          |
| ------------ | --------------- | ---------------------------------------------------- |
| `id`         | `AutoField`     | Primary key.                                         |
| `name`       | `CharField`     | The name of the workspace.                           |
| `owner_uid`  | `CharField`     | The Firebase UID of the user who owns the workspace. |
| `created_at` | `DateTimeField` | Timestamp of when the workspace was created.         |
| `updated_at` | `DateTimeField` | Timestamp of the last update.                        |

#### 2.1.2. Artifact Model

The `Artifact` model is polymorphic and can represent one of three types of artifacts, determined by the `kind` field.

| Field         | Type            | Description                                                                                      |
| ------------- | --------------- | ------------------------------------------------------------------------------------------------ |
| `id`          | `AutoField`     | Primary key.                                                                                     |
| `workspace`   | `ForeignKey`    | A reference to the `Workspace` this artifact belongs to.                                         |
| `kind`        | `CharField`     | The type of artifact. Can be `ENV_VAR`, `PROMPT`, or `DOC_LINK`.                                 |
| `environment` | `CharField`     | The environment the artifact belongs to. Can be `DEV`, `STAGING`, or `PROD`.                     |
| `key`         | `CharField`     | **(ENV_VAR only)** The key of the environment variable.                                          |
| `value`       | `TextField`     | **(ENV_VAR only)** The value of the environment variable. This value is masked in API responses. |
| `title`       | `CharField`     | **(PROMPT, DOC_LINK only)** The title of the prompt or link.                                     |
| `content`     | `TextField`     | **(PROMPT only)** The content of the code/AI prompt (supports Markdown).                         |
| `url`         | `URLField`      | **(DOC_LINK only)** The URL of the documentation link.                                           |
| `notes`       | `TextField`     | Optional notes for any artifact type.                                                            |
| `metadata`    | `JSONField`     | Additional metadata for the artifact (e.g., labels for `DOC_LINK`).                              |
| `created_at`  | `DateTimeField` | Timestamp of when the artifact was created.                                                      |
| `updated_at`  | `DateTimeField` | Timestamp of the last update.                                                                    |

### 2.2. API Design

The API is designed to be RESTful and is organized around the concepts of workspaces and artifacts.

- **Authentication**: All endpoints (except for the API documentation schema) require authentication. The client must include a valid Firebase ID token in the `Authorization` header with the `Bearer` scheme.
- **Ownership**: All resources are scoped to the authenticated user. A user can only access workspaces and artifacts that they own.

## 3. API Endpoints

The base URL for the API is `/api/v1/`.

### 3.1. Workspaces

- **Endpoint**: `/api/v1/workspaces/`
- **Description**: Provides full CRUD functionality for workspaces.

#### GET `/api/v1/workspaces/`

- **Description**: Retrieve a list of all workspaces owned by the authenticated user.
- **Successful Response (`200 OK`)**:

  ```json
  [
    {
      "id": 1,
      "name": "My First Workspace",
      "owner_uid": "some-firebase-uid",
      "created_at": "2025-09-06T12:00:00Z",
      "updated_at": "2025-09-06T12:00:00Z"
    }
  ]
  ```

#### POST `/api/v1/workspaces/`

- **Description**: Create a new workspace.
- **Request Body**:

  ```json
  {
    "name": "New Awesome Project"
  }
  ```

- **Successful Response (`201 CREATED`)**:

  ```json
  {
    "id": 2,
    "name": "New Awesome Project",
    "owner_uid": "some-firebase-uid",
    "created_at": "2025-09-06T13:00:00Z",
    "updated_at": "2025-09-06T13:00:00Z"
  }
  ```

---

### 3.2. Artifacts

- **Endpoint**: `/api/v1/workspaces/{workspace_id}/artifacts/`
- **Description**: Provides full CRUD functionality for artifacts within a specific workspace.

#### GET `/api/v1/workspaces/{workspace_id}/artifacts/`

- **Description**: Retrieve a list of all artifacts within a specific workspace.
- **Query Parameters**:
  - `kind`: Filter by artifact type (`ENV_VAR`, `PROMPT`, `DOC_LINK`).
  - `environment`: Filter by environment (`DEV`, `STAGING`, `PROD`).
  - `search`: Search term to filter artifacts by key, title, content, notes, or url.
- **Successful Response (`200 OK`)**:

  ```json
  [
    {
        "id": 1,
        "workspace": 1,
        "workspace_name": "My First Workspace",
        "kind": "ENV_VAR",
        "environment": "DEV",
        "created_at": "2025-09-06T12:05:00Z",
        "updated_at": "2025-09-06T12:05:00Z",
        "notes": "Database connection string",
        "key": "DATABASE_URL",
        "value": "••••••",
        "value_masked": true,
        "metadata": {}
    },
    {
        "id": 2,
        "workspace": 1,
        "workspace_name": "My First Workspace",
        "kind": "PROMPT",
        "environment": "DEV",
        "created_at": "2025-09-06T12:10:00Z",
        "updated_at": "2025-09-06T12:10:00Z",
        "notes": "A prompt for generating Django models.",
        "title": "Django Model Prompt",
        "content": "Generate a Django model for a blog post with fields for title, content, author, and publication date.",
        "metadata": {}
    }
  ]
  ```

#### POST `/api/v1/workspaces/{workspace_id}/artifacts/`

- **Description**: Create a new artifact within a workspace.
- **Request Body (for `ENV_VAR`)**:

  ```json
  {
    "kind": "ENV_VAR",
    "environment": "PROD",
    "key": "API_SECRET_KEY",
    "value": "a-very-secret-value"
  }
  ```

- **Request Body (for `PROMPT`)**:

  ```json
  {
    "kind": "PROMPT",
    "environment": "DEV",
    "title": "React Component Prompt",
    "content": "Create a React functional component for a button with customizable text and onClick handler."
  }
  ```

- **Successful Response (`201 CREATED`)**: The newly created artifact object.

---

### 3.3. Global Search and Views

#### GET `/api/v1/search/artifacts/`

- **Description**: Globally search across all artifacts owned by the user.
- **Query Parameters**:
  - `q`: The search term.
  - `kind`, `environment`, `workspace`: Optional filters.
- **Successful Response (`200 OK`)**: A list of matching artifact objects.

#### GET `/api/v1/docs/`

- **Description**: Get a list of all `DOC_LINK` artifacts across all workspaces for the user.
- **Successful Response (`200 OK`)**: A list of `DOC_LINK` artifact objects.

> Note: There is no dedicated global prompts endpoint; prompts are included in search results.

## 4. Setup and Installation

1. **Clone the repository**:

    ```bash
    git clone <repository-url>
    cd capstone-server
    ```

2. **Create and activate a virtual environment**:

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4. **Configure environment variables**:
    - Copy `.env.example` to `.env`.
    - Set the `SECRET_KEY` in your `.env` file.
    - For Firebase integration, obtain a service account JSON and set `FIREBASE_CREDENTIALS_FILE` to its path (or provide the `FIREBASE_*` variables: project id, private key id, private key, client email, client id, etc.).
5. **Run database migrations**:

    ```bash
    python manage.py migrate
    ```

6. **Run the development server**:

    ```bash
    python manage.py runserver
    ```

## 5. Deployment

For production deployment, it is recommended to use a production-ready web server like Gunicorn and a database like PostgreSQL.

1. **Configure your production environment variables** in your hosting provider's settings.
2. **Use a production-grade database** (e.g., PostgreSQL, MySQL). Update the `DATABASES` setting in `deadline_api/settings.py` accordingly, preferably using `dj-database-url`.
3. **Run Gunicorn** to serve the application:

    ```bash
    gunicorn deadline_api.wsgi:application
    ```

4. **Configure a reverse proxy** like Nginx to sit in front of Gunicorn, handle HTTPS, and serve static files.
