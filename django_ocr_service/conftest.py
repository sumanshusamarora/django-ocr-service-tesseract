"""
Conftest to enable testing
"""
import os

import boto3
from django.conf import settings
from django.core.management import call_command
from django.db import connections
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import pytest

from common_utils import get_schema_name
from ocr.storage_utils import delete_objects_from_cloud_storage


def run_sql(sql, database):
    """

    :param sql:
    :param database:
    :return:
    """
    conn = psycopg2.connect(
        database=database,
        user=settings.DATABASES["default"]["USER"],
        password=settings.DATABASES["default"]["PASSWORD"],
        host=settings.DATABASES["default"]["HOST"],
        port=settings.DATABASES["default"]["PORT"],
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(sql)
    conn.close()


@pytest.yield_fixture(scope="session")
def django_db_setup(django_db_blocker, django_db_createdb):
    """

    :param django_db_blocker:
    :param django_db_createdb:
    :return:
    """
    orig_db_name = "postgres"  # settings.DATABASES["default"]["NAME"]
    if settings.DATABASES["default"].get("TEST") and settings.DATABASES["default"].get("TEST").get("NAME"):
        test_db_name = settings.DATABASES["default"]["TEST"]["NAME"]
    else:
        test_db_name = "test_" + settings.DATABASES["default"]["NAME"]
    settings.DATABASES["default"]["NAME"] = test_db_name
    run_sql("DROP DATABASE IF EXISTS %s" % test_db_name, database=orig_db_name)
    run_sql("CREATE DATABASE %s" % test_db_name, database=orig_db_name)
    schema_name = get_schema_name()
    run_sql('CREATE SCHEMA IF NOT EXISTS "%s"' % schema_name, database=test_db_name)

    with django_db_blocker.unblock():
        call_command("migrate", "--verbosity=0")

    yield

    for connection in connections.all():
        connection.close()

    try:
        run_sql("DROP DATABASE %s" % test_db_name, database=orig_db_name)
    except:
        pass

def pytest_sessionstart(session):
    prefix = "test_data"
    settings.MEDIA_ROOT = os.path.join(settings.BASE_DIR, prefix)

def pytest_sessionfinish(session, exitstatus):
    prefix = "test_data"
    s3_client = boto3.client('s3')
    bucket = settings.CLOUD_STORAGE_BUCKET_NAME
    response = s3_client.list_objects_v2(Bucket=settings.CLOUD_STORAGE_BUCKET_NAME, Prefix=prefix)

    for object in response['Contents']:
        s3_client.delete_object(Bucket=bucket, Key=object['Key'])
