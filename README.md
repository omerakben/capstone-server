# DEADLINE - Developer Command Center

[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![DRF](https://img.shields.io/badge/DRF-3.16+-red.svg)](https://www.django-rest-framework.org/)
[![Firebase](https://img.shields.io/badge/Firebase-Admin-orange.svg)](https://firebase.google.com/)

A unified web-based command center for developers to manage environment variables, code prompts, and documentation links across different environments (Dev/Staging/Production).

## 🎯 Project Overview

**DEADLINE** consolidates critical developer workflow elements into a single, organized hub, addressing configuration fragmentation by providing a unified platform with environment-aware artifact management.

### Key Features

- **Unified Hub**: Single source of truth for environment configs, prompts, and documentation
- **Environment Awareness**: First-class support for Dev/Staging/Production separation
- **Security First**: Masked secrets, Firebase authentication, and safe export/import
- **Developer Focused**: Built by developers, for developers' actual workflow needs

## 🏗️ Architecture

### Technology Stack

- **Backend**: Django 5.2 + Django REST Framework
- **Authentication**: Firebase Admin SDK with JWT token validation
- **Database**: SQLite (local development)
- **API Documentation**: drf-spectacular (Swagger UI)
- **Environment Management**: python-decouple

### Project Structure

```
capstone-server/
├── deadline_api/          # Main Django project
│   ├── settings.py        # Django configuration
│   ├── urls.py           # URL routing
│   └── wsgi.py           # WSGI application
├── workspaces/            # Workspace management app
├── artifacts/             # Artifact management app (ENV_VAR, PROMPT, DOC_LINK)
├── auth_firebase/         # Firebase authentication app
├── my-docs/              # Project documentation and assets
├── .github/              # GitHub Copilot instructions
├── manage.py             # Django management script
├── requirements.txt      # Python dependencies
├── .env.example         # Environment configuration template
└── .gitignore           # Git ignore rules
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd capstone-server
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration (optional for local development)
   ```

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Start development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - API: http://127.0.0.1:8000/
   - Admin: http://127.0.0.1:8000/admin/
   - API Documentation: http://127.0.0.1:8000/api/docs/

## 📚 API Documentation

The project uses drf-spectacular for automated API documentation:

- **Interactive Swagger UI**: `/api/docs/`
- **OpenAPI Schema**: `/api/schema/`

### API Endpoints (Planned)

```
/api/v1/workspaces/     # Workspace management
/api/v1/artifacts/      # Artifact CRUD operations
/api/v1/auth/          # Firebase authentication
```

## 🔧 Development

### Project Status

✅ **Completed**: Initial Django setup with proper structure
🔄 **In Progress**: Model implementation and API endpoints
📋 **Planned**: Firebase authentication integration

### Development Commands

```bash
# Run development server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Django shell
python manage.py shell

# Check project configuration
python manage.py check
```

### Environment Configuration

Key environment variables (see `.env.example`):

- `SECRET_KEY`: Django secret key
- `DEBUG`: Enable/disable debug mode
- `ALLOWED_HOSTS`: Allowed host names
- `FIREBASE_*`: Firebase configuration (optional for local dev)

## 🔐 Authentication

The project uses Firebase Authentication for secure user management:

- JWT token-based authentication
- Row-level security with Firebase UID
- Mock authentication support for local development

## 📁 Data Models (Planned)

### Workspace
- User-owned containers for organizing artifacts
- Environment categorization (Dev/Staging/Prod)

### Artifacts (Polymorphic)
- **ENV_VAR**: Environment variables with masked values
- **PROMPT**: Code/AI prompts with markdown support
- **DOC_LINK**: Documentation links with labels

## 🎯 Development Roadmap

See `my-docs/server-TODO.md` for detailed implementation checklist.

## 📋 Contributing

This project follows Django and DRF best practices:

- Use Django's built-in admin for data management
- Follow RESTful API design patterns
- Implement proper authentication and permissions
- Write comprehensive tests

## 📄 License

[Add license information]

## 🤝 Support

For questions and support, please refer to the project documentation in the `my-docs/` directory.

---

**DEADLINE** - Unifying developer workflows, one artifact at a time.
