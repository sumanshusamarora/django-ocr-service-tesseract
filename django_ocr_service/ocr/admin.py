from django.contrib import admin
from .models import *


@admin.register(OCRInput)
class OCRInputAdmin(admin.ModelAdmin):
    pass
