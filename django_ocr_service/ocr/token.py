"""
This module uses django post save signal to create a REST token for user
"""
from datetime import datetime, timedelta, timezone
import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_expiring_token.models import ExpiringToken

logger = logging.getLogger(__name__)


def regenerated_expired_token(token_object):
    """
    Regenerates the expired token

    :param token_object:
    :return:
    """
    token_object.delete()
    token_object = ExpiringToken.objects.create(user=token_object.user)
    logger.info(f"Token regeranted for user {token_object.user}")
    return token_object


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, **kwargs):
    """
    Creates/Extracts auth token for a logged in user

    :param sender: Sending model in case of signal
    :param instance: User model instance
    :param kwargs:
    :return: Token
    """
    obj, created = ExpiringToken.objects.get_or_create(user=instance)
    if created:
        logger.info(f"New token created for user {obj.user}")
    else:
        if obj.expires < datetime.now(timezone.utc) - timedelta(minutes=1):
            logger.info("Token already expired. Regenerating!")
            obj = regenerated_expired_token(token_object=obj)
        else:
            logger.info(f"Token already exists for user {obj.user}")
    return obj.key

