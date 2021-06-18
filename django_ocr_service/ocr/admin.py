from django.contrib import admin
from .models import *


@admin.register(OCRInput)
class OCRInputAdmin(admin.ModelAdmin):
    pass


@admin.register(OCROutput)
class OCROutputAdmin(admin.ModelAdmin):
    pass
