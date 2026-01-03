# core/violation_engine.py

import pandas as pd
from config.speed_rules import TRAIN_SPEED_RULES


class ViolationEngineError(Exception):
    pass


def _get_speed_window(
    rtis_df: pd.DataFrame,
    ref_time,
    lookback_seconds: int = 180,
):
    """
    Extract RTIS rows within a lookback window before ref_time.
    """
    start_time = ref_time - pd.Timedelta(seconds=lookback_seconds)
    return rtis_df[
        (rtis_df["timestamp"] >= start_time) &
        (rtis_df["timestamp"] <= ref_time)
    ]


def evaluate_speed_violations(
    rtis_df: pd.DataFrame,
    signal_df: pd.DataFrame,
    stop_events_df: pd.DataFrame,
    train_type: str,
):
    """
    Evaluate speed violations inferred from RED signal stops.

    Parameters
    ----------
    rtis_df : pd.DataFrame
        Clean RTIS data.
    signal_df : pd.DataFrame
        Direction-aware signal context.
    stop_events_df : pd.DataFrame
        RED signal stop events.
    train_type : str
        VANDE BHARAT | COACHING | FREIGHT

    Returns
    -------
    pd.DataFrame
        Violation events.
    """

    train_key = train_type.upper()
    if train_key not in TRAIN_SPEED_RULES:
        raise ViolationEngineError(f"Invalid train type: {train_type}")

    # Quick lookup by sequence
    signal_by_seq = signal_df.set_index("sequence_no")

    violations = []

    for _, stop in stop_events_df.iterrows():
        red_seq = stop["sequence_no"]
        red_time = stop["stop_start_time"]

        # ---------- SINGLE YELLOW ----------
        sy_seq = red_seq - 1
        if sy_seq in signal_by_seq.index:
            sy_signal = signal_by_seq.loc[sy_seq]

            window = _get_speed_window(rtis_df, red_time)
            if not window.empty:
                max_speed = window["speed"].max()
                allowed = TRAIN_SPEED_RULES[train_key]["SINGLE_YELLOW"]

                if max_speed > allowed:
                    violations.append({
                        "violation_type": "SINGLE_YELLOW_SPEED",
                        "signal_name": sy_signal["signal_name"],
                        "emoji": sy_signal["emoji"],
                        "allowed_speed": allowed,
                        "observed_speed": round(max_speed, 2),
                        "reference_time": red_time,
                    })

        # ---------- DOUBLE YELLOW ----------
        dy_seq = red_seq - 2
        if dy_seq in signal_by_seq.index:
            dy_signal = signal_by_seq.loc[dy_seq]

            window = _get_speed_window(rtis_df, red_time)
            if not window.empty:
                max_speed = window["speed"].max()
                allowed = TRAIN_SPEED_RULES[train_key]["DOUBLE_YELLOW"]

                if max_speed > allowed:
                    violations.append({
                        "violation_type": "DOUBLE_YELLOW_SPEED",
                        "signal_name": dy_signal["signal_name"],
                        "emoji": dy_signal["emoji"],
                        "allowed_speed": allowed,
                        "observed_speed": round(max_speed, 2),
                        "reference_time": red_time,
                    })

        # ---------- RED SIGNAL SANITY ----------
        if stop["stop_duration_sec"] <= 0:
            violations.append({
                "violation_type": "RED_SIGNAL_NO_STOP",
                "signal_name": stop["signal_name"],
                "emoji": stop["emoji"],
                "allowed_speed": 0,
                "observed_speed": None,
                "reference_time": red_time,
            })

    return pd.DataFrame(violations)
