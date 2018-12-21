import os
from datetime import datetime

import pandas as pd
import pandas.errors as pandas_errors
import pytz
from django.conf import settings

from box.utils.privacy_utils import hash_mac_address


def find_csv(csv_filename_prefix: str, target_dir: str = None) -> str:
    """As we specify only the airodump output file prefix, this helper function finds the whole filename."""
    if target_dir is None:
        target_dir = os.getcwd()
    files_in_directory = os.listdir(target_dir)
    files_in_directory.sort(reverse=True)
    for file in files_in_directory:
        if file.endswith("csv") and file.startswith(csv_filename_prefix):
            return os.path.join(target_dir, file)
    print(
        "%s WARNING: No CSV file found in %s with prefix %s"
        % (settings.TERM_LBL, target_dir, settings.AIRODUMP_FILE_PREFIX)
    )


def parse_airomon_datetime(airomon_dt: str) -> datetime:
    """Parse string used by airomon and also make timezone aware."""
    aileen_tz = pytz.timezone(settings.TIME_ZONE)
    try:
        dt: datetime = datetime.strptime(airomon_dt, "%Y-%m-%d %H:%M:%S")
        dt = dt.astimezone(aileen_tz)
    except ValueError:
        print(
            "%s Warning: could not parse datetime %s, using 1-1-1970 for this one!"
            % (settings.TERM_LBL, airomon_dt)
        )
        dt = datetime(1970, 1, 1, 1, 1, 1, tzinfo=aileen_tz)

    return dt


def get_devices_from_csv_df(csv_filename: str) -> pd.DataFrame:
    """Read in the data frame and use only the columns which contain device info"""
    try:
        df = pd.read_csv(csv_filename, header=None, usecols=range(0, 6))
    except (pandas_errors.EmptyDataError, ValueError):
        print(
            "%s WARNING: No data in airomon file %s or file not found"
            % (settings.TERM_LBL, csv_filename)
        )
        return pd.DataFrame(
            columns=[
                "device_id",
                "time_seen",
                "total_packets",
                "access_point_id",
                "device_power",
            ]
        )

    # find the row with which starts the device info
    header_row = df.loc[df[0] == "Station MAC"]
    # get the index of that row
    header_row_index = header_row.index[0]
    # delete all the information about the device stuff
    df = df[header_row_index:]
    # rename the columns so the have device headers
    df = df.rename(columns=df.iloc[0]).drop(df.index[0])
    # remove white spaces from column headers
    df.rename(columns=lambda x: x.strip(), inplace=True)
    # drop the unnecessary info
    df.drop("First time seen", 1, inplace=True)
    df.rename(
        columns={
            "Station MAC": "device_id",
            "Last time seen": "time_seen",
            "# packets": "total_packets",
            "BSSID": "access_point_id",
            "Power": "device_power",
        },
        inplace=True,
    )
    # remove all blank white space, do custom operations like hashing and parsing dates
    df["device_id"] = df["device_id"].map(lambda x: hash_mac_address(str(x).strip()))
    df["time_seen"] = df["time_seen"].map(
        lambda x: parse_airomon_datetime(str(x).strip())
    )
    df["total_packets"] = df["total_packets"].map(lambda x: str(x).strip())
    df["access_point_id"] = df["access_point_id"].map(lambda x: str(x).strip())
    df["device_power"] = df["device_power"].map(lambda x: str(x).strip())

    return df


def read_airodump_csv_and_return_df(airodump_dir: str, csv_filename_prefix: str):
    data_csv = find_csv(csv_filename_prefix, target_dir=airodump_dir)
    df = get_devices_from_csv_df(data_csv)
    return df


if __name__ == "__main__":
    print("main")
    print(
        read_airodump_csv_and_return_df(
            "/tmp/aileen_client_detection_data/", "full_airodump_file"
        )
    )
