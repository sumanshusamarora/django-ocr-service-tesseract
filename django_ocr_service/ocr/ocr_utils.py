"""
Common OCR utils
"""
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime
import os
import logging

import cv2
from django.conf import settings
import pandas as pd
import numpy as np
from pathlib import Path
from pdf2image import convert_from_path
import PyPDF2
from PyPDF2 import PdfFileReader
from pytesseract import image_to_data
from s3urls import parse_url

from . import (
    is_cloud_storage,
    upload_to_cloud_storage,
    load_from_cloud_storage_and_save,
    preprocess_image_for_ocr,
)

logger = logging.getLogger(__name__)


def is_pdf(filepath: str):
    """
    Check if a file is pdf or not
    :return:
    """
    try:
        doc = PdfFileReader(open(filepath, "rb"))
        logger.info(f"{filepath} is a pdf file.")
        return doc.numPages > 0
    except PyPDF2.utils.PdfReadError:
        logger.info(f"{filepath} is a NOT a pdf file.")

    return False


def is_image(filepath: str):
    """
    Check if a file is pdf or not
    :return:
    """
    try:
        _ = cv2.imread(filepath)
        return True
    except:
        logger.info(f"{filepath} is a NOT a image file.")

    return False


def purge_directory(dirpath: str):
    """
    Removes all filed in a directory
    :param dirpath:
    :return:
    """
    for filename in os.listdir(dirpath):
        file_path = os.path.join(dirpath, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print("Failed to delete %s. Reason: %s" % (file_path, e))


def download_locally_if_cloud_storage_path(filepath: str, save_dir: str):
    """

    :return:
    """
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    is_cloud_storage_path = is_cloud_storage(filepath)

    # If cloud storage path, download to local for processing
    if is_cloud_storage_path:
        cloud_storage_parse_dict = parse_url(filepath)
        local_path = load_from_cloud_storage_and_save(
            obj=cloud_storage_parse_dict["key"],
            bucket=cloud_storage_parse_dict["bucket"],
            local_save_dir=save_dir,
        )
    else:
        local_path = filepath

    return local_path


def pdf_to_image(
    pdf_path: str,
    save_images_to_cloud=True,
    prefix: str = "media",
    dpi: int = 300,
    output_folder: str = None,
    fmt: str = "png",
    cloud_storage="s3",
    use_threading_to_upload=False,
):
    """

    :param pdfs:
    :return:
    """
    cloud_storage_object_paths = []
    cloud_storage_objects_kw_args = []

    if not output_folder:
        output_folder = settings.LOCAL_FILES_SAVE_DIR

    Path(output_folder).mkdir(parents=True, exist_ok=True)
    # Remove all files from otuput_dir to keep the container space in limit

    images = convert_from_path(
        pdf_path, dpi=dpi, output_folder=output_folder, fmt=fmt, paths_only=True
    )
    if not isinstance(images, list):
        images = [images]

    if save_images_to_cloud:
        datetime_prefix = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
    else:
        datetime_prefix = None

    if cloud_storage == "s3":
        # Save to S3 if save_images_to_cloud is True
        if datetime_prefix:
            for image in images:
                kw_args = {
                    "path": image,
                    "bucket": settings.AWS_STORAGE_BUCKET_NAME,
                    "prefix": f"{prefix}/{datetime_prefix}",
                    "key": f"{os.path.split(pdf_path)[-1]}/{os.path.split(image)[-1]}",
                    "append_datetime": False,
                }
                cloud_storage_objects_kw_args.append(kw_args)

                if not use_threading_to_upload:
                    logger.info("Using threading to upload to cloud")
                    s3_path = upload_to_cloud_storage(**kw_args)
                    cloud_storage_object_paths.append(s3_path)
                else:
                    with ThreadPoolExecutor(
                        max_workers=None, thread_name_prefix="upload-images-to-cloud"
                    ) as executor:
                        executor.submit(upload_to_cloud_storage, kwargs=kw_args)

    if save_images_to_cloud and not len(cloud_storage_object_paths) == len(images):
        logger.warning(
            "Not all images got uploaded to cloud storage. You might be missing data"
        )
    else:
        logger.error("Other storage backends except S3 not implemented yet")
        raise NotImplementedError

    return images, cloud_storage_objects_kw_args


def generate_text_from_ocr_output(
    ocr_dataframe: pd.DataFrame, text_join_delimiter="\n", overlap=0.3
):
    """
    Reads OCR json output and generates ocr text from it
    """
    ocr_dataframe = ocr_dataframe[ocr_dataframe["height"] < ocr_dataframe["top"].max()]
    ocr_dataframe["bottom"] = ocr_dataframe["top"] + ocr_dataframe["height"]
    ignore_index = []
    line_indexes = []
    data_indexes = list(ocr_dataframe.index)
    ocr_dataframe["text"] = ocr_dataframe["text"].fillna("")
    for i in data_indexes:
        if (
            i not in ignore_index
            and ocr_dataframe["text"][i]
            and not ocr_dataframe["text"][i].strip() == ""
        ):
            this_row_bottom = ocr_dataframe["top"][i] + ocr_dataframe["height"][i]
            line_index = list(
                ocr_dataframe[
                    (~ocr_dataframe.index.isin(ignore_index))
                    & (
                        ocr_dataframe["top"]
                        <= this_row_bottom - (overlap * ocr_dataframe["height"][i])
                    )
                    & (
                        ocr_dataframe["bottom"]
                        >= ocr_dataframe["top"][i]
                        + (overlap * ocr_dataframe["height"][i])
                    )
                ]
                .sort_values(by="left")
                .index
            )
            ignore_index += line_index
            line_indexes.append(line_index)
    all_tops = ocr_dataframe[
        ocr_dataframe.index.isin([index_l[0] for index_l in line_indexes])
    ]["top"]
    line_indexes = [line_indexes[ind] for ind in np.argsort(all_tops)]
    text_list = [
        " ".join(
            [
                str(ocr_dataframe["text"][index])
                for index in line_index
                if str(ocr_dataframe["text"][index])
            ]
        )
        for line_index in line_indexes
    ]

    return text_join_delimiter.join(text_list)


def build_tesseract_ocr_config(tsv_or_txt="tsv"):
    """

    :return:
    """
    config_list = [tsv_or_txt]

    # OEM
    if settings.OCR_OEM:
        config_list.append(f"--oem {settings.OCR_OEM}")

    # PSM
    if settings.OCR_PSM:
        config_list.append(f"--psm {settings.OCR_PSM}")

    # TESSDATA DIR
    if settings.OCR_TESSDATA_DIR:
        config_list.append(f"--tessdata-dir {settings.OCR_TESSDATA_DIR}")

    ocr_config = " ".join(config_list) if config_list else None

    return ocr_config


def ocr_image(
    imagepath: str, preprocess: bool = True, ocr_config=None, ocr_engine="tesseract"
):
    """

    :param imagepath:
    :param preprocess:
    :return:
    """
    ocr_text = None

    if preprocess:
        image = preprocess_image_for_ocr(imagepath)
    else:
        image = cv2.imread(imagepath)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if ocr_engine == "tesseract":
        if not ocr_config:
            ocr_config = build_tesseract_ocr_config()

        ocr_language = settings.OCR_LANGUAGE

        image_data = image_to_data(
            image,
            config=(ocr_config),
            lang=ocr_language,
            output_type="data.frame",
        )
        ocr_text = generate_text_from_ocr_output(ocr_dataframe=image_data)

    return ocr_text
