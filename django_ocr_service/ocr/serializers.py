from rest_framework import serializers
from .models import OCRInput

class OCRInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = OCRInput
        fields = ["s3_path", "bucket_name"]
