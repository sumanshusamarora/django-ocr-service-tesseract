"""

"""
from apscheduler.schedulers.background import BackgroundScheduler
from django.apps import AppConfig
from django.conf import settings

scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)


class OcrConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ocr"

    def ready(self):
        """
        Initialize Django apscheduler here
        :return:
        """
        from django_apscheduler.jobstores import DjangoJobStore

        # Stop scheduler if already running
        try:
            scheduler.remove_jobstore("default")
            scheduler.remove_all_jobs()
            scheduler.stop()
        except:
            pass

        if not scheduler.state:
            scheduler.add_jobstore(DjangoJobStore(), "default")
            scheduler.start()
