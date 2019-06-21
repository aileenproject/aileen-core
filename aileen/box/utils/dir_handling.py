import os
from tempfile import gettempdir

from django.conf import settings


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
