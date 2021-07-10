"""
Common utils to be utilized by application
"""
import logging
import os
import time

from django.conf import settings
from django.core.files.storage import FileSystemStorage

logger = logging.getLogger(__name__)


def get_schema_name(db_name: str = "default"):
    """
    Returns db schema for db_name input in settings.DATABASES
    :param db_name:
    :return:
    """
    schema_name = None
    db_options = settings.DATABASES[db_name].get("OPTIONS")

    if db_options:
        db_options_opt = db_options.get("options")

    if db_options is None or db_options_opt is None:
        return

    search_path_index = db_options_opt.find("search_path")
    if search_path_index > 0:
        schema_name = (
            db_options_opt[search_path_index + len("search_path") + 1 :]
            .replace("=", "")
            .strip()
        )
    return schema_name


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
                    deleted += 1

    logger.info(f"Removed {deleted} files from {dirpath}")
