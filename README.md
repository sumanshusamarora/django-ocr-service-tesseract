[![buddy pipeline](https://app.buddy.works/mlaiconsulting/django-ocr-service-tesseract/pipelines/pipeline/336761/badge.svg?token=b6b63ed04ef9440a32ede29c63bfd6b7240149764f645d3971cc67db0c7b5a9d "buddy pipeline")](https://app.buddy.works/mlaiconsulting/django-ocr-service-tesseract/pipelines/pipeline/336761)
# django-ocr-service-tesseract
Django API Service that exposes REST endpoint and Kafka messaging to OCR pdfs and images


### Sample Config
Add or mount a config.yml file in [config](config) directory of this repo. A config.yml should contain below information. 

Some config variables are recommended to be defined as environment variable rather than in config but for running/testing the application locally, it should be fine to define them in config.
```yaml
DATABASES:
  default:
    ENGINE: "django.db.backends.postgresql_psycopg2"
    HOST: "localhost" # Can be overridden by DB_HOST
    USER: "ml-user" # Can be overridden by DB_USER
    PASSWORD: "db_password" # Recommended as environment variable DB_PASSWORD
    PORT: "5432" # Can be overridden by DB_PORT
    
# You could also add DB_SCHEMA env variable if you need to use a specific schema

DEBUG: True
SECRET_KEY: "secret-key" # Recommended as environment variable SECRET_KEY

# AWS
AWS_ACCESS_KEY_ID: "AWS_ACCESS_KEY_ID" # Recommended as environment variable AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY: "AWS_SECRET_ACCESS_KEY" # Recommended as environment variable AWS_SECRET_ACCESS_KEY
AWS_STORAGE_BUCKET_NAME: "AWS_STORAGE_BUCKET_NAME"

# TOKEN
TOKEN_VALIDITY_IN_HOURS: 1

#SUPERUSER
DJANGO_SUPERUSER_USERNAME: "admin"
DJANGO_SUPERUSER_EMAIL: "admin@example.com"
DJANGO_SUPERUSER_PASSWORD: "PASSWORD" # Recommended as environment variable DJANGO_SUPERUSER_PASSWORD

# IMAGE PREPROCESSING
IMAGE_SIZE: 1800 # Optional, but gets set to 1800 by default if not defined
BINARY_THRESHOLD: 180 # Optional, but gets set to 180 by default if not defined

# OCR
OCR_OEM: 11
OCR_PSM: 0 # Optional
OCR_LANGUAGE: "eng" # Optional
```
