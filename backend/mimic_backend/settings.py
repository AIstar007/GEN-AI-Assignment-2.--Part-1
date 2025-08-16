import os
from pathlib import Path
from dotenv import load_dotenv   # ✅ to load .env

# -------------------- BASE DIR -------------------- #
BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------- ENV -------------------- #
load_dotenv(BASE_DIR / ".env")

# -------------------- SECURITY -------------------- #
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

# -------------------- APPS -------------------- #
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",       # ✅ DRF
    "core",                 # ✅ your app
    "django_extensions",    # ✅ so shell_plus etc. work
    'import_export',

    # your app
    'main',
]

# -------------------- MIDDLEWARE -------------------- #
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# -------------------- URLS -------------------- #
ROOT_URLCONF = "mimic_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "mimic_backend.wsgi.application"

# -------------------- DATABASE -------------------- #
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# -------------------- PASSWORDS -------------------- #
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -------------------- LANGUAGE / TIMEZONE -------------------- #
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# -------------------- STATIC -------------------- #
STATIC_URL = "static/"

# -------------------- DEFAULT PK -------------------- #
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------------------- CUSTOM -------------------- #
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SERVICE_NOW_EXCEL = os.environ.get("SERVICE_NOW_EXCEL", "servicenow_requests.xlsx")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000/api")