import pandas as pd

class RTISLoaderError(Exception):
    pass

REQUIRED_COLUMNS = [
    "Logging Time",
    "Latitude",
    "Longitude",
    "Speed",
    "distFromSpeed",
]

COLUMN_MAP = {
    "Logging Time": "logging_time",
    "Latitude": "latitude",
    "Longitude": "longitude",
    "Speed": "speed",
    "distFromSpeed": "dist_from_speed",
}


def load_rtis_file(file):
    try:
        df = pd.read_csv(file)
    except Exception as e:
        raise RTISLoaderError(f"Failed to read RTIS file: {e}")

    # ---- validate columns ----
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise RTISLoaderError(f"Missing required columns: {missing}")

    # ---- normalize column names ----
    df = df.rename(columns=COLUMN_MAP)

    # ---- parse logging time ----
    df["logging_time"] = pd.to_datetime(
        df["logging_time"],
        errors="coerce",
    )

    df = df.dropna(subset=["logging_time", "latitude", "longitude", "speed"])
    df = df.sort_values("logging_time").reset_index(drop=True)

    return df
