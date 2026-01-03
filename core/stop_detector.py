# core/stop_detector.py

import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2


class StopDetectionError(Exception):
    pass


# --- Helper: Haversine distance (meters) ---
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def detect_signal_stops(
    rtis_df: pd.DataFrame,
    signal_df: pd.DataFrame,
    stop_speed_threshold: float = 0.0,
    min_stop_duration_sec: int = 10,
    max_signal_radius_m: int = 150,
):
    """
    Detect signal-based stops (RED inference).

    Stops near LEVEL_CROSSING or NEUTRAL_SECTION are ignored
    for RED / violation logic.
    """

    df = rtis_df.copy()
    df["is_stopped"] = df["speed"] <= stop_speed_threshold

    stop_groups = []
    current = []

    # 1️⃣ Group consecutive stopped points
    for _, row in df.iterrows():
        if row["is_stopped"]:
            current.append(row)
        else:
            if current:
                stop_groups.append(pd.DataFrame(current))
                current = []

    if current:
        stop_groups.append(pd.DataFrame(current))

    stop_events = []

    # Assets that must NOT be treated as RED signals
    EXCLUDED_ASSETS = {"LEVEL_CROSSING", "NEUTRAL_SECTION"}

    for stop_df in stop_groups:
        start_time = stop_df["logging_time"].iloc[0]
        end_time = stop_df["logging_time"].iloc[-1]
        duration_sec = (end_time - start_time).total_seconds()

        if duration_sec < min_stop_duration_sec:
            continue

        mean_lat = stop_df["latitude"].mean()
        mean_lon = stop_df["longitude"].mean()

        nearest_signal = None
        min_distance = np.inf

        # 2️⃣ Find nearest asset
        for _, sig in signal_df.iterrows():
            dist = haversine_distance(
                mean_lat, mean_lon,
                sig["latitude"], sig["longitude"]
            )
            if dist < min_distance:
                min_distance = dist
                nearest_signal = sig

        # 3️⃣ Validate proximity
        if nearest_signal is None or min_distance > max_signal_radius_m:
            continue

        # 4️⃣ Exclude non-signal assets
        if nearest_signal["asset_type"] in EXCLUDED_ASSETS:
            continue

        stop_events.append({
            "sequence_no": nearest_signal["sequence_no"],
            "signal_name": nearest_signal["signal_name"],
            "asset_type": nearest_signal["asset_type"],
            "emoji": nearest_signal["emoji"],
            "stop_start_time": start_time,
            "stop_end_time": end_time,
            "stop_duration_sec": duration_sec,
            "distance_to_asset_m": round(min_distance, 2),
        })

    return pd.DataFrame(stop_events)
