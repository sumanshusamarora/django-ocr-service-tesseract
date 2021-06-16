# django-ocr-service-tesseract
Django API Service that exposes REST endpoint and Kafka messaging to OCR pdfs and images


### Sample Config
```yaml

DATABASES:
  default:
    ENGINE: "django.db.backends.postgresql_psycopg2"
    HOST: "localhost"
    NAME: "mtg_clf_ext_app"
    USER: "ml-user"
    PASSWORD: "db_password"
    PORT: "5432"

DEBUG: True
SECRET_KEY: "secret-key"

#AWS
AWS_ACCESS_KEY_ID: "AWS_ACCESS_KEY_ID"
AWS_SECRET_ACCESS_KEY: "AWS_SECRET_ACCESS_KEY"
AWS_STORAGE_BUCKET_NAME: "AWS_STORAGE_BUCKET_NAME"

# TOKEN
TOKEN_VALIDITY_IN_HOURS: 1

#SUPERUSER
DJANGO_SUPERUSER_USERNAME: "admin"
DJANGO_SUPERUSER_EMAIL: "admin@example.com"
DJANGO_SUPERUSER_PASSWORD: "PASSWORD"

# IMAGE PREPROCESSING
IMAGE_SIZE: 1800
BINARY_THRESHOLD: 180

# OCR
OCR_OEM: 11
```