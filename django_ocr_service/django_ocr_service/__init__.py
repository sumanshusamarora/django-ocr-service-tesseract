"""
Setup config
"""
import ast
import os
import uuid

import yaml

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(THIS_DIR, "..", "..", "config")

for filename in os.listdir(CONFIG_DIR):
    if ".local" in filename:
        config_filename = filename
        break
    else:
        config_filename = filename


CONFIG_FILE = os.path.join(CONFIG_DIR, config_filename)

with open(CONFIG_FILE, "r") as configfile:
    config = yaml.safe_load(configfile)

# Secret Key
if not config.get("SECRET_KEY"):
    config["SECRET_KEY"] = uuid.uuid4().hex

# DEBUG
if not config.get("DEBUG"):
    if "insecure" in config["SECRET_KEY"]:
        config["DEBUG"] = True
    else:
        config["DEBUG"] = False
else:
    config.get("DEBUG")

if os.environ.get("AWS_ACCESS_KEY_ID"):
    config["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID")

if os.environ.get("AWS_SECRET_ACCESS_KEY"):
    config["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY")

if os.environ.get("AWS_STORAGE_BUCKET_NAME"):
    config["AWS_STORAGE_BUCKET_NAME"] = os.environ.get("AWS_STORAGE_BUCKET_NAME")

if os.environ.get("AWS_REGION"):
    config["AWS_REGION"] = os.environ.get("AWS_REGION")

if not config.get("ALLOWED_HOSTS"):
    config["ALLOWED_HOSTS"] = "*"

if not config.get("TOKEN_VALIDITY_IN_HOURS"):
    config["TOKEN_VALIDITY_IN_HOURS"] = 1
else:
    config["TOKEN_VALIDITY_IN_HOURS"] = int(config["TOKEN_VALIDITY_IN_HOURS"])

if not os.environ.get("DJANGO_SUPERUSER_USERNAME") and not config.get(
    "DJANGO_SUPERUSER_USERNAME"
):
    config["DJANGO_SUPERUSER_USERNAME"] = None

if not os.environ.get("DJANGO_SUPERUSER_EMAIL") and not config.get(
    "DJANGO_SUPERUSER_EMAIL"
):
    config["DJANGO_SUPERUSER_EMAIL"] = None

if not os.environ.get("DJANGO_SUPERUSER_PASSWORD") and not config.get(
    "DJANGO_SUPERUSER_PASSWORD"
):
    config["DJANGO_SUPERUSER_PASSWORD"] = None

# IMAGE PREPROCSSING
if not config.get("IMAGE_SIZE"):
    config["IMAGE_SIZE"] = 1800

if not config.get("BINARY_THRESHOLD"):
    config["BINARY_THRESHOLD"] = 180


# OCR
if not config.get("OCR_OEM"):
    config["OCR_OEM"] = 11

# DATABASES
if not config.get("DATABASES"):
    config["DATABASES"] = {
        "default": {"ENGINE": "django.db.backends.postgresql_psycopg2"}
    }

if os.environ.get("DB_NAME"):
    config["DATABASES"]["default"]["NAME"] = os.environ.get("DB_NAME")

if os.environ.get("DB_PASSWORD"):
    config["DATABASES"]["default"]["PASSWORD"] = os.environ.get("DB_PASSWORD")

if os.environ.get("DB_HOST"):
    config["DATABASES"]["default"]["HOST"] = os.environ.get("DB_HOST")

if os.environ.get("DB_USER"):
    config["DATABASES"]["default"]["USER"] = os.environ.get("DB_USER")

if os.environ.get("DB_PORT"):
    config["DATABASES"]["default"]["PORT"] = os.environ.get("DB_PORT")

if os.environ.get("DB_SCHEMA"):
    config["DATABASES"]["default"]["OPTIONS"] = {
        "options": f"-c search_path={os.environ.get('DB_SCHEMA')}"
    }


if os.environ.get("USE_THREADING_TO_UPLOAD_DELETE"):
    config["USE_THREADING_TO_UPLOAD_DELETE"] = os.environ.get(
        "USE_THREADING_TO_UPLOAD_DELETE"
    )

if not config.get("USE_THREADING_TO_UPLOAD_DELETE"):
    config["USE_THREADING_TO_UPLOAD_DELETE"] = True
