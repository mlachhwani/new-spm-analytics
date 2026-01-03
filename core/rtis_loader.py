# core/rtis_loader.py

import pandas as pd


REQUIRED_COLUMNS = [
    "Device Id",
    "Logging Time",
    "Latitude",
    "Longitude",
    "Speed",
    "distFromSpeed",
]


class RTISLoaderError(Exception):
    """Custom exception for RTIS loading errors."""
    pass


def load_rtis_file(
    file_path_or_buffer,
    analysis_start_datetime,
    analysis_end_datetime
):
    """
    Load and clean RTIS data.

    Parameters
    ----------
    file_path_or_buffer : str or file-like
        Path to RTIS CSV/XLSX or uploaded file buffer (Streamlit).
    analysis_start_datetime : datetime
        User-selected analysis start time.
    analysis_end_datetime : datetime
        User-selected analysis end time.

    Returns
    -------
    pd.DataFrame
        Clean, time-filtered RTIS dataframe.
    """

    # 1️⃣ Load file (CSV or Excel)
    try:
        if str(file_path_or_buffer).lower().endswith(".csv"):
            df = pd.read_csv(file_path_or_buffer)
        else:
            df = pd.read_excel(file_path_or_buffer)
    except Exception as e:
        raise RTISLoaderError(f"Failed to read RTIS file: {e}")

    # 2️⃣ Validate required columns
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise RTISLoaderError(
            f"RTIS file missing required columns: {missing_cols}"
        )

    # 3️⃣ Keep only required columns
    df = df[REQUIRED_COLUMNS].copy()

    # 4️⃣ Standardize column names
    df.rename(
        columns={
            "Device Id": "device_id",
            "Logging Time": "timestamp",
            "Latitude": "latitude",
            "Longitude": "longitude",
            "Speed": "speed",
            "distFromSpeed": "dist_from_speed",
        },
        inplace=True,
    )

    # 5️⃣ Datatype conversions
    try:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    except Exception as e:
        raise RTISLoaderError(f"Invalid timestamp format: {e}")

    for col in ["latitude", "longitude", "speed", "dist_from_speed"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 6️⃣ Drop invalid rows
    df.dropna(
        subset=["timestamp", "latitude", "longitude", "speed"],
        inplace=True
    )

    # 7️⃣ Physical sanity checks
    df = df[
        (df["latitude"].between(-90, 90)) &
        (df["longitude"].between(-180, 180)) &
        (df["speed"] >= 0)
    ]

    # 8️⃣ Time window filtering
    df = df[
        (df["timestamp"] >= analysis_start_datetime) &
        (df["timestamp"] <= analysis_end_datetime)
    ]

    if df.empty:
        raise RTISLoaderError(
            "No RTIS data available in the selected time window."
        )

    # 9️⃣ Device ID handling
    device_counts = df["device_id"].value_counts()
    primary_device_id = device_counts.idxmax()
    df = df[df["device_id"] == primary_device_id]

    # 10️⃣ Sort & deduplicate
    df.sort_values("timestamp", inplace=True)
    df.drop_duplicates(subset=["timestamp"], keep="first", inplace=True)

    df.reset_index(drop=True, inplace=True)

    return df
