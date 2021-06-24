"""

"""
import json
import logging

from django.conf import settings
from django.http.request import QueryDict
from django_expiring_token.authentication import ExpiringTokenAuthentication
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
import requests

from .models import OCRInput, OCROutput
from .serializers import OCRInputSerializer
from .token import create_auth_token

logger = logging.getLogger(__name__)


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


class GenerateOCR(APIView):
    """
    View to enable POST method for text extraction
    """

    authentication_classes = [ExpiringTokenAuthentication]
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

        if not data:
            return Response(
                data={"Error": "File input required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ocr_input_serializer_obj = OCRInputSerializer(data=data)

        if ocr_input_serializer_obj.is_valid(raise_exception=True):
            logger.info("Serializer is valid")
            try:
                model_obj = OCRInput.objects.create(**data)
                return Response(
                    data={"guid": model_obj.guid},
                    status=status.HTTP_200_OK,
                )
            except Exception as exception:
                return Response(
                    data={"Response": exception},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
        else:
            logger.info("Serializer is invalid")
            return Response(
                data=ocr_input_serializer_obj.errors, status=status.HTTP_400_BAD_REQUEST
            )


class GetOCR(APIView):
    """
    Get OCR files and text by guid
    """

    authentication_classes = [ExpiringTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """

        :param request:
        :return:
        """
        if isinstance(request.query_params, QueryDict):
            data = request.query_params.dict()
        else:  # Handles test case when data is passed as dict
            data = request.query_params

        if not data.get("guid") and isinstance(data.get("guid"), str):
            logger.info("Invalid request, guid expected")
            return Response(
                data={"guid": "Invalid request, guid expected"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            try:
                input_obj = OCRInput.objects.get(guid=data.get("guid"))
            except:
                logger.info(f"Invalid guid {data.get('guid')}")
                return Response(
                    data={"guid": "Invalid guid"}, status=status.HTTP_400_BAD_REQUEST
                )
            else:
                output_objs = OCROutput.objects.filter(guid=input_obj).values(
                    "image_path", "text"
                )
                response_dict = {obj["image_path"]: obj["text"] for obj in output_objs}

                if (
                    len(output_objs) == input_obj.page_count
                    and input_obj.page_count > 0
                ):
                    logger.info("OCR finished. Returning results")
                    stat = status.HTTP_200_OK
                else:
                    logger.info("OCR not finished. Returning unfinished results")
                    stat = status.HTTP_202_ACCEPTED

                return Response(data=response_dict, status=stat)


class GenerateOCR_SNS(APIView):
    """
    View to enable POST method for text extraction
    """

    message_type_header = "HTTP_X_AMZ_SNS_MESSAGE_TYPE"

    def post(self, request):
        """
        Rest post method

        :return:
        """
        if self.message_type_header in request.META:
            payload = json.loads(request.body.decode("utf-8"))
            logger.info(f"Payload - {payload}")
            message_type = request.META[self.message_type_header]
            if message_type == "SubscriptionConfirmation":
                logger.info(f"It is a subscription record")
                subscribe_url = payload.get("SubscribeURL")
                res = requests.get(subscribe_url)
                if res.status_code != 200:
                    logger.error(
                        "Failed to verify SNS Subscription",
                        extra={
                            "verification_reponse": res.content,
                            "sns_payload": request.body,
                        },
                    )

                    return Response(
                        data={
                            "error": "Invalid verification:\n{0}".format(res.content)
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                message = json.loads(payload.get("Message"))
                logger.info(f"Message received on SNS topic - {message}")
                return self.handle_sns_message(message)

            return Response(status=status.HTTP_200_OK)

    def handle_sns_message(self, message):
        model_obj = OCRInput.objects.create(
            guid=message["id"], cloud_storage_uri=message["data"]["uri"]
        )
        return Response(data={"guid": model_obj.guid}, status=status.HTTP_200_OK)
