"""
Common OCR utils
"""
import os
import logging

from django.conf import settings
from pdf2image import convert_from_path
import PyPDF2
from PyPDF2 import PdfFileReader
from s3urls import parse_url

from .s3_storage_utils import (
    is_s3,
    upload_to_s3,
    load_from_s3_and_save,
    delete_objects_from_s3,
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
        return doc.numPages() > 0
    except PyPDF2.utils.PdfReadError:
        logger.info(f"{filepath} is a NOT a pdf file.")

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


def pdf_to_image(
    pdf_path: str,
    save_images_to_cloud=True,
    prefix: str = "media",
    drop_pdf=True,
    dpi: int = 300,
    output_folder: str = "/tmp",
    fmt: str = "png",
    cloud_storage="s3",
):
    """

    :param pdfs:
    :return:
    """
    # Remove all files from otuput_dir to keep the container space in limit
    purge_directory(output_folder)

    if cloud_storage == "s3":
        # Check if s3 link which in all cases it should be since backend storage is s3 too
        is_s3_path = is_s3(pdf_path)

        # If s3 path, download to local for processing
        if is_s3_path:
            s3_parse_dict = parse_url(pdf_path)
            local_path = load_from_s3_and_save(
                obj=s3_parse_dict["key"], bucket=s3_parse_dict["bucket"]
            )
        else:
            local_path = pdf_path

        images = convert_from_path(
            local_path, dpi=dpi, output_folder=output_folder, fmt=fmt, paths_only=True
        )
        if not isinstance(images, list):
            images = [images]

        s3_object_paths = []
        for image in images:
            if save_images_to_cloud:
                s3_path = upload_to_s3(
                    path=image,
                    bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    prefix=prefix,
                    key=os.path.split(image),
                )
                s3_object_paths.append(s3_path)
                os.remove(image)

        if save_images_to_cloud and not len(s3_object_paths) == len(images):
            logger.warning(
                "Not all images got uploaded to S3. You might be missing data"
            )

        if drop_pdf:
            logger.info("Dropping input pdf")
            if s3_path:
                delete_objects_from_s3(
                    keys=s3_parse_dict["key"], bucket=s3_parse_dict["bucket"]
                )
    else:
        logger.error("Other storage backends except S3 not implemented yet")
        raise NotImplementedError

    return s3_object_paths or [images]
