"""
Django settings for deadline_api project.

DEADLINE - Developer Command Center
Unified hub for managing environment variables, prompts, and documentation links.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

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

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
    cast=lambda x: [item.strip() for item in x.split(",")],
)

# CORS settings for local development with React frontend
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

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
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
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

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework configuration
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        # "auth_firebase.authentication.FirebaseAuthentication",  # TODO: Enable after creating Firebase auth
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
}


# Firebase configuration
def get_firebase_private_key():
    """Get Firebase private key with proper line ending handling."""
    key = config("FIREBASE_PRIVATE_KEY", default="", cast=str)
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

# Local development settings
if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

    # Show debug toolbar for localhost
    INTERNAL_IPS = ["127.0.0.1", "localhost"]

    # Firebase mock for local development
    USE_FIREBASE_MOCK = config("USE_FIREBASE_MOCK", default=True, cast=bool)
