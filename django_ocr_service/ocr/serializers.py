from rest_framework import serializers
from .models import OCRInput


class OCRInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = OCRInput
        fields = ["cloud_storage_uri", "file", "ocr_config", "ocr_language"]
