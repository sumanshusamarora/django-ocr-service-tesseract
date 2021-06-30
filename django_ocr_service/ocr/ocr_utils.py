"""
Common OCR utils
"""
from datetime import datetime
import os
import logging
import warnings

import checksum
import cv2
from django.conf import settings
import multiprocessing
import numpy as np
import pandas as pd
from pandas.core.common import SettingWithCopyWarning
from pathlib import Path
from pdf2image import convert_from_path
from PyPDF2 import PdfFileReader
from pytesseract import image_to_data
from s3urls import parse_url

import ocr
from . import (
    generate_cloud_storage_key,
    is_cloud_storage,
    load_from_cloud_storage_and_save,
    preprocess_image_for_ocr,
    upload_to_cloud_storage,
)

warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)
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


def generate_save_image_kwargs(
    images: list,
    pdf_path: str,
    append_datetime: bool = True,
    prefix: str = "media",
    cloud_storage="s3",
):
    """

    :param images:
    :param pdf_path:
    :param prefix:
    :param cloud_storage:
    :return:
    """
    cloud_storage_objects_kw_args = []

    if not prefix:
        prefix = ""

    if append_datetime:
        logging.info("Append date is True, adding datetime to prefix")
        prefix = f"{prefix}/{datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')}"

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
    else:
        raise NotImplementedError("No other storage backend implemented except s3")

    return cloud_storage_objects_kw_args


def save_images(kw_args, use_async_to_upload: bool = False):
    """

    :param kw_args:
    :param use_async_to_upload:
    :return:
    """

    if not isinstance(kw_args, list):
        kw_args = [kw_args]

    logging.info("Starting image upload")
    cloud_storage_object_paths = []
    for kw_arg in kw_args:
        if use_async_to_upload:
            from django_q.tasks import async_task
            logging.info("Uploading to cloud through async task")
            try:
                # Below async task may already be a async thread but starting another thread to do this job would
                # increase the speed of async OCR thread which is our prime motive. The upload is completely
                # alright to happen in a separate thread too
                async_task(
                    func="ocr.storage_utils.upload_to_cloud_storage",
                    group="Upload",
                    **kw_arg,
                )

                cloud_storage_path = generate_cloud_storage_key(
                    path=kw_arg["path"],
                    key=kw_arg["key"],
                    prefix=kw_arg["prefix"],
                    append_datetime=kw_arg["append_datetime"],
                )
            except Exception as exception:
                logger.error("Error adding background task to upload image to cloud")
                logger.error(exception)
                use_async_to_upload = False

        # Else condition is not used on purpose since we want to move the job to happen in
        # sync fashion if job scheduling fails
        if not use_async_to_upload:
            logging.info("Uploading to cloud in a blocking thread")
            cloud_storage_path = upload_to_cloud_storage(**kw_arg)
            logging.info("File uploaded to cloud in a blocking thread")

        cloud_storage_object_paths.append(cloud_storage_path)

    # Logging to show image upload status
    if not len(cloud_storage_object_paths):
        logger.warning("Image upload failed")
    elif not len(cloud_storage_object_paths) == len(kw_args):
        logger.warning("Not all images got uploaded to cloud storage")

    return cloud_storage_object_paths


def pdf_to_image(
    pdf_path: str, output_folder: str = None, dpi: int = 300, fmt: str = "png"
):
    """

    :param pdf_path:
    :param output_folder:
    :param dpi:
    :param fmt:
    :return:
    """
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

    return images


def generate_text_from_ocr_output(
    ocr_dataframe: pd.DataFrame, text_join_delimiter="\n", overlap=0.3
):
    """
    Reads OCR json output and generates ocr text from it
    """
    ocr_dataframe = ocr_dataframe[ocr_dataframe["height"] < ocr_dataframe["top"].max()]
    ocr_dataframe.loc[:, "bottom"] = (
        ocr_dataframe.loc[:, "top"] + ocr_dataframe.loc[:, "height"]
    )
    ignore_index = []
    line_indexes = []
    data_indexes = list(ocr_dataframe.index)
    ocr_dataframe.loc[:, "text"] = ocr_dataframe.loc[:, "text"].copy().fillna("")
    for i in data_indexes:
        if (
            i not in ignore_index
            and ocr_dataframe["text"][i]
            and not ocr_dataframe["text"][i].strip() == ""
        ):
            this_row_bottom = (
                ocr_dataframe.loc[i, "top"] + ocr_dataframe.loc[i, "height"]
            )
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


