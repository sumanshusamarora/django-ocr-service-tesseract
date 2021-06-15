"""

"""
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import OCRInputSerializer


class GenerateOcrFromPDF(APIView):
    """

    """

    authentication_classes = [TokenAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        """
        Rest post method

        :return:
        """
        serialized_model = OCRInputSerializer(request.data)
        if serialized_model.is_valid():
            pass