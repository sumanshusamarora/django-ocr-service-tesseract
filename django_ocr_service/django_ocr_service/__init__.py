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

# DEBUG
if os.environ.get("DEBUG"):
    config["DEBUG"] = ast.literal_eval(os.environ.get("DEBUG"))
if config.get("DEBUG") is None:
    if "insecure" in config["SECRET_KEY"]:
        config["DEBUG"] = True
    else:
        config["DEBUG"] = False

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

if os.environ.get("TOKEN_VALIDITY_IN_HOURS"):
    config["TOKEN_VALIDITY_IN_HOURS"] = int(os.environ.get("TOKEN_VALIDITY_IN_HOURS"))
if not config.get("TOKEN_VALIDITY_IN_HOURS"):
    config["TOKEN_VALIDITY_IN_HOURS"] = 1

if os.environ.get("DJANGO_SUPERUSER_USERNAME"):
    config["DJANGO_SUPERUSER_USERNAME"] = os.environ.get("DJANGO_SUPERUSER_USERNAME")
else:
    config["DJANGO_SUPERUSER_USERNAME"] = config.get("DJANGO_SUPERUSER_USERNAME")

if os.environ.get("DJANGO_SUPERUSER_EMAIL"):
    config["DJANGO_SUPERUSER_EMAIL"] = os.environ.get("DJANGO_SUPERUSER_EMAIL")
else:
    config["DJANGO_SUPERUSER_EMAIL"] = config.get("DJANGO_SUPERUSER_EMAIL")

if os.environ.get("DJANGO_SUPERUSER_PASSWORD"):
    config["DJANGO_SUPERUSER_PASSWORD"] = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
else:
    config["DJANGO_SUPERUSER_PASSWORD"] = config.get("DJANGO_SUPERUSER_PASSWORD")

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

# USE_ASYNC_FOR_SPEED
if os.environ.get("USE_ASYNC_FOR_SPEED"):
    config["USE_ASYNC_FOR_SPEED"] = ast.literal_eval(
        os.environ.get("USE_ASYNC_FOR_SPEED")
    )
if config.get("USE_ASYNC_FOR_SPEED") is None:
    config["USE_ASYNC_FOR_SPEED"] = True

# DROP_INPUT_FILE_POST_PROCESSING
if os.environ.get("DROP_INPUT_FILE_POST_PROCESSING"):
    config["DROP_INPUT_FILE_POST_PROCESSING"] = ast.literal_eval(
        os.environ.get("DROP_INPUT_FILE_POST_PROCESSING")
    )
if config.get("DROP_INPUT_FILE_POST_PROCESSING") is None:
    config["DROP_INPUT_FILE_POST_PROCESSING"] = True

if config.get("SAVE_IMAGES_TO_CLOUD") is None:
    config["SAVE_IMAGES_TO_CLOUD"] = True


# MONGO
if os.environ.get("MONGO_HOST"):
    config["MONGO_HOST"] = os.environ.get("MONGO_HOST")

config["MONGO_HOST"] = "mongodb://" + config["MONGO_HOST"].replace("mongodb://", "")

if os.environ.get("MONGO_PORT"):
    config["MONGO_PORT"] = int(os.environ.get("MONGO_PORT"))

if not config.get("MONGO_PORT"):
    config["MONGO_PORT"] = 27017


if os.environ.get("MONGO_USER"):
    config["MONGO_USER"] = os.environ.get("MONGO_USER")

if os.environ.get("MONGO_PASSWORD"):
    config["MONGO_PASSWORD"] = os.environ.get("MONGO_PASSWORD")

# Secret Key
if os.environ.get("SECRET_KEY"):
    config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

if not config.get("SECRET_KEY"):
    config["SECRET_KEY"] = uuid.uuid4().hex

if os.environ.get("DELETE_OLD_IMAGES_DAYS"):
    config["DELETE_OLD_IMAGES_DAYS"] = int(os.environ.get("DELETE_OLD_IMAGES_DAYS"))

if not config.get("DELETE_OLD_IMAGES_DAYS"):
    config["DELETE_OLD_IMAGES_DAYS"] = 2


if os.environ.get("LOCAL_FILES_SAVE_DIR"):
    config["LOCAL_FILES_SAVE_DIR"] = os.environ.get("LOCAL_FILES_SAVE_DIR")

if not config.get("LOCAL_FILES_SAVE_DIR"):
    config["LOCAL_FILES_SAVE_DIR"] = "/tmp/ocr_inputs"
