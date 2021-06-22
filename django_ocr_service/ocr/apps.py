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
        scheduler.add_jobstore(DjangoJobStore(), "default")
        scheduler.start()
