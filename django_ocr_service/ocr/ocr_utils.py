"""
Common OCR utils
"""
from datetime import datetime
import os
import logging
import time
import uuid

import arrow
import cv2
from django.conf import settings
import multiprocessing
import numpy as np
import pandas as pd
from pathlib import Path
from pdf2image import convert_from_path
from PyPDF2 import PdfFileReader
from pytesseract import image_to_data
from s3urls import parse_url

from . import (
    generate_cloud_storage_key,
    is_cloud_storage,
    load_from_cloud_storage_and_save,
    preprocess_image_for_ocr,
    upload_to_cloud_storage,
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
    except:
        logger.info(f"{filepath} is a NOT a pdf file.")

    return False


def is_image(filepath: str):
    """
    Check if a file is pdf or not
    :return:
    """
    try:
        image_array = cv2.imread(filepath)
        if image_array is not None:
            return True
    except:
        pass

    logger.info(f"{filepath} is a NOT a image file.")
    return False

def clean_local_storage(dirpath: str, days: int = 2):
    """
    Method to clean local storage
    :return:
    """
    if not os.path.isdir(dirpath):
        raise NotADirectoryError

    os_walker = os.walk(dirpath)
    now = time.time()

    deleted = 0
    for dir, subdirs, file_list in os_walker:
        for file in file_list:
            if file:
                filepath = os.path.join(dir, file)
                if os.stat(filepath).st_mtime < now - (days * 24 * 60 * 60):
                    os.remove(filepath)
                    deleted+=1

    logger.info(f"Removed {deleted} files from {dirpath}")


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
            key=cloud_storage_parse_dict["key"],
            bucket=cloud_storage_parse_dict["bucket"],
            local_save_dir=save_dir,
        )
    else:
        local_path = filepath

    return local_path


def pdf_to_image(
    pdf_path: str,
    output_folder: str = None,
    save_images_to_cloud=True,
    prefix: str = "media",
    dpi: int = 300,
    fmt: str = "png",
    cloud_storage: str = "s3",
    use_async_to_upload: bool = False,
    append_datetime: bool = True,
):
    """

    :param pdfs:
    :return:
    """
    cloud_storage_object_paths = []
    cloud_storage_objects_kw_args = []

    if not prefix:
        prefix = ""

    if append_datetime:
        logging.info("Append date is True, adding datetime to prefix")
        prefix = f"{prefix}/{datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')}"

    if not output_folder:
        output_folder = settings.LOCAL_FILES_SAVE_DIR

    logger.info(f"Directory {output_folder} set for image saving")

    Path(output_folder).mkdir(parents=True, exist_ok=True)
    # Remove all files from output_dir to keep the container space in limit
    logger.info(f"Converting pdf to images using {multiprocessing.cpu_count()} threads")
    images = convert_from_path(
        pdf_path,
        dpi=dpi,
        output_folder=output_folder,
        fmt=fmt,
        paths_only=True,
        thread_count=multiprocessing.cpu_count(),
    )
    logger.info(f"{len(images)} images stored at {output_folder}")

    if not isinstance(images, list):
        images = [images]

    if save_images_to_cloud:
        if cloud_storage == "s3":
            logger.info("Using S3 cloud storage backend")
            # Save to S3 if save_images_to_cloud is True
            for image in images:
                kw_args = {
                    "path": image,
                    "bucket": settings.AWS_STORAGE_BUCKET_NAME,
                    "prefix": prefix,
                    "key": f"{os.path.split(pdf_path)[-1]}/{os.path.split(image)[-1]}",
                    "append_datetime": False,
                }

                cloud_storage_objects_kw_args.append(kw_args)

                logging.info("Starting image upload")

                if use_async_to_upload:
                    from django_q.models import Schedule
                    from django_q.tasks import schedule
                    logging.info("Uploading to cloud through background job")
                    try:
                        schedule(
                            func='ocr.storage_utils.upload_to_cloud_storage',
                            name=f"{kw_args['key']}-{uuid.uuid4().hex}"[:99],
                            schedule_type=Schedule.ONCE,
                            path=image,
                            bucket=settings.AWS_STORAGE_BUCKET_NAME,
                            prefix=prefix,
                            key=f"{os.path.split(pdf_path)[-1]}/{os.path.split(image)[-1]}",
                            append_datetime=False,
                            next_run=arrow.utcnow().shift(seconds=1).datetime,
                        )

                        cloud_storage_path = generate_cloud_storage_key(
                            path=kw_args["path"],
                            key=kw_args["key"],
                            prefix=kw_args["prefix"],
                            append_datetime=kw_args["append_datetime"],
                        )
                    except Exception as exception:
                        logger.error("Error adding background task to upload image to cloud")
                        logger.error(exception)
                        use_async_to_upload = False

                # Else condition is not used on purpose since we want to move the job to happen in
                # sync fashion if job scheduling fails
                if not use_async_to_upload:
                    logging.info("Uploading to cloud in a blocking thread")
                    cloud_storage_path = upload_to_cloud_storage(**kw_args)

                cloud_storage_object_paths.append(cloud_storage_path)

            if not len(cloud_storage_object_paths):
                logger.warning("Image upload failed")

            elif not len(cloud_storage_object_paths) == len(images):
                logger.warning("Not all images got uploaded to cloud storage")
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
    ocr_dataframe["text"].fillna("", inplace=True)
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


def build_tesseract_ocr_config(
    tsv_or_txt="tsv", oem: int = None, psm: int = None, tessdata_dir: str = None
):
    """

    :return:
    """
    config_list = [tsv_or_txt]

    # OEM
    if oem:
        config_list.append(f"--oem {oem}")
    elif settings.OCR_OEM:
        config_list.append(f"--oem {settings.OCR_OEM}")

    # PSM
    if psm:
        config_list.append(f"--psm {psm}")
    elif settings.OCR_PSM:
        config_list.append(f"--psm {settings.OCR_PSM}")

    # TESSDATA DIR
    if tessdata_dir:
        config_list.append(f"--tessdata-dir {tessdata_dir}")
    elif settings.OCR_TESSDATA_DIR:
        config_list.append(f"--tessdata-dir {settings.OCR_TESSDATA_DIR}")

    ocr_config = " ".join(config_list) if config_list else None

    return ocr_config

def ocr_image(
    imagepath: str,
    preprocess: bool = True,
    ocr_config: str=None,
    ocr_engine: str="tesseract",
    inputocr_instance=None,
    **kwargs,
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
        logger.info(f"OCR results received for {imagepath}")
        ocr_text = generate_text_from_ocr_output(ocr_dataframe=image_data)

        if inputocr_instance is not None:
            logger.info(f"Saving OCR output to DB for {imagepath}")
            kwargs["ocr_output_model"].objects.create(
                guid=inputocr_instance,
                image_path=kwargs["cloud_imagepath"],
                text=ocr_text,
            )
            logger.info(f"OCR output saved to DB for {imagepath}")

    else:
        raise NotImplementedError(
            "No other OCR engine except tesseract is supported currently"
        )

    return ocr_text
