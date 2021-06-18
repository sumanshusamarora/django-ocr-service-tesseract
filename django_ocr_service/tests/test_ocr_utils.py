"""
Tests for ocr utils. Most of these methods have already been tested as part of api and model testing.
This module contains atomic tests for each method (where possible)
"""
from django.conf import settings
import os
import random
import shutil
import tempfile

import pytest

from ocr.ocr_utils import (
    is_pdf,
    is_image,
    purge_directory,
    download_locally_if_cloud_storage_path,
)
from .help_testutils import (
    TESTFILE_IMAGE_PATH,
    TESTFILE_PDF_PATH,
    TEST_DIR,
    UploadDeleteTestFile,
)


@pytest.mark.parametrize(
    "filepath, output",
    [
        (TESTFILE_IMAGE_PATH, False),
        (TESTFILE_PDF_PATH, True),
        (os.path.join(TEST_DIR, os.listdir(TEST_DIR)[0]), False),
    ],
)
def test_is_pdf(filepath, output):
    """

    :return:
    """
    assert is_pdf(filepath) == output


@pytest.mark.parametrize(
    "filepath, output",
    [
        (TESTFILE_IMAGE_PATH, True),
        (TESTFILE_PDF_PATH, False),
        (os.path.join(TEST_DIR, os.listdir(TEST_DIR)[0]), False),
    ],
)
def test_is_image(filepath, output):
    """

    :return:
    """
    assert is_image(filepath) == output


def test_purge_directory():
    """

    :return:
    """
    # Setup
    dir_path = "/tmp/test_data"
    if os.path.isdir(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path, exist_ok=True)
    random_number = random.randint(1, 5)
    temp_files_list = []
    for index in range(random_number):
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            dir=dir_path,
            suffix=".png",
        )
        temp_files_list.append(temp_file)
    # Test
    before_purge = 0
    for file in temp_files_list:
        if os.path.isfile(file.name):
            before_purge += 1

    purge_directory(dir_path)

    after_purge = 0
    for file in temp_files_list:
        if os.path.isfile(file.name):
            after_purge += 1

    # Teardown
    shutil.rmtree(dir_path)
    assert before_purge == random_number and after_purge == 0 and before_purge > 0

def test_download_locally_if_cloud_storage_path():
    """

    :return:
    """
    # Setup
    local_dir = "/tmp/testdir/"
    upload_delete_obj = UploadDeleteTestFile()
    cloud_path = upload_delete_obj.upload_test_file_to_cloud_storage()
    local_filepath = os.path.join(local_dir, os.path.split(upload_delete_obj.filepath)[-1])
    before_download_file_exists = os.path.isfile(local_filepath)

    # Test
    download_locally_if_cloud_storage_path(filepath=cloud_path, save_dir=local_dir)
    after_download_file_exists = os.path.isfile(local_filepath)

    # Teardown
    if after_download_file_exists:
        os.remove(local_filepath)

    # Assert
    assert not before_download_file_exists and after_download_file_exists

def test_download_locally_if_cloud_storage_path_local_file():
    """

    :return:
    """
    # Setup
    local_dir = "/tmp/testdir/"
    local_filepath = os.path.join(local_dir, os.path.split(TESTFILE_PDF_PATH)[-1])
    before_download_file_exists = os.path.isfile(local_filepath)

    # Test
    download_locally_if_cloud_storage_path(filepath=TESTFILE_PDF_PATH, save_dir=local_dir)
    after_download_file_exists = os.path.isfile(local_filepath)

    # Teardown
    if after_download_file_exists:
        os.remove(local_filepath)

    # Assert
    assert not before_download_file_exists and not after_download_file_exists and TESTFILE_PDF_PATH
