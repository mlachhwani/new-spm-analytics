# core/violation_engine.py

import pandas as pd


class ViolationEngineError(Exception):
    """Custom exception for violation engine errors."""
    pass


# --- Speed rules (LOCKED) ---
SPEED_RULES = {
    "VANDE BHARAT": {
        "SINGLE_YELLOW": 90,
        "DOUBLE_YELLOW": 110,
    },
    "COACHING": {
        "SINGLE_YELLOW": 60,
        "DOUBLE_YELLOW": 100,
    },
    "FREIGHT": {
        "SINGLE_YELLOW": 40,
        "DOUBLE_YELLOW": 55,
    },
}


def _get_speed_window(
    rtis_df: pd.DataFrame,
    signal_time,
    lookback_seconds: int = 180,
):
    """
    Extract RTIS rows before a signal event for speed evaluation.
    """
    start_time = signal_time - pd.Timedelta(seconds=lookback_seconds)
    return rtis_df[
        (rtis_df["timestamp"] >= start_time) &
        (rtis_df["timestamp"] <= signal_time)
    ]


def evaluate_speed_violations(
    rti
