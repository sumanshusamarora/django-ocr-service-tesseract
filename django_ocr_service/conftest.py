import pytest
from django.db import connections
from django.core.management import call_command

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from django.conf import settings

def run_sql(sql, database):
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


def get_schema_name():
    schema_name = None
    db_options = settings.DATABASES["default"].get("OPTIONS")
    db_options_opt = db_options.get("options")
    if db_options is None or db_options_opt is None:
        return

    search_path_index = db_options_opt.find("search_path")
    if search_path_index > 0:
        schema_name = (
            db_options_opt[search_path_index + len("search_path") + 1 :]
            .replace("=", "")
            .strip()
        )
    return schema_name


@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker, django_db_createdb):
    orig_db_name = "postgres"  # settings.DATABASES["default"]["NAME"]
    if settings.DATABASES["default"]["TEST"]["NAME"]:
        test_db_name = settings.DATABASES["default"]["TEST"]["NAME"]
    else:
        test_db_name = "test_" + settings.DATABASES["default"]["NAME"]
    settings.DATABASES["default"]["NAME"] = test_db_name
    run_sql("DROP DATABASE IF EXISTS %s" % test_db_name, database=orig_db_name)
    run_sql("CREATE DATABASE %s" % test_db_name, database=orig_db_name)
    schema_name = get_schema_name()
    run_sql("CREATE SCHEMA IF NOT EXISTS %s" % schema_name, database=test_db_name)

    with django_db_blocker.unblock():
        call_command("migrate", "--verbosity=0")

    yield

    for connection in connections.all():
        connection.close()

    try:
        run_sql("DROP DATABASE %s" % test_db_name, database=orig_db_name)
    except:
        pass
