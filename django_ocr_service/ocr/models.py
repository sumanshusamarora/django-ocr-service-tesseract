"""
Define models to enable easy integration
"""
import logging
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from s3urls import parse_url
import urllib

from . import (
    delete_objects_from_s3,
    download_locally_if_s3_path,
    is_image,
    is_pdf,
    is_s3,
    ocr_image,
    pdf_to_image,
    purge_directory
)

logger = logging.getLogger(__name__)

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
    ocr_config = models.CharField(max_length=255, blank=True, null=True)
    ocr_language = models.CharField(max_length=50, blank=True, null=True)
    ocr_text = models.TextField(max_length=None, blank=True, null=True)
    result_response = models.TextField(max_length=None, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """
        Applies validators
        :return:
        """
        if not self.file.name and not self.cloud_storage_url_or_uri:
            raise ValidationError("Cloud file path or file upload required")

    def delete_input_file(self, filepath):
        """
        Delete input file post procesing
        :return:
        """
        if settings.DROP_PDF_POST_PROCESSING:
            s3_parse_dict = is_s3(filepath)
            if s3_parse_dict:
                logger.info("Dropping input pdf")
                delete_objects_from_s3(
                    keys=s3_parse_dict["key"], bucket=s3_parse_dict["bucket"]
                )

    def do_ocr(self):
        """
        Perform OCR on input file
        :return:
        """
        try:
            image_filepaths = []
            ocr_text_list = []

            if self.file:
                filepath = self.file.url
            else:
                filepath = self.cloud_storage_url_or_uri

            filepath = urllib.parse.unquote(filepath)

            local_filepath = download_locally_if_s3_path(filepath, save_dir=settings.LOCAL_FILES_SAVE_DIR)

            if is_pdf(local_filepath):
                image_filepaths, s3_object_paths = pdf_to_image(pdf_path=local_filepath)

            elif is_image(local_filepath):
                image_filepaths = [local_filepath]

            if image_filepaths:
                output_dict = dict()
                for index, image in enumerate(image_filepaths):
                    ocr_text = ocr_image(imagepath=image)
                    ocr_text_list.append(ocr_text)
                    output_dict[s3_object_paths[index]] = ocr_text

                self.ocr_text = "\n".join(ocr_text)
                self.result_response = output_dict

        except Exception as exception:
            purge_directory(settings.LOCAL_FILES_SAVE_DIR)
            raise exception
        else:
            purge_directory(settings.LOCAL_FILES_SAVE_DIR)
            self.delete_input_file(filepath)


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

        self.do_ocr()

        super(OCRInput, self).save()

    def __str__(self):
        """

        :return:
        """
        return f'GUID: {self.guid} || Bucket: {self.bucket_name} || Last Modified At: {self.modified_at.strftime("%Y-%m-%d %H:%M:%S")}'
