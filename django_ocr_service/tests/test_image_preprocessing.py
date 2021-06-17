"""
Tests for image preprocessing
"""
import pytest

from ocr.models import OCRInput
from .help_testutils import (
    create_rest_user_login_generate_token,
    TESTFILE_PDF_PATH,
    UploadDeleteTestFile,
)

pytestmark = pytest.mark.django_db()
