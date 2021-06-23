"""
Common utils to be utilized by application
"""
from django.conf import settings


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
