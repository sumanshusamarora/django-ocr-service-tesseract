"""
Define models to enable easy integration
"""
import logging
import uuid

import checksum
import s3urls
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from s3urls import parse_url
from urllib.parse import unquote_plus, unquote

from django_ocr_service.custom_storage import CloudMediaHybridStorage
from . import (
    download_locally_if_cloud_storage_path,
    generate_cloud_storage_key,
    generate_save_image_kwargs,
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
        storage = CloudMediaHybridStorage,
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

    def _prepare_for_ocr(self):
        """
        Perform OCR on input file
        :return:
        """
        self.input_is_image = False
        image_filepaths = []

        if self.file.name:
            local_filepath = self.file.storage.local_filepath
            logger.info(f"Received uploaded file - {local_filepath} as input")
        else:
            self.cloud_storage_uri = unquote(unquote_plus(self.cloud_storage_uri))
            filepath = unquote(unquote_plus(self.cloud_storage_uri))
            logger.info(f"Stored file uri - {filepath}")
            local_filepath = download_locally_if_cloud_storage_path(
                filepath, save_dir=settings.LOCAL_FILES_SAVE_DIR
            )
            logger.info(f"Cloud URI file downloaded locally at {local_filepath}")

        if not isinstance(local_filepath, str):
            logger.info("File download failed")
            return

        self.checksum = checksum.get_for_file(local_filepath)

        if is_pdf(local_filepath):
            image_filepaths = pdf_to_image(
                pdf_path=local_filepath,
                output_folder=settings.LOCAL_FILES_SAVE_DIR,
            )

        elif is_image(local_filepath):
            image_filepaths = [local_filepath]
            self.input_is_image = True

        return image_filepaths, local_filepath

    def _do_ocr(self, image_filepaths: list, cloud_storage_objects_kw_args: list):
        """

        :return:
        """
        if image_filepaths:
            # Generate cloud storage paths to allow upload and ocr
            cloud_storage_object_paths = [
                generate_cloud_storage_key(
                    path=kw_args["path"],
                    key=kw_args["key"],
                    prefix=kw_args["prefix"],
                    append_datetime=kw_args["append_datetime"],
                )
                for kw_args in cloud_storage_objects_kw_args
            ]

            for index, image in enumerate(image_filepaths):
                kw_args = {
                    "imagepath": image,
                    "preprocess": True,
                    "ocr_config": None,
                    "ocr_engine": "tesseract",
                    "inputocr_guid": self.guid,
                    "cloud_imagepath": cloud_storage_object_paths[index],
                    "save_images_to_cloud": True,
                    "save_to_cloud_kw_args": cloud_storage_objects_kw_args[index],
                    "use_async_to_upload": settings.USE_ASYNC_FOR_SPEED,
                }

                use_async_to_ocr = settings.USE_ASYNC_FOR_SPEED

                if use_async_to_ocr:
                    try:
                        from django_q.tasks import async_task

                        logger.info("Adding async task to OCR image!!!")
                        async_task(
                            func="ocr.ocr_utils.ocr_image",
                            group="OCR",
                            **kw_args,
                        )
                        logger.info(
                            "Async task to OCR image added!!!"
                        )
                    except Exception as exception:
                        logger.error(
                            "Error adding async task to upload image to cloud"
                        )
                        logger.error(exception)
                        use_async_to_ocr = False

                # Else condition is not used on purpose since we want to move the job to happen in
                # sync fashion if job scheduling fails
                if not use_async_to_ocr:
                    ocr_image(**kw_args)

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
        image_filepaths, local_filepath = self._prepare_for_ocr()

        cloud_storage_objects_kw_args = generate_save_image_kwargs(
            images=image_filepaths,
            pdf_path=local_filepath,
            prefix="media",
            append_datetime=True,
            cloud_storage="s3",
        )

        logger.info(
            "Pre-work finished. All set to start OCR process after saving the model again"
        )
        super(OCRInput, self).save()

        logger.info("Starting OCR process now")
        self._do_ocr(image_filepaths, cloud_storage_objects_kw_args)
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
