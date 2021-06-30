"""
Tests to ensure common utils are doing whats expected
"""
import os
import random
import tempfile

from common_utils import (
    clean_local_storage,
    get_schema_name,
)


def test_get_schema_name(settings):
    """

    :param settings:
    :return:
    """
    schema_name_real = "testing_schema"
    settings.DATABASES["default"]["OPTIONS"] = {
        "options": f"-c search_path={schema_name_real}"
    }
    assert get_schema_name() == schema_name_real


def test_get_schema_name_no_schema(settings):
    """

    :param settings:
    :return:
    """
    settings.DATABASES["default"].pop("OPTIONS", None)
    assert not get_schema_name()


def test_clean_local_storage():
    """

    :return:
    """
    dirpath = "/tmp/ocr_inputs/"
    random_number = random.choice(list(range(6)))

    tempfiles = []
    for _ in range(random_number):
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, prefix="test", dir=dirpath
        )
        tempfiles.append(temp_file.name)

    added_files_exist_count = len([file for file in tempfiles if os.path.isfile(file)])
    clean_local_storage(dirpath, days=0)
    all_files_count = os.listdir(dirpath)

    assert added_files_exist_count == random_number and not len(all_files_count)
