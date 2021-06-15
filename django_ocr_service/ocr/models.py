import os
import uuid

from django.conf import settings
from django.db import models
from PyPDF2 import PdfFileReader

from .ocr_utils import upload_to_s3

# Create your models here.
class OCRInput(models.Model):
    """

    """
    guid = models.CharField(max_length=100)
    file = models.FileField(upload_to="input_pdfs", blank=True, null=True)
    s3_path = models.TextField(max_length=None)
    bucket_name = models.CharField(max_length=255)
    is_pdf = models.NullBooleanField()

    def save(self):
        if not self.guid:
            self.guid = uuid.uuid4().hex

        if self.file.path:
            self.s3_path = upload_to_s3(path=os.path.join(settings.MEDIA_URL, self.file.path), bucket=settings.AWS_STORAGE_BUCKET_NAME, prefix="input_pdfs")
            self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME

        if self.file.path and os.path.splitext(self.file.path).lower() == ".pdf":
            self.is_pdf = True
        else:
            self.is_pdf = False

        super(OCRInput, self).save()


class OCROutput(models.Model):
    """

    """

    guid = models.ForeignKey(OCRInput, on_delete=models.CASCADE)
