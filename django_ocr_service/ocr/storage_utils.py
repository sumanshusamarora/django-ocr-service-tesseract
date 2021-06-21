"""
Storage utils
"""
from datetime import datetime
import logging
import os

from django.core.files.base import ContentFile
from django.conf import settings
from s3urls import parse_url

from django_ocr_service.custom_storage import CloudMediaStorage

logger = logging.getLogger(__name__)


def instantiate_custom_cloud_stroage(
    bucket: str = None, clear_default_location: bool = True
):
    """
    Simple instantiates cloud_storage and retun instance object
    :return:
    """
    cloud_storage = CloudMediaStorage()

    # Set location to top dir so we can get the full location from generate_cloud_storage_key method
    if clear_default_location:
        cloud_storage.location = ""

    # Change bucket name if it comes as part of input else use settings
    if bucket:
        cloud_storage.bucket._name = bucket

    return cloud_storage


def generate_cloud_storage_key(
    path: str,
    key: str,
    prefix: str = None,
    append_datetime: bool = True,
):
    """
    Generates a key for object to be uploaded
    :param path:
    :param key:
    :param prefix:
    :param append_datetime:
    :return:
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

    return key


def upload_to_cloud_storage(
    path: str,
    bucket: str = None,
    prefix: str = None,
    key: str = None,
    append_datetime: bool = True,
):
    """

    :param path:
    :param bucket:
    :param prefix:
    :param key:
    :param append_datetime:
    :return:
    """
    cloud_storage = instantiate_custom_cloud_stroage(
        bucket=bucket, clear_default_location=True
    )

    # prefix is none because it is already set as location
    key = generate_cloud_storage_key(
        path=path, key=key, prefix=prefix, append_datetime=append_datetime
    )

    try:
        with open(path, "rb") as infile:
            _ = cloud_storage.save(key, ContentFile(infile.read()))
        logger.info(f"Successfully uploaded file {path} to {key}")
    except Exception as exception:
        logger.error(exception)

    return cloud_storage.url(name=key)

def generate_cloud_object_url(key: str,
                              bucket: str = None,
                              ):
    """

    :return:
    """
    cloud_storage = instantiate_custom_cloud_stroage(
        bucket=bucket, clear_default_location=True
    )
    return cloud_storage.url(name=key)


def load_from_cloud_storage_and_save(
    key: str, bucket: str = None, local_save_dir: str = "/tmp"
):
    """

    :param obj: Object path
    :param bucket: Bucket Name
    :param local_save_dir: Local directory to save file

    :return: Local filepath of object
    """
    obj_name = os.path.split(key)[-1]
    save_path = os.path.join(local_save_dir, obj_name)

    cloud_storage = instantiate_custom_cloud_stroage(
        bucket=bucket, clear_default_location=True
    )
    try:
        with cloud_storage.open(key) as openfile:
            with open(save_path, "wb") as savefile:
                savefile.write(openfile.read())

        logger.info(f"Downloaded s3 object {key} and saved to {save_path}")
    except Exception as exception:
        logger.error(exception)
        return None

    return save_path


def delete_objects_from_cloud_storage(keys, bucket: str):
    """

    :param obj: Object path
    :param bucket: Bucket Name
    :param local_save_dir: Local directory to save file

    :return: Local filepath of object
    """
    if not isinstance(keys, list):
        keys = [keys]

    cloud_storage = instantiate_custom_cloud_stroage(
        bucket=bucket, clear_default_location=True
    )

    delete_count = 0
    for obj_key in keys:
        try:
            cloud_storage.delete(name=obj_key)
            delete_count += 1
            logger.info(
                f"Dropped s3 object {obj_key} from bucket {cloud_storage.bucket_name}"
            )
        except Exception as exception:
            logger.error(exception)

    return delete_count


def is_cloud_storage(url: str, storage_name: str = "s3"):
    """

    :param path: Path to file or dir
    :return:
    """
    if not storage_name in settings.ALLOWED_STORAGES:
        raise NotImplementedError("Only {} storage(s) implemented yet")

    try:
        if storage_name == "s3":
            parse_url_dict = parse_url(url)
            return parse_url_dict
        else:
            # This else block should have more code when other storages are supported
            raise NotImplementedError(f"{storage_name} not implemented yet")
    except:
        logger.info(f"{url} not a valid {storage_name} url")

    return None

