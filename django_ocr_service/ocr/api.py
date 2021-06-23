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
        if isinstance(request.data, QueryDict):
            data = request.data.dict()
        else:  # Handles test case when data is passed as dict
            data = request.data

        if not data.get("guid") and isinstance(data.get("guid"), str):
            logger.info("Invalid request, guid expected")
            return Response(
                data={"guid":"Invalid request, guid expected"}, status=status.HTTP_400_BAD_REQUEST
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
                output_objs = OCROutput.objects.filter(guid=input_obj).values("image_path", "text")
                response_dict = {obj["image_path"]: obj["text"] for obj in output_objs}

                if len(output_objs) == input_obj.page_count and input_obj.page_count > 0:
                    logger.info("OCR finished. Returning results")
                    stat = status.HTTP_200_OK
                else:
                    logger.info("OCR not finished. Returning unfinished results")
                    stat = status.HTTP_202_ACCEPTED


                return Response(
                    data=response_dict, status=stat
                )

class GenerateOCR_SNS(APIView):
    """
    View to enable POST method for text extraction
    """
    message_type_header = 'HTTP_X_AMZ_SNS_MESSAGE_TYPE'

    def post(self, request):
        """
        Rest post method

        :return:
        """
        if self.message_type_header in request.META:
            payload = json.loads(request.body.decode('utf-8'))

            logger.info(payload)

            message_type = request.META[self.message_type_header]

            if message_type == 'SubscriptionConfirmation':
                subscribe_url = payload.get('SubscribeURL')
                res = requests.get(subscribe_url)
                if res.status_code != 200:
                    logger.error('Failed to verify SNS Subscription', extra={
                        'verification_reponse': res.content,
                        'sns_payload': request.body,
                    })

                    return Response(data={'error':'Invalid verification:\n{0}'.format(res.content)},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                #{
                #    'Type': 'Notification', 'MessageId': '549ab8c1-b1e2-5437-81c1-e18d60b685b8',
                #    'TopicArn': 'arn:aws:sns:us-west-2:287646123622:uploaded-file-event-topic', 'Subject': 'input-record',
                #     'Message': '{\n    "id": "5d5da358-87b4-499d-bf95-74fc8e785387",\n    "source": "file-upload-handler",\n    "type": "file.upload.v1",\n    "data": {\n        "awsRegion": "us-west-2",\n        "bucket": "shore-dev-bucket",\n        "fileKey": "Initial%25201003%2520-%2520Alley.pdf",\n        "uri": "s3://shore-dev-bucket/Initial%25201003%2520-%2520Alley.pdf"\n    }\n}',
                #     'Timestamp': '2021-06-23T06:05:08.186Z', 'SignatureVersion': '1',
                #     'Signature': 'Ybsiw8FdXcTA7o/eQa4rrwV1xGaz7Ow4O3+CdbFBKDz8Cfv167OqRkLY0J1vN3e748/yNIT8FnMT58NQvBwPQvnbqOeWfj/C5rMRRxe/L9tE3yq20TIp/21jTXHUG6/GNyYZbhIsL5M3S7h0WPbNnI75MX6gf5KErpoBVXHoGKSzY9w+HQJ/Dnrr7UBtv7+Y2t0AlboN2sdupRZDF4R9F+pvPX/0hNXw+utvwpYfMUID/HlQcWme46OYHPc+ZcUnNZPhki9VAU82rviCQG1OYIk8Xlsx0eL4MMSSczaOI8DKhMk1Cm4vCjwCcnnGRbJQ4KBl0MpaR0U9YetRIIbizQ==',
                #     'SigningCertURL': 'https://sns.us-west-2.amazonaws.com/SimpleNotificationService-010a507c1833636cd94bdb98bd93083a.pem',
                #     'UnsubscribeURL': 'https://sns.us-west-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-west-2:287646123622:uploaded-file-event-topic:93a88c57-7447-432b-b900-37520423bccf'
                 #}
                # The actual body is in the 'Message' key of the
                # notification, which in turn is also a json encoded
                # string. Which needs to be parsed as json before
                # actually being useful.
                message = json.loads(payload.get('Message'))
                return self.handle_sns_message(message)

            return Response(status=status.HTTP_200_OK)

    def handle_sns_message(self, message):
        logger.info(message)
        model_obj = OCRInput.objects.create(cloud_storage_url_or_uri=message["data"]["uri"])
        return Response(data={"guid":model_obj.guid}, status=status.HTTP_200_OK)


