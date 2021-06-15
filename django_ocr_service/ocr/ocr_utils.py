"""
Collection of utils to support OCR
"""
from datetime import datetime
import logging
import os

from django.conf import settings
import boto3
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)

if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
    s3_client = boto3.client("S3")
    logger.info("AWS credentials set via environment variables")
else:
    raise ConnectionError("AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY variables not set")


def is_s3(path: str):
    """

    :param path: Path to file or dir
    :return:
    """
    if path.lower().startswith("s3://"):
        logger.info(f"{path} is an s3 path")
        return True

    return False


def delete_objects_from_s3(obj_path, bucket: str):
    """

    :param obj: Object path
    :param bucket: Bucket Name
    :param local_save_dir: Local directory to save file

    :return: Local filepath of object
    """
    if not isinstance(obj_path, list):
        obj_path = [obj_path]

    for obj in obj_path:
        try:
            s3_client.delete_object(Bucket=bucket, Key=obj)
            logger.info(f"Dropped s3 object {obj}")
        except Exception as exception:
            logger.error(exception)


def load_from_s3_and_save(obj: str, bucket: str, local_save_dir="/tmp"):
    """

    :param obj: Object path
    :param bucket: Bucket Name
    :param local_save_dir: Local directory to save file

    :return: Local filepath of object
    """
    obj_name = os.path.split(obj)
    save_path = os.path.join(local_save_dir, obj_name)

    try:
        s3_client.download_file(bucket, obj, save_path)
        logger.info(f"Downloaded s3 object {obj} and saved to {save_path}")
    except Exception as exception:
        logger.error(exception)
        return None

    return save_path


def upload_to_s3(path: str, bucket: str, prefix: str = None, key: str = None):
    """

    :param path: Local filepath
    :param bucket: Bucket Name
    :param key: Key name if different from original

    :return: S3 filepath
    """
    if not os.path.isfile(path):
        raise ValueError(f"Invalid filepath {path}")

    if not key:
        key = os.path.split(path)

    if prefix and prefix not in key:
        key = os.path.join(prefix, key)

    try:
        s3_client.upload_file(path, bucket, key)
        logger.info(f"Successfully uploaded file {path} to {key}")
    except Exception as exception:
        logger.error(exception)
        return None

    return key


def pdf_to_image(
    pdf_path: str,
    save_to_s3=True,
    bucket: str = None,
    drop_pdf=True,
    dpi: int = 300,
    output_folder: str = "/tmp",
    fmt: str = "png",
):
    """

    :param pdfs:
    :return:
    """
    datetime_str = datetime.utcnow().strftime("%Y-%M-%d-%H-%m-%S")
    is_s3_path = is_s3(pdf_path)

    if is_s3_path:
        local_path = load_from_s3_and_save(
            pdf_path, dpi=dpi, output_folder=output_folder, fmt=fmt
        )
    else:
        local_path = pdf_path

    images = convert_from_path(local_path)
    if not isinstance(images, list):
        images = [images]

    if save_to_s3 and not bucket:
        raise ValueError("Bucket name input required")

    s3_object_paths = []
    for image in images:
        if save_to_s3:
            s3_path = upload_to_s3(
                path=image.filename,
                bucket=bucket,
                prefix=f"{os.path.split(local_path)[-1]}/{datetime_str}",
                key=os.path.split(image.filename),
            )
            s3_object_paths.append(s3_path)
            os.remove(image.filename)

    if save_to_s3 and not len(s3_object_paths) == len(images):
        logger.warning("Not all images got uploaded to S3. You might be missing data")

    if drop_pdf:
        logger.info("Dropping input pdf")
        if s3_path:
            delete_objects_from_s3(obj_path=pdf_path, bucket=bucket)
        else:
            if os.path.isfile(pdf_path):
                os.remove(pdf_path)

    return s3_object_paths or [image.filename for image in images]
