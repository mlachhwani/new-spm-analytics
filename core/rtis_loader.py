# core/rtis_loader.py

import pandas as pd


REQUIRED_COLUMNS = {
    "latitude",
    "longitude",
    "speed",
    "logging_time",
    "dist_from_speed",
}


def load_rtis_file(file):
    df = pd.read_csv(file)

    # ---- Normalize column names ----
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # Handle RTIS-specific naming
    df.rename(
        columns={
            "logging_time": "logging_time",
            "loggingtime": "logging_time",
            "latitude": "latitude",
            "longitude": "longitude",
            "speed": "speed",
            "distfromspeed": "dist_from_speed",
        },
        inplace=True,
    )

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # ---- Parse time ----
    df["logging_time"] = pd.to_datetime(
        df["logging_time"],
        errors="coerce",
        dayfirst=True,
    )

    df = df.dropna(
        subset=["logging_time", "latitude", "longitude", "speed"]
    )

    df = df.sort_values("logging_time").reset_index(drop=True)

    return df