def get_obj_if_already_present(checksum):
    """

    :param checksum:
    :return:
    """
    objs = ocr.models.OCROutput.objects.filter(checksum=checksum)

    if objs:
        logger.info(
            f"Existing results found in OCROutput model for file having checksum {checksum}"
        )
        return objs.latest("modified_at")

    logger.info(
        f"No results found in OCROutput model for file having checksum {checksum}"
    )
    return None


def load_image(imagepath, preprocess: bool = True):
    """

    :param preprocess:
    :return:
    """
    if preprocess:
        logger.info("Preprocessing image")
        image = preprocess_image_for_ocr(imagepath)
    else:
        logger.info("Preprocessing is set to False, reading image")
        image = cv2.imread(imagepath)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    return image


def ocr_using_tesseract_engine(image, ocr_config=None):
    """

    :param image:
    :param ocr_config:
    :return:
    """
    logger.info("Tesseract selected as OCR engine")
    if not ocr_config:
        ocr_config = build_tesseract_ocr_config()

    ocr_language = settings.OCR_LANGUAGE
    logger.info(f"OCR Config - {ocr_config}, OCR Language - {ocr_language}")

    image_data = image_to_data(
        image,
        config=(ocr_config),
        lang=ocr_language,
        output_type="data.frame",
    )
    ocr_text = generate_text_from_ocr_output(ocr_dataframe=image_data)

    return ocr_text


def ocr_image(
    imagepath: str,
    preprocess: bool = True,
    ocr_config: str = None,
    ocr_engine: str = "tesseract",
    inputocr_guid: str = None,
    cloud_imagepath: str = None,
    save_images_to_cloud: bool = True,
    save_to_cloud_kw_args=None,
    use_async_to_upload: bool = True,
):
    """

    :param imagepath:
    :param preprocess:
    :param ocr_config:
    :param ocr_engine:
    :param inputocr_guid:
    :param cloud_imagepath:
    :param save_images_to_cloud
    :param save_to_cloud_kw_args
    :return:
    """
    if save_images_to_cloud and not save_to_cloud_kw_args:
        raise ValueError(
            "Save kw_args dictionary input requires when save images input is True"
        )

    ocr_text = None

    image_checksum = checksum.get_for_file(imagepath)

    output_obj = get_obj_if_already_present(image_checksum)

    if output_obj:
        cloud_imagepath = output_obj.image_path
        ocr_text = output_obj.text
    else:
        image = load_image(imagepath=imagepath, preprocess=preprocess)

        if ocr_engine == "tesseract":
            logger.info("Tesseract selected as OCR engine")
            ocr_text = ocr_using_tesseract_engine(image=image, ocr_config=ocr_config)
            logger.info(f"OCR results received for {imagepath}")
        else:
            raise NotImplementedError(
                "No other OCR engine except tesseract is supported currently"
            )

        # If checksum is unique and save to cloud is True, upload image to cloud storage
        if save_images_to_cloud:
            save_images(save_to_cloud_kw_args, use_async_to_upload)

    if inputocr_guid and ocr_text:
        inputocr_instance = ocr.models.OCRInput.objects.get(guid=inputocr_guid)
        logger.info(f"Saving OCR output to DB for {imagepath}")
        _ = ocr.models.OCROutput.objects.create(
            guid=inputocr_instance,
            image_path=cloud_imagepath,
            text=ocr_text,
            checksum=image_checksum,
        )
        logger.info(f"OCR output saved to DB for {imagepath}")

    return ocr_text
