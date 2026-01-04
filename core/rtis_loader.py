def load_rtis_file(file):
    import pandas as pd

    df = pd.read_csv(file)

    REQUIRED_COLUMNS = {
        "logging_time",
        "latitude",
        "longitude",
        "speed",
        "dist_from_speed",
    }

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # ---- parse logging time ----
    df["logging_time"] = pd.to_datetime(
        df["logging_time"],
        errors="coerce",
        dayfirst=True,
    )

    df = df.dropna(subset=[
        "logging_time",
        "latitude",
        "longitude",
        "speed",
        "dist_from_speed",
    ])

    df = df.sort_values("logging_time").reset_index(drop=True)

    return df
