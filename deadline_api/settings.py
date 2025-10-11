"""
Django settings for deadline_api project.

DEADLINE - Developer Command Center
Unified hub for managing environment variables, prompts, and documentation links.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import os
from pathlib import Path

from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-5s4zka&zl7^8+#l7f2&#vx$xwyq1wo&q6kdt!t7j%l(@f*c6#s",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=True, cast=bool)

# Demo mode for public deployment without Firebase
DEMO_MODE = config("DEMO_MODE", default=False, cast=bool)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1,testserver",
    cast=lambda x: [item.strip() for item in x.split(",")],
)

# CORS settings for local development and production
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Common alternate dev ports
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
]

# Add Vercel domain if configured
VERCEL_FRONTEND_URL = config("VERCEL_FRONTEND_URL", default="")
if VERCEL_FRONTEND_URL:
    CORS_ALLOWED_ORIGINS.append(VERCEL_FRONTEND_URL)

CORS_ALLOW_CREDENTIALS = True


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "django_extensions",
    # Local apps
    "workspaces",
    "artifacts",
    "auth_firebase",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Static files for production
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "auth_firebase.demo_middleware.DemoModeAuthenticationMiddleware",  # Demo mode support
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "deadline_api.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "deadline_api.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

import dj_database_url

DATABASES = {
    "default": dj_database_url.config(
        default="sqlite:///" + str(BASE_DIR / "db.sqlite3"),
        conn_max_age=600,
        conn_health_checks=True,
    )
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise configuration for static files in production
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework configuration
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "auth_firebase.authentication.FirebaseAuthentication",
        "rest_framework.authentication.SessionAuthentication",  # Keep for admin interface
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# drf-spectacular settings for API documentation
SPECTACULAR_SETTINGS = {
    "TITLE": "DEADLINE API",
    "DESCRIPTION": "Developer Command Center - Unified hub for managing environment variables, prompts, and documentation links",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    # Suppress schema-related warnings in local development checks
    "DISABLE_ERRORS_AND_WARNINGS": True,
}


# Firebase configuration
def get_firebase_private_key():
    """Get Firebase private key with proper line ending handling."""
    key = config("FIREBASE_PRIVATE_KEY", default="")
    return key.replace("\\n", "\n") if key else ""


FIREBASE_CONFIG = {
    "type": config("FIREBASE_TYPE", default="service_account"),
    "project_id": config("FIREBASE_PROJECT_ID", default=""),
    "private_key_id": config("FIREBASE_PRIVATE_KEY_ID", default=""),
    "private_key": get_firebase_private_key(),
    "client_email": config("FIREBASE_CLIENT_EMAIL", default=""),
    "client_id": config("FIREBASE_CLIENT_ID", default=""),
    "auth_uri": config(
        "FIREBASE_AUTH_URI", default="https://accounts.google.com/o/oauth2/auth"
    ),
    "token_uri": config(
        "FIREBASE_TOKEN_URI", default="https://oauth2.googleapis.com/token"
    ),
    "auth_provider_x509_cert_url": config(
        "FIREBASE_AUTH_PROVIDER_X509_CERT_URL",
        default="https://www.googleapis.com/oauth2/v1/certs",
    ),
    "client_x509_cert_url": config("FIREBASE_CLIENT_X509_CERT_URL", default=""),
}

FIREBASE_CREDENTIALS_FILE = config("FIREBASE_CREDENTIALS_FILE", default="")

"""Firebase Admin SDK Initialization.

Attempts credential initialization using (in order):
1. Explicit service account JSON file path via FIREBASE_CREDENTIALS_FILE
2. Individual FIREBASE_* environment variables forming a credentials dict

All warnings are routed through Python's logging module (no print statements) so
they can be managed by the deployment logging configuration.
"""

import logging

logger = logging.getLogger(__name__)

# Firebase initialization - skip entirely in demo mode
if not DEMO_MODE:
    try:  # Initialize Firebase Admin SDK
        import firebase_admin
        from firebase_admin import credentials

        if len(firebase_admin._apps) == 0:  # pylint: disable=protected-access
            cred = None

            # Priority 1: Check for runtime-generated credentials file (Railway production)
            runtime_creds_path = "/tmp/firebase-credentials.json"
            if os.path.exists(runtime_creds_path):
                cred = credentials.Certificate(runtime_creds_path)
                logger.info("Using Firebase credentials from %s", runtime_creds_path)
            # Priority 2: Check for explicitly configured credentials file (local dev)
            elif FIREBASE_CREDENTIALS_FILE and os.path.exists(FIREBASE_CREDENTIALS_FILE):
                cred = credentials.Certificate(FIREBASE_CREDENTIALS_FILE)
                logger.info("Using Firebase credentials from %s", FIREBASE_CREDENTIALS_FILE)
            # Priority 3: Try environment variables (fallback, may have formatting issues)
            elif FIREBASE_CONFIG.get("project_id"):
                cred = credentials.Certificate(FIREBASE_CONFIG)
                logger.info("Using Firebase credentials from environment variables")

            if cred is not None:
                firebase_admin.initialize_app(cred)
            else:
                if DEBUG:
                    logger.warning(
                        "Firebase credentials not configured. Set FIREBASE_CREDENTIALS_FILE or FIREBASE_* env vars."
                    )
    except ImportError:
        if not DEBUG:
            raise
        logger.warning(
            "firebase_admin not installed; authentication will fail outside development."
        )
    except (ValueError, KeyError) as e:
        if not DEBUG:
            raise
        logger.warning("Firebase initialization failed (development mode): %s", e)
else:
    logger.info("Demo mode enabled - skipping Firebase initialization")

# Local development settings
if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    INTERNAL_IPS = ["127.0.0.1", "localhost"]
    # Dev bypass removed – real Firebase auth only
