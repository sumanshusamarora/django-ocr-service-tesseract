"""
Tests for ocr utils. Most of these methods have already been tested as part of api and model testing.
This module contains atomic tests for each method (where possible)
"""
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
    download_locally_if_cloud_storage_path,
    generate_save_image_kwargs,
    generate_text_from_ocr_output,
    get_obj_if_already_present,
    is_pdf,
    is_image,
    load_image,
    ocr_image,
    ocr_using_tesseract_engine,
    pdf_to_image,
    save_images,
)
from ocr.storage_utils import (
    delete_objects_from_cloud_storage,
    generate_cloud_storage_key,
    object_exists_in_cloud_storage,
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


def test_pdf_to_image():
    """

    :return:
    """
    # Test
    local_image_fps = pdf_to_image(
        pdf_path=TESTFILE_PDF_PATH,
    )

    # Assert
    assert (
        len(local_image_fps) == 2
        and os.path.split(local_image_fps[0])[0] == settings.LOCAL_FILES_SAVE_DIR
    )


def test_pdf_to_image_pass_image():
    """

    :return:
    """
    with pytest.raises(pdf2image.exceptions.PDFPageCountError):
        pdf_to_image(pdf_path=TESTFILE_IMAGE_PATH)


def test_pdf_to_image_specific_dir():
    """

    :return:
    """
    # Setup
    local_dir = "/tmp/testdir"

    # Test
    local_image_fps = pdf_to_image(
        pdf_path=TESTFILE_PDF_PATH,
        output_folder=local_dir,
    )

    # Teardown
    for impath in local_image_fps:
        if os.path.isfile(impath):
            os.remove(impath)

    assert (
        len(local_image_fps) == 2 and os.path.split(local_image_fps[0])[0] == local_dir
    )


def test_generate_save_image_kwargs():
    """

    :return:
    """
    out = generate_save_image_kwargs(
        images=[TESTFILE_IMAGE_PATH, TESTFILE_PDF_PATH],
        pdf_path=TESTFILE_PDF_PATH,
        append_datetime=False,
        prefix="media",
        cloud_storage="s3",
    )
    expected_out = [
        {
            "path": TESTFILE_IMAGE_PATH,
            "bucket": settings.CLOUD_STORAGE_BUCKET_NAME,
            "prefix": "media",
            "key": "sample-test-pdf.pdf/test-image.png",
            "append_datetime": False,
        },
        {
            "path": TESTFILE_PDF_PATH,
            "bucket": settings.CLOUD_STORAGE_BUCKET_NAME,
            "prefix": "media",
            "key": "sample-test-pdf.pdf/sample-test-pdf.pdf",
            "append_datetime": False,
        },
    ]
    assert out == expected_out


def test_generate_save_image_kwargs_no_prefix():
    """

    :return:
    """
    out = generate_save_image_kwargs(
        images=[TESTFILE_IMAGE_PATH, TESTFILE_PDF_PATH],
        pdf_path=TESTFILE_PDF_PATH,
        append_datetime=False,
        prefix=None,
        cloud_storage="s3",
    )
    expected_out = [
        {
            "path": TESTFILE_IMAGE_PATH,
            "bucket": settings.CLOUD_STORAGE_BUCKET_NAME,
            "prefix": "",
            "key": "sample-test-pdf.pdf/test-image.png",
            "append_datetime": False,
        },
        {
            "path": TESTFILE_PDF_PATH,
            "bucket": settings.CLOUD_STORAGE_BUCKET_NAME,
            "prefix": "",
            "key": "sample-test-pdf.pdf/sample-test-pdf.pdf",
            "append_datetime": False,
        },
    ]
    assert out == expected_out


def generate_save_image_kwargs_other_storage():
    """

    :return:
    """
    with pytest.raises(NotImplementedError):
        generate_save_image_kwargs(
            images=[TESTFILE_IMAGE_PATH, TESTFILE_PDF_PATH],
            pdf_path=TESTFILE_PDF_PATH,
            append_datetime=False,
            prefix=None,
            cloud_storage="s3",
        )


def test_save_images():
    """

    :return:
    """
    kw_args = generate_save_image_kwargs(
        images=[TESTFILE_IMAGE_PATH, TESTFILE_PDF_PATH],
        pdf_path=TESTFILE_PDF_PATH,
        append_datetime=False,
        prefix="test_data",
        cloud_storage="s3",
    )
    save_images(kw_args=kw_args, use_async_to_upload=False)
    objs_exist = [
        object_exists_in_cloud_storage(
            key=f'{kw_arg["prefix"]}/{kw_arg["key"]}', bucket=kw_arg["bucket"]
        )
        for kw_arg in kw_args
    ]
    assert not [obj for obj in objs_exist if not obj]


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
        save_images_to_cloud=False,
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
        save_images_to_cloud=False,
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
        save_images_to_cloud=False,
    )
    assert isinstance(out, str)


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

    input_obj = OCRInput.objects.create(
        file=upload_file,
        guid=guid,
    )
    checksum_image_file = checksum.get_for_file(TESTFILE_IMAGE_PATH)

    _ = OCROutput.objects.create(
        guid=input_obj,
        image_path=TESTFILE_IMAGE_PATH,
        checksum=checksum_image_file,
        text="blah blah",
    )

    text = ocr_image(
        imagepath=TESTFILE_IMAGE_PATH,
        preprocess=False,
        save_images_to_cloud=False,
    )

    assert text == "blah blah"


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
    image_array = load_image(
        imagepath=TESTFILE_IMAGE_PATH,
        preprocess=True,
    )
    assert isinstance(image_array, np.ndarray)


def test_load_image_no_preprocess():
    """

    :return:
    """
    image_array = load_image(
        imagepath=TESTFILE_IMAGE_PATH,
        preprocess=False,
    )
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

    input_obj = OCRInput.objects.create(
        file=upload_file,
        guid=guid,
    )
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
