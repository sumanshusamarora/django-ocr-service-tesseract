"""
Test API Methods
"""
import os.path
import time

from django.conf import settings  # Being used by a test. Do not remove settings import
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django_expiring_token.models import ExpiringToken
import pytest
from s3urls import parse_url
import signal
import subprocess

from ocr import (
    delete_objects_from_cloud_storage,
    object_exists_in_cloud_storage,
)
from ocr.models import OCRInput, OCROutput
from .help_testutils import (
    create_rest_user_login_generate_token,
    TESTFILE_PDF_PATH,
    UploadDeleteTestFile,
)

pytestmark = pytest.mark.django_db(transaction=True)


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
        self.process = subprocess.Popen(
            ["python", "manage.py", "qcluster"], shell=True, preexec_fn=os.setsid
        )
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
        os.killpg(self.process.pid, signal.SIGTERM)

    def test_post_ocr_unauthenticated(self):
        """

        :return:
        """
        response = self.django_client.post(
            "/api/ocr/",
            data={"cloud_storage_uri": self.uploaded_filepath},
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
            "/api/ocr/", data={"cloud_storage_uri": self.uploaded_filepath}
        )

        ocrinput_objs = OCRInput.objects.all().first()

        assert (
            isinstance(ocrinput_objs.guid, str)
            and response.status_code == 200
            and response.data["guid"] == ocrinput_objs.guid
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
        response = self.django_client.post("/api/ocr/", data={"file": upload_file},)

        ocrinput_objs = OCRInput.objects.all().first()
        time.sleep(5)

        assert (
            isinstance(ocrinput_objs.guid, str)
            and response.status_code == 200
            and response.data["guid"] == ocrinput_objs.guid
        )

    def test_post_ocr_authenticated_no_async(self, settings):
        """
        apscheduler doesnt play well with pytest so turning background function off to
        1) Test the non background code works as expected
        2) Test the post background functionality of code

        :return:
        """
        settings.USE_BACKGROUND_TASK_FOR_SPEED = False
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

        response = self.django_client.post("/api/ocr/", data={"file": upload_file},)

        ocrinput_objs = OCRInput.objects.all().first()

        assert (
            isinstance(ocrinput_objs.guid, str)
            and response.status_code in [200, 202]
            and response.data["guid"] == ocrinput_objs.guid
        )


class TestGetOCR:
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

    def test_get_ocr(self):
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
            "/api/ocr/", data={"cloud_storage_uri": self.uploaded_filepath}
        )

        time.sleep(5)
        self.django_client.credentials(HTTP_AUTHORIZATION="Token " + token)
        getocr_response = self.django_client.get(
            "/api/get-ocr/", {"guid": response.data["guid"]},
        )
        assert str(getocr_response.status_code).startswith("20")


class TestAPINegativeScenarios:
    def setup_method(self):
        """

        :return:
        """
        (
            self.django_client,
            self.user,
            self.token_true,
        ) = create_rest_user_login_generate_token()

    def test_post_ocr_without_data(self):
        """

        :return:
        """
        self.django_client.force_authenticate(user=self.user)
        token_response = self.django_client.get(
            "/api/get-token/", content_type="application/json"
        )
        token = token_response.data["token"]
        self.django_client.credentials(HTTP_AUTHORIZATION="Token " + token)
        response = self.django_client.post("/api/ocr/")

        assert (
            response.status_code == 400
            and response.json()["Error"] == "File input required"
        )

    def test_post_ocr_wrong_data(self):
        """

        :return:
        """
        self.django_client.force_authenticate(user=self.user)
        token_response = self.django_client.get(
            "/api/get-token/", content_type="application/json"
        )
        token = token_response.data["token"]
        self.django_client.credentials(HTTP_AUTHORIZATION="Token " + token)
        response = self.django_client.post("/api/ocr/", data={"file": "string"})
        assert response.status_code == 400 and isinstance(response.json()["file"], list)

    def test_get_ocr_no_guid(self):
        """

        :return:
        """
        self.django_client.force_authenticate(user=self.user)
        token_response = self.django_client.get(
            "/api/get-token/", content_type="application/json"
        )
        token = token_response.data["token"]
        self.django_client.credentials(HTTP_AUTHORIZATION="Token " + token)
        response = self.django_client.get("/api/get-ocr/")
        assert response.status_code == 400 and response.json() == {
            "guid": "Invalid request, guid expected"
        }

    def test_get_ocr_wrong_guid_value(self):
        """

        :return:
        """
        self.django_client.force_authenticate(user=self.user)
        token_response = self.django_client.get(
            "/api/get-token/", content_type="application/json"
        )
        token = token_response.data["token"]
        self.django_client.credentials(HTTP_AUTHORIZATION="Token " + token)
        response = self.django_client.get("/api/get-ocr/", {"guid": "string"})
        assert response.status_code == 400 and response.json()["guid"].startswith(
            "Invalid guid"
        )
