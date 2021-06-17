"""
Test OCR model
"""
import os.path
import uuid

from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings
import pytest

from ocr.models import OCRInput
from .help_testutils import TESTFILE_PDF_PATH, UploadDeleteTestFile

pytestmark = pytest.mark.django_db()

class TestOCRInputModel:
    """

    """
    def setup_method(self):
        """

        :return:
        """
        data = File(open(TESTFILE_PDF_PATH, 'rb'))
        filename = os.path.split(TESTFILE_PDF_PATH)[-1]
        self.upload_file = InMemoryUploadedFile(name=filename,
                                                file=data,
                                                content_type='multipart/form-data',
                                                size=500,
                                                field_name=None,
                                                charset=None,
                                                )
        self.guid = uuid.uuid4().hex

    def test_create_model_object_upload_file(self):
        """

        :return:
        """
        ocr_input_object = OCRInput(file=self.upload_file,
                                    guid=self.guid,
                                    ocr_config="--oem 4",
                                    )
        ocr_input_object.save()
        assert ocr_input_object.guid == self.guid and isinstance(ocr_input_object.ocr_text, str) and ocr_input_object.bucket_name == settings.AWS_STORAGE_BUCKET_NAME


    def test_clean_method_raise_validation_error(self):
        """

        :return:
        """
        ocr_input_object = OCRInput(guid=self.guid,
                                    ocr_config="--oem 4",
                                    )
        with pytest.raises(ValidationError):
            ocr_input_object.clean()

