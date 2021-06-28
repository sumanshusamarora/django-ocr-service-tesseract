"""
Utils to enable testing without code duplication
"""
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client
from rest_framework.test import APIClient

from ocr import (
    delete_objects_from_cloud_storage,
    upload_to_cloud_storage,
)
from ocr.token import create_auth_token


username = "testuser"
password = "12345"

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
TESTDATA_DIR = os.path.join(TEST_DIR, "testdata")
TESTFILE_PDF_PATH = os.path.join(TESTDATA_DIR, "sample-test-pdf.pdf")
TESTFILE_IMAGE_PATH = os.path.join(TESTDATA_DIR, "test-image.png")
TEST_DATAFRAME = os.path.join(TESTDATA_DIR, "ocr_dataframe.pickle")

def create_user_login_generate_token():
    """

    :return:
    """
    user = User.objects.create(username=username)
    user.set_password(password)
    user.save()
    django_client = Client()
    _ = django_client.login(username=username, password=password)
    token = create_auth_token(sender=User, instance=user)
    return django_client, user, token


def create_rest_user_login_generate_token():
    """

    :return:
    """
    user = User.objects.create(username=username)
    user.set_password(password)
    user.save()
    rest_client = APIClient()
    rest_client.login(username=username, password=password)
    token = create_auth_token(sender=User, instance=user)
    return rest_client, user, token


class UploadDeleteTestFile:
    """ """

    def __init__(self, filepath=None, bucket=None):
        """

        :param filepath:
        :param bucket:
        """
        self.filepath = filepath
        self.bucket = bucket

        if not self.filepath:
            self.filepath = TESTFILE_PDF_PATH

        if not self.bucket:
            self.bucket = settings.AWS_STORAGE_BUCKET_NAME

    def upload_test_file_to_cloud_storage(self):
        """

        :param path:
        :return:
        """
        self.cloud_upload_path = upload_to_cloud_storage(
            path=self.filepath,
            bucket=self.bucket,
            prefix="test_data",
            append_datetime=False,
        )
        return self.cloud_upload_path

    def drop_test_file_from_cloud_storage(self):
        """

        :param path:
        :return:
        """
        delete_objects_from_cloud_storage(
            keys=self.cloud_upload_path,
            bucket=self.bucket,
        )



