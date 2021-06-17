"""

"""
from django.conf import settings
from django.http.request import QueryDict
from django_expiring_token.authentication import ExpiringTokenAuthentication
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .models import OCRInput
from .serializers import OCRInputSerializer
from .token import create_auth_token


class GenerateToken(APIView):
    """
    API view to generate token
    """

    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Rest post method

        :return:
        """
        token = create_auth_token(
            sender=settings.AUTH_USER_MODEL, instance=request.user, created=True
        )
        if token:
            return Response(data={"token": token}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class GenerateOcrFromPDF(APIView):
    """ """

    authentication_classes = [ExpiringTokenAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        """
        Rest post method

        :return:
        """
        if isinstance(request.data, QueryDict):
            data = request.data.dict()
        else:  # Handles test case when data is passed as dict
            data = request.data

        ocr_input_serializer_obj = OCRInputSerializer(data=data)
        if ocr_input_serializer_obj.is_valid():
            try:
                model_obj = OCRInput.objects.create(**data)
                return Response(
                    data={"response": model_obj.result_response},
                    status=status.HTTP_200_OK,
                )
            except Exception as exception:
                return Response(
                    data={"Response": exception},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
        else:
            return Response(
                data=ocr_input_serializer_obj.errors, status=status.HTTP_400_BAD_REQUEST
            )
