"""
Collection of s3 utils to support OCR function.

This file will require major refactor if we even change the cloud platform
"""
from datetime import datetime
import logging
import os

import boto3
from s3urls import parse_url

logger = logging.getLogger(__name__)

if os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"):
    s3_client = boto3.client("s3")
    logger.info("AWS credentials set via environment variables")
else:
    raise ConnectionError("AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY variables not set")


def is_s3(url: str):
    """

    :param path: Path to file or dir
    :return:
    """
    try:
        parse_url_dict = parse_url(url)
        return parse_url_dict
    except:
        logger.info(f"{url} not a valid S3 url")

    return None


def delete_objects_from_s3(keys, bucket: str):
    """

    :param obj: Object path
    :param bucket: Bucket Name
    :param local_save_dir: Local directory to save file

    :return: Local filepath of object
    """
    if not isinstance(keys, list):
        keys = [keys]

    for obj in keys:
        try:
            s3_client.delete_object(Bucket=bucket, Key=obj)
            logger.info(f"Dropped s3 object {obj}")
        except Exception as exception:
            logger.error(exception)


def load_from_s3_and_save(obj: str, bucket: str, local_save_dir: str):
    """

    :param obj: Object path
    :param bucket: Bucket Name
    :param local_save_dir: Local directory to save file

    :return: Local filepath of object
    """
    obj_name = os.path.split(obj)[-1]
    save_path = os.path.join(local_save_dir, obj_name)

    try:
        s3_client.download_file(bucket, obj, save_path)
        logger.info(f"Downloaded s3 object {obj} and saved to {save_path}")
    except Exception as exception:
        logger.error(exception)
        return None

    return save_path


def upload_to_s3(
    path: str,
    bucket: str,
    prefix: str = None,
    key: str = None,
    append_datetime: bool = True,
):
    """

    :param path: Local filepath
    :param bucket: Bucket Name
    :param key: Key name if different from original

    :return: S3 filepath
    """
    if not os.path.isfile(path):
        raise ValueError(f"Invalid filepath {path}")

    if not key:
        key = os.path.split(path)[-1]

    if append_datetime:
        datetime_str = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        key = os.path.join(datetime_str, key)

    if prefix and prefix not in key:
        key = os.path.join(prefix, key)

    try:
        s3_client.upload_file(path, bucket, key)
        logger.info(f"Successfully uploaded file {path} to {key}")
    except Exception as exception:
        logger.error(exception)
        return None

    return key
