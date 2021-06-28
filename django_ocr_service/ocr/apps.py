"""

"""
import logging

import arrow
from django.apps import AppConfig

logger = logging.getLogger(__name__)

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
        from django_q.tasks import schedule

        schedule_task_name = "CleanUpStorage"

        # Delete all existing storage clean task
        Schedule.objects.filter(name=schedule_task_name).delete()

        # Add new task to clean storage
        _ = schedule(
            name=schedule_task_name,
            func="ocr.ocr_utils.clean_local_storage",
            schedule_type=Schedule.DAILY,
            dirpath=settings.LOCAL_FILES_SAVE_DIR,
            days = settings.DELETE_OLD_IMAGES_DAYS,
            q_options={
                "ack_failure": True,
                "catch_up": False,
                "max_attempts": 1,
            },
            next_run=arrow.utcnow().shift(days=1).replace(hour=10, minute=0).datetime,
        )

        logger.info("Storage cleaning task schedule created!!!")

