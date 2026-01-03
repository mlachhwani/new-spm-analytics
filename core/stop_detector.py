# core/stop_detector.py

import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2


class StopDetectionError(Exception):
    """Custom exception for stop detection issues."""
    pass


# --- Helper: Haversine distance (meters) ---
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters

    lat1, lon1, lat2, lon2 = map(
        radians, [lat1, lon1, lat2, lon2]
    )

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
    Detect signal-based stops from RTIS data.

    Parameters
    ----------
    rtis_df : pd.DataFrame
        Output of rtis_loader (clean RTIS data).
    signal_df : pd.DataFrame
        Output of bui
