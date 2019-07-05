import os
import logging
from tempfile import gettempdir
import importlib

from django.conf import settings


logger = logging.getLogger(__name__)


def build_tmp_dir_name(ensure_existence=True):
    dir_name = os.path.join(gettempdir(), settings.TMP_DIR_NAME)
    if ensure_existence and not os.path.exists(dir_name):
        os.mkdir(dir_name)
    return dir_name


def clean_tmp_files():
    tmp_path = build_tmp_dir_name()
    for tmp_file in [
        f for f in os.listdir(tmp_path) if f.startswith(settings.SENSOR_FILE_PREFIX)
    ]:
        os.remove("%s/%s" % (tmp_path, tmp_file))


def get_sensor():
    try:
        sensor = importlib.import_module(settings.SENSOR_MODULE)
    except Exception as e:
        raise Exception(
            "Cannot import sensor module %s: %s" % (settings.SENSOR_MODULE, str(e))
        )
    if type(sensor).__name__ != "module":
        raise Exception(
            "Sensor module found at %s is of type %s, not module!"
            % (settings.SENSOR_MODULE, type(sensor))
        )
    if not "start_sensing" in sensor.__dict__:
        raise Exception(
            "Need the start_sensing function to be available in %s."
            % settings.SENSOR_MODULE
        )
    if not "get_latest_reading_as_df" in sensor.__dict__:
        raise Exception(
            "Need the get_latest_reading_as_df function to be available in %s."
            % settings.SENSOR_MODULE
        )
    return sensor
