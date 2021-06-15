"""
This module uses django post save signal to create a REST token for user
"""
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        obj = Token.objects.create(user=instance)
        return obj

class GenerateToken(APIView):
    """

    """

    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self):
        """
        Rest post method

        :return:
        """
        token_obj = create_auth_token(sender=settings.AUTH_USER_MODEL)
        if token_obj is not None:
            return Response(data={"token":token_obj.token}, status=status.HTTP_200_OK)



