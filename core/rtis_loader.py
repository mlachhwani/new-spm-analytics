import pandas as pd

class RTISLoaderError(Exception):
    pass

REQUIRED_COLUMNS = [
    "Latitude",
    "Longitude",
    "Speed",
    "distFromSpeed",
]

COLUMN_MAP = {
    "Latitude": "latitude",
    "Longitude": "longitude",
    "Speed": "speed",
    "distFromPrevLatLng": "dist_from_prev",
    "distFromSpeed": "dist_from_speed",
}


def load_rtis_file(file):
    try:
        df = pd.read_csv(file)
    except Exception as e:
        raise RTISLoaderError(f"Failed to read RTIS file: {e}")

    # ---- normalize columns ----
    df = df.rename(columns=COLUMN_MAP)

    missing = [v for v in COLUMN_MAP.values() if v not in df.columns]
    if missing:
        raise RTISLoaderError(f"Missing required columns: {missing}")

    # ---- basic cleaning ----
    df = df.dropna(subset=["latitude", "longitude", "speed"])
    df = df.reset_index(drop=True)

    return df
