"""
Test OCR model
"""
import os.path
import time
import uuid

from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.uploadedfile import InMemoryUploadedFile
import pytest
from s3urls import parse_url

from ocr import (
    delete_objects_from_cloud_storage,
)
from ocr.models import OCRInput, OCROutput
from .help_testutils import TESTFILE_PDF_PATH, TESTFILE_IMAGE_PATH

pytestmark = pytest.mark.django_db(transaction=True)


class TestOCRInputOutputModel:
    """ """

    def setup_method(self):
        """

        :return:
        """
        data = File(open(TESTFILE_PDF_PATH, "rb"))
        filename = os.path.split(TESTFILE_PDF_PATH)[-1]

        self.upload_file = InMemoryUploadedFile(
            name=filename,
            file=data,
            content_type="multipart/form-data",
            size=500,
            field_name=None,
            charset=None,
        )
        self.guid = uuid.uuid4().hex

    def test_create_model_object_upload_pdf(self):
        """

        :return:
        """

        ocr_input_object = OCRInput(
            file=self.upload_file,
            guid=self.guid,
            ocr_config="--oem 4",
        )
        ocr_input_object.save()

        input_obj = OCRInput.objects.get(guid=self.guid)
        time.sleep(5)
        output_objs = OCROutput.objects.filter(guid=input_obj)
        delete_objects_from_cloud_storage(
            keys=[parse_url(obj.image_path)["key"] for obj in output_objs]
        )
        assert ocr_input_object.guid == self.guid and len(output_objs) > 0

    def test_create_model_object_upload_image(self):
        """

        :return:
        """
        data = File(open(TESTFILE_IMAGE_PATH, "rb"))
        filename = os.path.split(TESTFILE_IMAGE_PATH)[-1]

        self.upload_image = InMemoryUploadedFile(
            name=filename,
            file=data,
            content_type="image/png",
            size=500,
            field_name=None,
            charset=None,
        )
        ocr_input_object = OCRInput(
            file=self.upload_image,
            guid=self.guid,
            ocr_config="--oem 4",
        )
        ocr_input_object.save()

        input_obj = OCRInput.objects.get(guid=self.guid)
        time.sleep(5)
        output_objs = OCROutput.objects.filter(guid=input_obj)
        delete_objects_from_cloud_storage(
            keys=[parse_url(obj.image_path)["key"] for obj in output_objs]
        )
        assert (
            ocr_input_object.guid == self.guid
            and len(output_objs) > 0
            and isinstance(output_objs[0].text, str)
            and isinstance(output_objs[0].image_path, str)
        )

    def test_clean_method_raise_validation_error(self):
        """

        :return:
        """
        ocr_input_object = OCRInput(
            guid=self.guid,
            ocr_config="--oem 4",
        )
        with pytest.raises(ValidationError):
            ocr_input_object.clean()
