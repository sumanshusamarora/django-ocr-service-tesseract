"""
Define models to enable easy integration
"""
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from s3urls import parse_url

# Create your models here.
class OCRInput(models.Model):
    """
    Model to enable OCR input API and UI utility
    """

    guid = models.CharField(max_length=100, editable=False)
    file = models.FileField(
        upload_to="input_pdfs",
        blank=True,
        null=True,
        help_text="File or Cloud storage URL/URI required",
    )
    cloud_storage_url_or_uri = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
        help_text="File or Cloud storage URL/URI required",
    )
    bucket_name = models.CharField(max_length=255, blank=True, null=True)
    filename = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """
        Applies validators
        :return:
        """
        if not self.file.name and not self.cloud_storage_url_or_uri:
            raise ValidationError("Cloud file path or file upload required")

    def save(self, *args, **kwargs):
        """
        Override base save to add additional checks and actions

        :return:
        """
        # Set default bucket name, will be overridden if different
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME

        if not self.guid:
            self.guid = uuid.uuid4().hex

        if self.cloud_storage_url_or_uri:
            parsed_url_dict = parse_url(self.cloud_storage_url_or_uri)
            self.bucket_name = parsed_url_dict["bucket"]
        else:
            self.cloud_storage_url_or_uri = self.file.url

        super(OCRInput, self).save()

    def __str__(self):
        """

        :return:
        """
        return f'GUID: {self.guid} || Bucket: {self.bucket_name} || Last Modified At: {self.modified_at.strftime("%Y-%m-%d %H:%M:%S")}'
