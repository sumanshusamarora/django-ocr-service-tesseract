"""
Test API Methods
"""
import os.path

from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django_expiring_token.models import ExpiringToken
import pytest

from ocr.models import OCRInput
from .help_testutils import (
    create_rest_user_login_generate_token,
    TESTFILE_PDF_PATH,
    UploadDeleteTestFile,
)

pytestmark = pytest.mark.django_db()


class TestGetTokenAPI:
    """ """

    def setup_method(self):
        """

        :return:
        """
        (
            self.django_client,
            self.user,
            self.token_true,
        ) = create_rest_user_login_generate_token()

    def test_get_token_authenticated(self):
        """

        :return:
        """
        self.django_client.force_authenticate(user=self.user)
        response = self.django_client.get(
            "/api/get-token/", content_type="application/json"
        )
        expected_token = ExpiringToken.objects.get(user=self.user).key
        assert response.status_code == 200 and response.data == {
            "token": expected_token
        }

    def test_get_token_unauthenticated(self):
        """

        :return:
        """
        response = self.django_client.get(
            "/api/get-token/", content_type="application/json"
        )
        assert response.status_code == 401


class TestPostOCR:
    """ """

    def setup_method(self):
        """

        :return:
        """
        (
            self.django_client,
            self.user,
            self.token_true,
        ) = create_rest_user_login_generate_token()
        self.upload_delete = UploadDeleteTestFile()
        self.uploaded_filepath = self.upload_delete.upload_test_file_to_cloud_storage()

    def teardown_method(self):
        """

        :return:
        """
        self.upload_delete.drop_test_file_from_cloud_storage()

    def test_post_ocr_unauthenticated(self):
        """

        :return:
        """
        response = self.django_client.post(
            "/api/ocr/",
            data={"cloud_storage_url_or_uri": self.uploaded_filepath},
            format="json",
        )
        assert response.status_code == 401

    def test_post_ocr_authenticated_from_uploaded_path(self):
        """

        :return:
        """
        self.django_client.force_authenticate(user=self.user)
        token_response = self.django_client.get(
            "/api/get-token/", content_type="application/json"
        )
        token = token_response.data["token"]
        self.django_client.credentials(HTTP_AUTHORIZATION="Token " + token)

        response = self.django_client.post(
            "/api/ocr/", data={"cloud_storage_url_or_uri": self.uploaded_filepath}
        )
        ocrinput_objs = OCRInput.objects.all()
        assert (
            len(ocrinput_objs) > 0
            and response.status_code == 200
            and isinstance(response.data["response"], dict)
        )

    def test_post_ocr_authenticated_direct_upload(self):
        """

        :return:
        """
        self.django_client.force_authenticate(user=self.user)
        token_response = self.django_client.get(
            "/api/get-token/", content_type="application/json"
        )
        token = token_response.data["token"]

        self.django_client.credentials(HTTP_AUTHORIZATION="Token " + token)
        data = File(open(TESTFILE_PDF_PATH, "rb"))
        filename = os.path.split(TESTFILE_PDF_PATH)[-1]
        upload_file = SimpleUploadedFile(
            name=filename, content=data.read(), content_type="multipart/form-data"
        )

        response = self.django_client.post(
            "/api/ocr/",
            data={"file": upload_file},
        )
        ocrinput_objs = OCRInput.objects.all()
        assert (
            len(ocrinput_objs) > 0
            and response.status_code == 200
            and isinstance(response.data["response"], dict)
        )
