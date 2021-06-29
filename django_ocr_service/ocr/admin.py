"""
Admin site
"""
from django.contrib import admin
from django.contrib.admin.filters import SimpleListFilter

from .models import *

class OCRStatusFilter(SimpleListFilter):
    title = 'OCR Status'
    parameter_name = "guid"

    def get_ocr_status(self, obj):
        """

        :return:
        """
        output_count = OCROutput.objects.filter(guid=obj).count()
        if not output_count:
            return "Not Available"
        else:
            if output_count == obj.page_count:
                return "Finished"
            else:
                return "In Progress"

    def lookups(self, request, model_admin):
        """

        :param request:
        :param model_admin:
        :return:
        """
        return [
            ("Not Available", "Not Available"),
            ("In Progress", "In Progress"),
            ("Finished", "Finished"),
        ]

    def queryset(self, request, queryset):
        """

        :param request:
        :param queryset:
        :return:
        """
        if self.value():
            all_ocr_status_dict = {obj.guid: self.get_ocr_status(obj) for obj in queryset}
            return queryset.filter(guid__in=[key for key, value in all_ocr_status_dict.items() if value == self.value()])


@admin.register(OCRInput)
class OCRInputAdmin(admin.ModelAdmin):

    search_fields = ['guid', 'cloud_storage_uri', 'bucket_name', 'filename', 'ocr_config', 'result_response', 'modified_at']
    list_filter = ('bucket_name',
                   'ocr_config',
                   OCRStatusFilter,
                   )


@admin.register(OCROutput)
class OCROutputAdmin(admin.ModelAdmin):
    search_fields = ['guid__guid', 'image_path', 'modified_at']
