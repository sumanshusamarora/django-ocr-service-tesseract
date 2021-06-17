"""
Test for serializer
"""
import os

from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile

from ocr.serializers import OCRInputSerializer
from .help_testutils import TESTFILE_PDF_PATH


def test_positive_case_storage_path():
    """

    :return:
    """
    serializer_obj = OCRInputSerializer(
        data={"cloud_storage_url_or_uri": "some string"}
    )
    assert serializer_obj.is_valid()


def test_positive_case_uploaded_file():
    """

    :return:
    """
    data = File(open(TESTFILE_PDF_PATH, "rb"))
    filename = os.path.split(TESTFILE_PDF_PATH)[-1]
    upload_file = SimpleUploadedFile(
        name=filename, content=data.read(), content_type="multipart/form-data"
    )
    serializer_obj = OCRInputSerializer(data={"file": upload_file})
    assert serializer_obj.is_valid()


def test_positive_case_no_input():
    """

    :return:
    """
    serializer_obj = OCRInputSerializer(data={})
    assert serializer_obj.is_valid()


def test_more_than_just_file():
    """ """
    serializer_obj = OCRInputSerializer(
        data={"cloud_storage_url_or_uri": "some string", "ocr_config": "something"}
    )
    assert serializer_obj.is_valid()
