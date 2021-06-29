"""
Tests for ocr utils. Most of these methods have already been tested as part of api and model testing.
This module contains atomic tests for each method (where possible)
"""
from datetime import datetime
import os

import checksum
import numpy as np
from django.conf import settings
from django.core.files import File
from django.core.files.uploadedfile import InMemoryUploadedFile
import pandas as pd
import pdf2image
from PIL import Image
import pytest

from ocr.models import (
    OCRInput,
    OCROutput,
)
from ocr.ocr_utils import (
    build_tesseract_ocr_config,
    load_image,
    ocr_using_tesseract_engine,
    is_pdf,
    is_image,
    download_locally_if_cloud_storage_path,
    pdf_to_image,
    generate_text_from_ocr_output,
    ocr_image,
    get_obj_if_already_present,
)
from ocr.storage_utils import (
    delete_objects_from_cloud_storage,
    generate_cloud_storage_key,
)
from .help_testutils import (
    TESTFILE_IMAGE_PATH,
    TESTFILE_PDF_PATH,
    TEST_DATAFRAME,
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
        pdf_path=TESTFILE_PDF_PATH, output_folder=local_dir, save_images_to_cloud=False,
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
        pdf_path=TESTFILE_PDF_PATH, save_images_to_cloud=False,
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
        pdf_path=TESTFILE_PDF_PATH, save_images_to_cloud=True, append_datetime=True,
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


@pytest.mark.django_db(transaction=True)
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


def test_pdf_to_image_other_storage():
    """

    :return:
    """
    with pytest.raises(NotImplementedError):
        pdf_to_image(pdf_path=TESTFILE_PDF_PATH, cloud_storage="not s3")


def test_build_tesseract_ocr_config_default():
    """

    :return:
    """
    assert build_tesseract_ocr_config() == "tsv --oem 11"


def test_build_tesseract_ocr_config_custom():
    """

    :return:
    """
    assert (
        build_tesseract_ocr_config(
            tsv_or_txt="txt", oem=4, psm=1, tessdata_dir="something"
        )
        == "txt --oem 4 --psm 1 --tessdata-dir something"
    )


def test_build_tesseract_ocr_config_setting(settings):
    """

    :return:
    """
    settings.OCR_OEM = 4
    settings.OCR_PSM = 1
    settings.OCR_TESSDATA_DIR = "something"
    assert (
        build_tesseract_ocr_config(tsv_or_txt="txt")
        == "txt --oem 4 --psm 1 --tessdata-dir something"
    )


@pytest.mark.django_db(transaction=True)
def test_ocr_image():
    """

    :return:
    """
    out = ocr_image(
        imagepath=TESTFILE_IMAGE_PATH,
        preprocess=True,
        ocr_config=None,
        ocr_engine="tesseract",
    )
    assert isinstance(out, str)


@pytest.mark.django_db(transaction=True)
def test_ocr_image_no_preprocess():
    """

    :return:
    """
    out = ocr_image(
        imagepath=TESTFILE_IMAGE_PATH,
        preprocess=False,
        ocr_config=None,
        ocr_engine="tesseract",
    )
    assert isinstance(out, str)


@pytest.mark.django_db(transaction=True)
def test_ocr_image_manual_ocr_config():
    """

    :return:
    """
    out = ocr_image(
        imagepath=TESTFILE_IMAGE_PATH,
        preprocess=False,
        ocr_config="--psm 4 --oem 3",
        ocr_engine="tesseract",
    )
    assert isinstance(out, str)


def test_generate_text_from_ocr_output():
    """

    :return:
    """
    dataframe = pd.read_pickle(TEST_DATAFRAME)
    text = generate_text_from_ocr_output(dataframe)
    assert isinstance(text, str)


def test_load_image_preprocess():
    """

    :return:
    """
    image_array = load_image(imagepath=TESTFILE_IMAGE_PATH, preprocess=True,)
    assert isinstance(image_array, np.ndarray)


def test_load_image_no_preprocess():
    """

    :return:
    """
    image_array = load_image(imagepath=TESTFILE_IMAGE_PATH, preprocess=False,)
    assert (
        isinstance(image_array, np.ndarray)
        and image_array.shape == Image.open(TESTFILE_IMAGE_PATH).size[::-1]
    )


def test_ocr_using_tesseract_engine():
    """

    :return:
    """
    assert isinstance(ocr_using_tesseract_engine(TESTFILE_IMAGE_PATH), str)


@pytest.mark.django_db(transaction=True)
def test_get_obj_if_already_present():
    """

    :param self:
    :return:
    """
    data = File(open(TESTFILE_PDF_PATH, "rb"))
    filename = os.path.split(TESTFILE_PDF_PATH)[-1]

    upload_file = InMemoryUploadedFile(
        name=filename,
        file=data,
        content_type="multipart/form-data",
        size=500,
        field_name=None,
        charset=None,
    )
    guid = "test_get_obj_if_already_present"

    input_obj = OCRInput.objects.create(file=upload_file, guid=guid,)
    checksum_image_file = checksum.get_for_file(TESTFILE_IMAGE_PATH)

    out_before_adding = get_obj_if_already_present(checksum_image_file)

    output_obj = OCROutput.objects.create(
        guid=input_obj,
        image_path=TESTFILE_IMAGE_PATH,
        checksum=checksum_image_file,
        text="blah blah",
    )

    out_after_adding = get_obj_if_already_present(checksum_image_file)

    assert not out_before_adding and out_after_adding == output_obj


@pytest.mark.django_db(transaction=True)
def test_ocr_image_when_object_already_present():
    """

    :param self:
    :return:
    """
    data = File(open(TESTFILE_PDF_PATH, "rb"))
    filename = os.path.split(TESTFILE_PDF_PATH)[-1]

    upload_file = InMemoryUploadedFile(
        name=filename,
        file=data,
        content_type="multipart/form-data",
        size=500,
        field_name=None,
        charset=None,
    )
    guid = "test_get_obj_if_already_present"

    input_obj = OCRInput.objects.create(file=upload_file, guid=guid,)
    checksum_image_file = checksum.get_for_file(TESTFILE_IMAGE_PATH)

    _ = OCROutput.objects.create(
        guid=input_obj,
        image_path=TESTFILE_IMAGE_PATH,
        checksum=checksum_image_file,
        text="blah blah",
    )

    text = ocr_image(imagepath=TESTFILE_IMAGE_PATH, preprocess=False)

    assert text == "blah blah"
