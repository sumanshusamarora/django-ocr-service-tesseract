"""
Django settings for django_ocr_service project.

Generated by 'django-admin startproject' using Django 3.2.4.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
from datetime import timedelta
import logging.config
import os

from pathlib import Path
import yaml

from . import config

urllib3_logger = logging.getLogger("urllib3")
urllib3_logger.setLevel(logging.CRITICAL)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

with open(os.path.join(BASE_DIR, "logging.yaml"), "r") as logginginput:
    logging_config = yaml.safe_load(logginginput)
    logging.config.dictConfig(logging_config)


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config["SECRET_KEY"]

# CLOUD SETTINGS
os.environ["AWS_ACCESS_KEY_ID"] = config.get("AWS_ACCESS_KEY_ID")
os.environ["AWS_SECRET_ACCESS_KEY"] = config.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = config.get("AWS_STORAGE_BUCKET_NAME")
CLOUD_STORAGE_BUCKET_NAME = config.get("AWS_STORAGE_BUCKET_NAME")
os.environ["AWS_STORAGE_BUCKET_NAME"] = AWS_STORAGE_BUCKET_NAME
AWS_REGION = config.get("AWS_REGION")
os.environ["AWS_REGION"] = AWS_REGION


# SUPERUSER ENV VARIABLES
os.environ["DJANGO_SUPERUSER_USERNAME"] = config.get("DJANGO_SUPERUSER_USERNAME")
os.environ["DJANGO_SUPERUSER_EMAIL"] = config.get("DJANGO_SUPERUSER_EMAIL")
os.environ["DJANGO_SUPERUSER_PASSWORD"] = config.get("DJANGO_SUPERUSER_PASSWORD")

# IMAGE PREPROCESSING
IMAGE_SIZE = config["IMAGE_SIZE"]
BINARY_THRESHOLD = config["BINARY_THRESHOLD"]
LOCAL_FILES_SAVE_DIR = config.get("LOCAL_FILES_SAVE_DIR")
if not LOCAL_FILES_SAVE_DIR:
    LOCAL_FILES_SAVE_DIR = "/tmp/ocr_inputs"

# OCR
OCR_OEM = config.get("OCR_OEM")
OCR_PSM = config.get("OCR_PSM")
OCR_TESSDATA_DIR = config.get("OCR_TESSDATA_DIR")
OCR_LANGUAGE = config.get("OCR_LANGUAGE")
SAVE_IMAGES_TO_CLOUD = config.get("SAVE_IMAGES_TO_CLOUD")
DROP_INPUT_FILE_POST_PROCESSING = config.get("DROP_INPUT_FILE_POST_PROCESSING")
USE_ASYNC_TO_UPLOAD_FILES = config.get("USE_ASYNC_TO_UPLOAD_FILES")

# REST
TOKEN_VALIDITY_IN_HOURS = config["TOKEN_VALIDITY_IN_HOURS"]
EXPIRING_TOKEN_DURATION = timedelta(hours=TOKEN_VALIDITY_IN_HOURS)

# OTHER DJANGO
DEBUG = config["DEBUG"]
ALLOWED_HOSTS = config["ALLOWED_HOSTS"].split(",")

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "ocr.apps.OcrConfig",
    "rest_framework",
    "django_expiring_token",
    "storages",
    "django_apscheduler",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "django_expiring_token.authentication.ExpiringTokenAuthentication",
    ],
}

ROOT_URLCONF = "django_ocr_service.urls"

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

WSGI_APPLICATION = "django_ocr_service.wsgi.application"

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = config["DATABASES"]


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# STORAGE BACKEND RELATED
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]
STATIC_URL = "/static/"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DEFAULT_FILE_STORAGE = "django_ocr_service.custom_storage.CloudMediaStorage"
STATICFILES_STORAGE = "django_ocr_service.custom_storage.CloudStaticStorage"

ALLOWED_STORAGES = ["s3"]

APSCHEDULER_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
APSCHEDULER_RUN_NOW_TIMEOUT = 90

