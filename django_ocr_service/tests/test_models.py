"""
Test OCR model
"""
import os.path
import uuid

import checksum
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.uploadedfile import InMemoryUploadedFile
import pytest

from ocr.models import OCRInput, OCROutput
from .help_testutils import (
    TESTFILE_PDF_PATH,
    TESTFILE_IMAGE_PATH,
)

pytestmark = pytest.mark.django_db(transaction=True)


class TestOCRInputOutputModel:
    """ """

    def setup_method(self, settings):
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
        assert (
            input_obj.guid == self.guid
            and input_obj.checksum == checksum.get_for_file(TESTFILE_PDF_PATH)
        )

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

        assert (
            input_obj.guid == self.guid
            and input_obj.checksum == checksum.get_for_file(TESTFILE_IMAGE_PATH)
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
