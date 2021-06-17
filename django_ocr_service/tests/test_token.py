"""
Tests for token.py
"""
from datetime import datetime, timezone

from django.contrib.auth.models import User
from django_expiring_token.models import ExpiringToken
import pytest

from ocr.token import create_auth_token, regenerated_expired_token
from .help_testutils import create_user_login_generate_token

pytestmark = pytest.mark.django_db()

class TestTokenGeneration:
    """

    """
    def setup_method(self):
        """

        :return:
        """
        self.django_client, self.user, self.token_true = create_user_login_generate_token()

    def test_create_auth_token(self):
        """

        :return:
        """
        token_expected = ExpiringToken.objects.get(user=self.user).key
        assert token_expected == self.token_true

    def test_create_auth_token_expired(self):
        """

        :return:
        """
        token_obj = ExpiringToken.objects.get(user=self.user)
        token_obj.expires = datetime.now(timezone.utc)
        token_obj.save()
        token_old = token_obj.key

        token_regenerated = create_auth_token(sender=User, instance=self.user)
        token_new = ExpiringToken.objects.get(user=self.user).key
        assert self.token_true == token_old and token_new == token_regenerated

    def test_create_auth_token_not_expired(self):
        """

        :return:
        """
        token_obj = ExpiringToken.objects.get(user=self.user)
        token_old = token_obj.key

        token_regenerated = create_auth_token(sender=User, instance=self.user)
        token_new = ExpiringToken.objects.get(user=self.user).key
        assert self.token_true == token_old == token_new == token_regenerated

    def test_regenerated_expired_token(self):
        """

        :return:
        """
        token_obj = ExpiringToken.objects.get(user=self.user)
        token_old = token_obj.key
        token_regenerated = regenerated_expired_token(token_obj).key
        token_new = ExpiringToken.objects.get(user=self.user).key
        assert self.token_true == token_old and token_new == token_regenerated

