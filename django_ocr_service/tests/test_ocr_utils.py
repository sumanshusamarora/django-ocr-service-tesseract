"""
Tests for ocr utils. Most of these methods have already been tested as part of api and model testing.
This module contains atomic tests for each method (where possible)
"""
from datetime import datetime
import os
import random
import shutil
import tempfile

from django.conf import settings
import pdf2image
import pytest

from ocr.ocr_utils import (
    is_pdf,
    is_image,
    purge_directory,
    download_locally_if_cloud_storage_path,
    pdf_to_image,
)
from ocr.s3_storage_utils import (
    delete_objects_from_cloud_storage,
    generate_cloud_storage_key,
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
    local_filepath = os.path.join(
        local_dir, os.path.split(upload_delete_obj.filepath)[-1]
    )
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
    download_locally_if_cloud_storage_path(
        filepath=TESTFILE_PDF_PATH, save_dir=local_dir
    )
    after_download_file_exists = os.path.isfile(local_filepath)

    # Teardown
    if after_download_file_exists:
        os.remove(local_filepath)

    # Assert
    assert (
        not before_download_file_exists
        and not after_download_file_exists
        and TESTFILE_PDF_PATH
    )


def test_pdf_to_image_simple_tc():
    """

    :return:
    """
    # Setup
    local_dir = "/tmp/testdir"

    # Test
    local_image_fps, cloud_fps = pdf_to_image(
        pdf_path=TESTFILE_PDF_PATH,
        output_folder=local_dir,
        save_images_to_cloud=False,
    )

    # Teardown
    for impath in local_image_fps:
        if os.path.isfile(impath):
            os.remove(impath)

    assert (
        len(local_image_fps) == 2
        and not cloud_fps
        and os.path.split(local_image_fps[0])[0] == local_dir
    )


def test_pdf_to_image_simple_default_folder():
    """

    :return:
    """
    # Test
    local_image_fps, cloud_fps = pdf_to_image(
        pdf_path=TESTFILE_PDF_PATH,
        save_images_to_cloud=False,
    )
    # Teardown
    for impath in local_image_fps:
        if os.path.isfile(impath):
            os.remove(impath)

    assert (
        len(local_image_fps) == 2
        and not cloud_fps
        and os.path.split(local_image_fps[0])[0] == settings.LOCAL_FILES_SAVE_DIR
    )


def test_pdf_to_image_save_to_cloud_no_prefix():
    """

    :return:
    """
    local_image_fps, cloud_kw_args = pdf_to_image(
        pdf_path=TESTFILE_PDF_PATH,
        save_images_to_cloud=True,
        append_datetime=False,
        prefix=None,
    )

    # Teardown
    for impath in local_image_fps:
        if os.path.isfile(impath):
            os.remove(impath)

    delete_count = delete_objects_from_cloud_storage(
        keys=[cloud_kw["key"] for cloud_kw in cloud_kw_args],
        bucket=cloud_kw_args[0]["bucket"],
    )

    assert (
        len(local_image_fps) == 2
        and len(cloud_kw_args) == 2
        and os.path.split(local_image_fps[0])[0] == settings.LOCAL_FILES_SAVE_DIR
        and delete_count == 2
    )


def test_pdf_to_image_save_to_cloud_with_custom_prefix():
    """

    :return:
    """
    # Setup
    prefix = "testfile"

    # Test
    local_image_fps, cloud_kw_args = pdf_to_image(
        pdf_path=TESTFILE_PDF_PATH,
        save_images_to_cloud=True,
        prefix=prefix,
        append_datetime=False,
    )

    # Teardown
    cloud_stroage_paths = []
    for index, impath in enumerate(local_image_fps):
        cloud_stroage_paths.append(
            generate_cloud_storage_key(
                path=impath,
                key=cloud_kw_args[index]["key"],
                prefix=cloud_kw_args[index]["prefix"],
                append_datetime=cloud_kw_args[index]["append_datetime"],
            )
        )

        if os.path.isfile(impath):
            os.remove(impath)

    delete_count = delete_objects_from_cloud_storage(
        keys=[cloud_path for cloud_path in cloud_stroage_paths],
        bucket=cloud_kw_args[0]["bucket"],
    )

    # Assert
    assert (
        len(local_image_fps) == 2
        and len(cloud_kw_args) == 2
        and os.path.split(local_image_fps[0])[0] == settings.LOCAL_FILES_SAVE_DIR
        and delete_count == 2
        and cloud_stroage_paths[0].startswith(prefix)
    )


def test_pdf_to_image_save_to_cloud_append_datetime():
    """

    :return:
    """
    # Test
    local_image_fps, cloud_kw_args = pdf_to_image(
        pdf_path=TESTFILE_PDF_PATH,
        save_images_to_cloud=True,
        append_datetime=True,
    )

    # Teardown
    cloud_stroage_paths = []
    for index, impath in enumerate(local_image_fps):
        cloud_stroage_paths.append(
            generate_cloud_storage_key(
                path=impath,
                key=cloud_kw_args[index]["key"],
                prefix=cloud_kw_args[index]["prefix"],
                append_datetime=cloud_kw_args[index]["append_datetime"],
            )
        )

        if os.path.isfile(impath):
            os.remove(impath)

    delete_count = delete_objects_from_cloud_storage(
        keys=[cloud_path for cloud_path in cloud_stroage_paths],
        bucket=cloud_kw_args[0]["bucket"],
    )

    # Assert
    assert (
        len(local_image_fps) == 2
        and len(cloud_kw_args) == 2
        and os.path.split(local_image_fps[0])[0] == settings.LOCAL_FILES_SAVE_DIR
        and delete_count == 2
        and datetime.now().date().__str__() in cloud_stroage_paths[0]
    )


def test_pdf_to_image_save_to_cloud_async():
    """

    :return:
    """
    # Test
    local_image_fps, cloud_kw_args = pdf_to_image(
        pdf_path=TESTFILE_PDF_PATH,
        save_images_to_cloud=True,
        append_datetime=False,
        use_async_to_upload=True,
    )

    # Teardown
    cloud_stroage_paths = []
    for index, impath in enumerate(local_image_fps):
        cloud_stroage_paths.append(
            generate_cloud_storage_key(
                path=impath,
                key=cloud_kw_args[index]["key"],
                prefix=cloud_kw_args[index]["prefix"],
                append_datetime=cloud_kw_args[index]["append_datetime"],
            )
        )

        if os.path.isfile(impath):
            os.remove(impath)

    delete_count = delete_objects_from_cloud_storage(
        keys=[cloud_path for cloud_path in cloud_stroage_paths],
        bucket=cloud_kw_args[0]["bucket"],
    )

    # Assert
    assert (
        len(local_image_fps) == 2
        and len(cloud_kw_args) == 2
        and os.path.split(local_image_fps[0])[0] == settings.LOCAL_FILES_SAVE_DIR
        and delete_count == 2
    )


def test_pdf_to_image_pass_image():
    """

    :return:
    """
    with pytest.raises(pdf2image.exceptions.PDFPageCountError):
        pdf_to_image(pdf_path=TESTFILE_IMAGE_PATH)
