"""django_ocr_service URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import logging

import arrow
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from ocr.api import (
    GenerateOCR,
    GenerateOCR_SNS,
    GetOCR,
    GenerateToken,
)

logger = logging.getLogger(__name__)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("api/get-token/", GenerateToken.as_view()),
    path("api/ocr/", GenerateOCR.as_view()),
    path("api/get-ocr/", GetOCR.as_view()),
    path("api/sns/ocr/", GenerateOCR_SNS.as_view()),
]



from django_q.models import Schedule
from django_q.tasks import schedule

schedule_task_name = "CleanUpStorage"

# Delete all existing storage clean task
try:
    Schedule.objects.filter(name=schedule_task_name).delete()

    # Add new task to clean storage
    _ = schedule(
        name=schedule_task_name,
        func="ocr.ocr_utils.clean_local_storage",
        schedule_type=Schedule.DAILY,
        dirpath=settings.LOCAL_FILES_SAVE_DIR,
        days=settings.DELETE_OLD_IMAGES_DAYS,
        q_options={
            "ack_failure": True,
            "catch_up": False,
            "max_attempts": 1,
        },
        next_run=arrow.utcnow().shift(days=1).replace(hour=10, minute=0).datetime,
    )

    logger.info("Storage cleaning task schedule created!!!")
except Exception as exception:
    logger.error(f"{schedule_task_name} task scheduling failed - {exception}")



