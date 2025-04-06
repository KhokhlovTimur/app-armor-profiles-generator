import os
from dotenv import load_dotenv
import logging

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LOGS_TIME_PATTERN = "%Y-%m-%d %H:%M:%S"

dotenv_path = os.path.join(PROJECT_ROOT, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

PROFILES_PATH = os.environ.get('APPARMOR_PROFILES_PATH', '/etc/apparmor.d')

logging.basicConfig(level=logging.INFO, filename="py_log.log",filemode="w",
                    format="%(asctime)s %(levelname)s %(message)s")