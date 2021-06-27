"""

"""
import logging
import os
import time

import arrow
from django.apps import AppConfig

logger = logging.getLogger(__name__)

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
    for dir, subdirs, file in os_walker:
        if file:
            filepath = os.path.join(dir, file)
            if os.stat(filepath).st_mtime < now - (days * 24 * 60 * 60):
                os.remove(filepath)
                deleted+=1

    logger.info(f"Removed {deleted} files from {dirpath}")

class OcrConfig(AppConfig):
    """

    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "ocr"

    def ready(self):
        """
        Schedule the task to
        :return:
        """
        from django.conf import settings
        from django_q.models import Schedule

        schedule_task_name = "CleanUpStorage"

        # Delete all existing storage clean task
        Schedule.objects.filter(name=schedule_task_name).delete()

        kw_args = {
            "dirpath": settings.LOCAL_FILES_SAVE_DIR,
            "days": settings.DELETE_OLD_IMAGES_DAYS,
        }

        # Add new task to clean storage
        _ = Schedule.objects.create(
            name=schedule_task_name,
            func=clean_local_storage,
            schedule_type=Schedule.DAILY,
            kwargs=kw_args,
            next_run=arrow.utcnow().shift(days=1).replace(hour=10, minute=0).datetime,
        )

        logger.info("Storage cleaning task schedule created!!!")

