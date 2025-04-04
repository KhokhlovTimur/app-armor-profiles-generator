import datetime
import os.path
import re

from src.constants import PROJECT_ROOT

def join_project_root(*args):
    return os.path.join(PROJECT_ROOT, *args)

def load_stylesheet(file_name, elem):
    __path = join_project_root("resources", "styles/")
    with open(__path + file_name, "r") as file:
        elem.setStyleSheet(file.read())

def load_stylesheet_buttons(elem):
    load_stylesheet("buttons.qss", elem)

def get_profile_file_timestamp(profile_name: str) -> dict:
    result = {}
    profile_path = "/etc/apparmor.d/" + profile_name
    try:
        mtime = os.path.getmtime(profile_path)
        result["modified"] = datetime.datetime.fromtimestamp(mtime)

        if hasattr(os, "stat"):
            stat = os.stat(profile_path)
            if hasattr(stat, "st_birthtime"):
                result["created"] = datetime.datetime.fromtimestamp(stat.st_birthtime)
            elif hasattr(stat, "st_ctime"):
                result["created"] = datetime.datetime.fromtimestamp(stat.st_ctime)

    except FileNotFoundError:
        result["error"] = "Файл не найден"
    except Exception as e:
        result["error"] = str(e)

    return result

