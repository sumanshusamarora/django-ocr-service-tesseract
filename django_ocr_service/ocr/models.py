"""
Define models to enable easy integration
"""
import logging
import uuid

import arrow
import checksum
import s3urls
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from s3urls import parse_url
from urllib.parse import unquote_plus, unquote

from . import (
    download_locally_if_cloud_storage_path,
    generate_cloud_storage_key,
    delete_objects_from_cloud_storage,
    is_image,
    is_pdf,
    is_cloud_storage,
    ocr_image,
    pdf_to_image,
)

logger = logging.getLogger(__name__)

# Create your models here.
class OCRInput(models.Model):
    """
    Model to enable OCR input API and UI utility
    """

    guid = models.CharField(max_length=100, editable=False)
    file = models.FileField(
        upload_to="input_files",
        blank=True,
        null=True,
        help_text="File or Cloud storage URI required",
    )
    cloud_storage_uri = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
        help_text="File or Cloud storage URI required",
    )
    bucket_name = models.CharField(max_length=255, blank=True, null=True)
    filename = models.CharField(max_length=255, blank=True, null=True)
    ocr_config = models.CharField(max_length=255, blank=True, null=True)
    ocr_language = models.CharField(max_length=50, blank=True, null=True)
    page_count = models.PositiveIntegerField(default=0)
    result_response = models.TextField(max_length=None, blank=True, null=True)
    checksum = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """
        Applies validators
        :return:
        """
        if not self.file.name and not self.cloud_storage_uri:
            raise ValidationError("Cloud file path or file upload required")

    def _delete_input_file(self):
        """

        :return:
        """
        if self.file.name:
            self.file.storage.delete(name=self.file.name)
            logger.info("Dropped uploaded input file")
        else:
            logger.info("Starting process to delete cloud storage input file")
            parsed_uri_dict = parse_url(self.cloud_storage_uri)
            delete_objects_from_cloud_storage(
                keys=[parsed_uri_dict["key"]], bucket=parsed_uri_dict["bucket"]
            )
            logger.info(
                f'Dropped input file {parsed_uri_dict["key"]} in bucket {parsed_uri_dict["bucket"]}'
            )

    def _prepare_for_ocr(self):
        """
        Perform OCR on input file
        :return:
        """
        self.input_is_image = False
        image_filepaths = []

        if self.file.name:
            filepath = self.file.url
            logger.info(f"Uploaded file - {filepath}")
        else:
            self.cloud_storage_uri = unquote(unquote_plus(self.cloud_storage_uri))
            filepath = unquote(unquote_plus(self.cloud_storage_uri))
            logger.info(f"Stored file uri - {filepath}")

        local_filepath = download_locally_if_cloud_storage_path(
            filepath, save_dir=settings.LOCAL_FILES_SAVE_DIR
        )

        if not isinstance(local_filepath, str):
            logger.info("File download failed")
            return
        else:
            logger.info(f"File {filepath} downloaded locally")

        self.checksum = checksum.get_for_file(local_filepath)

        if is_pdf(local_filepath):
            image_filepaths, cloud_storage_objects_kw_args = pdf_to_image(
                pdf_path=local_filepath,
                save_images_to_cloud=settings.SAVE_IMAGES_TO_CLOUD,
                use_async_to_upload=settings.USE_BACKGROUND_TASK_FOR_SPEED,
            )

            # Below line allows getting the upload paths even if upload to cloud storage
            #  not finished due to threading workers still finishing their jobs
            cloud_storage_object_paths = [
                generate_cloud_storage_key(
                    path=kw_args["path"],
                    key=kw_args["key"],
                    prefix=kw_args["prefix"],
                    append_datetime=kw_args["append_datetime"],
                )
                for kw_args in cloud_storage_objects_kw_args
            ]

        elif is_image(local_filepath):
            image_filepaths = [local_filepath]
            cloud_storage_object_paths = [filepath]
            self.input_is_image = True

        return image_filepaths, cloud_storage_object_paths

    def _do_ocr(self, image_filepaths: list, cloud_storage_object_paths: list):
        """

        :return:
        """
        if image_filepaths:
            for index, image in enumerate(image_filepaths):
                kw_args = {
                    "imagepath": image,
                    "preprocess": True,
                    "ocr_config": None,
                    "ocr_engine": "tesseract",
                    "inputocr_guid": self.guid,
                    "cloud_imagepath": cloud_storage_object_paths[index],
                }

                use_async_to_ocr = settings.USE_BACKGROUND_TASK_FOR_SPEED

                if use_async_to_ocr:
                    try:
                        from django_q.models import Schedule
                        from django_q.tasks import schedule

                        logger.info("Scheduling background task to OCR image!!!")
                        schedule(
                            func="ocr.ocr_utils.ocr_image",
                            name=f"OCR-{self.guid}-{image}-{uuid.uuid4().hex}"[:99],
                            schedule_type=Schedule.ONCE,
                            **kw_args,
                            next_run=arrow.utcnow().shift(seconds=3).datetime,
                        )
                        logger.info(
                            "Background task to OCR image scheduled successfully!!!"
                        )
                    except Exception as exception:
                        logger.error(
                            "Error adding background task to upload image to cloud"
                        )
                        logger.error(exception)
                        use_async_to_ocr = False

                # Else condition is not used on purpose since we want to move the job to happen in
                # sync fashion if job scheduling fails
                if not use_async_to_ocr:
                    ocr_image(**kw_args)

            if settings.DROP_INPUT_FILE_POST_PROCESSING and not self.input_is_image:
                # Only delete input file if its a pdf since we convert it to images and re-upload it
                # We don not want to duplicate the information
                logger.info(
                    f"Settings to drop input file is {settings.DROP_INPUT_FILE_POST_PROCESSING} and input is not an image so dropping input file"
                )
                try:
                    self._delete_input_file()
                    logger.info("Input file deleted")
                except:
                    logger.warning(
                        "Error dropping input file. Does the application have access to location?"
                    )

        self.result_response = {"guid": self.guid}
        self.page_count = len(image_filepaths)

    def save(self, *args, **kwargs):
        """
        Override base save to add additional checks and actions

        :return:
        """
        # Set default bucket name, will be overridden if different
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME

        if not self.guid:
            self.guid = uuid.uuid4().hex

        logger.info(f"Cloud Log: Input GUID - {self.guid}")

        if self.cloud_storage_uri:
            parsed_uri_dict = parse_url(self.cloud_storage_uri)
            self.bucket_name = parsed_uri_dict["bucket"]
        else:
            self.cloud_storage_uri = self.file.url

        self.clean()

        super(OCRInput, self).save()

        logger.info("Starting pre-work for OCR...")
        image_filepaths, cloud_storage_object_paths = self._prepare_for_ocr()
        super(OCRInput, self).save()
        logger.info("All set to start OCR. Model saved again!")

        logger.info("Starting OCR process now")
        self._do_ocr(image_filepaths, cloud_storage_object_paths)
        logger.info("OCR process finished, saving model object again")
        logger.info(f"Cloud Log: Output GUID - {self.guid}")

        super(OCRInput, self).save()

    def __str__(self):  # pragma: no cover
        """

        :return:
        """
        return f'GUID: {self.guid} || Bucket: {self.bucket_name} || Last Modified At: {self.modified_at.strftime("%Y-%m-%d %H:%M:%S")}'


class OCROutput(models.Model):
    """
    Model to show OCR Output
    """

    guid = models.ForeignKey(OCRInput, on_delete=models.CASCADE)
    image_path = models.CharField(max_length=1000, blank=False, null=False)
    text = models.TextField(max_length=None, blank=True, null=False)
    checksum = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """

        :return:
        """
        if not is_cloud_storage(self.image_path):
            self.image_path = s3urls.build_url(
                "s3", self.guid.bucket_name, self.image_path
            )

        super(OCROutput, self).save(*args, **kwargs)

    def __str__(self):
        """

        :return:
        """
        return f"{self.guid} || Imagepath: {self.image_path}"
