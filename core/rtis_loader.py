import pandas as pd


class RTISLoaderError(Exception):
    pass


REQUIRED_COLUMNS = [
    "timestamp",
    "speed",
    "latitude",
    "longitude",
]


def load_rtis_file(file, start_time=None, end_time=None):
    try:
        filename = file.name.lower()

        if filename.endswith(".csv"):
            df = pd.read_csv(file)

        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(file, engine="openpyxl")

        else:
            raise RTISLoaderError("Unsupported file format")

    except Exception as e:
        raise RTISLoaderError(f"Failed to read RTIS file: {e}")

    # ---- validate columns ----
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise RTISLoaderError(f"Missing required columns: {missing}")

    # ---- parse timestamp ----
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])

    # ---- optional time filtering ----
    if start_time:
        df = df[df["timestamp"] >= start_time]
    if end_time:
        df = df[df["timestamp"] <= end_time]

    df = df.sort_values("timestamp").reset_index(drop=True)

    return df
