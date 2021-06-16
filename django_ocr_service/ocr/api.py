"""

"""
from django_expiring_token.authentication import ExpiringTokenAuthentication
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .models import OCRInput
from .serializers import OCRInputSerializer


class GenerateOcrFromPDF(APIView):
    """ """

    authentication_classes = [ExpiringTokenAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        """
        Rest post method

        :return:
        """
        data = request.data.dict()
        ocr_input_serializer_obj = OCRInputSerializer(data=data)
        if ocr_input_serializer_obj.is_valid():
            model_obj = OCRInput.objects.create(**data)
            return Response(data={"response":model_obj.result_response}, status=status.HTTP_200_OK)
