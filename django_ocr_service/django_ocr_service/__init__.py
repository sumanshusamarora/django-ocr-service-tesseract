"""
Setup config
"""
import ast
import os
import uuid

import yaml

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(THIS_DIR, "..", "config")

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
    ast.literal_eval(config.get("DEBUG"))

if os.environ.get("AWS_ACCESS_KEY_ID"):
    config["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID")

if os.environ.get("AWS_SECRET_ACCESS_KEY"):
    config["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY")

if os.environ.get("AWS_STORAGE_BUCKET_NAME"):
    config["AWS_STORAGE_BUCKET_NAME"] = os.environ.get("AWS_STORAGE_BUCKET_NAME")



if not config.get("ALLOWED_HOSTS"):
    config["ALLOWED_HOSTS"] = "*"

if os.environ.get("SUPERUSER"):
    config["SUPERUSER"] = os.environ.get("SUPERUSER")
else:
    config["SUPERUSER"] = None
