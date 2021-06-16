from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class CloudMediaStorage(S3Boto3Storage):
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    location = "media"
    file_overwrite = False


class CloudStaticStorage(S3Boto3Storage):
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    location = "static"
    file_overwrite = True
