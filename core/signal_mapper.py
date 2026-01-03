# core/signal_mapper.py

import pandas as pd


class SignalMappingError(Exception):
    """Custom exception for signal mapping issues."""
    pass


def resolve_signal_coordinates(
    signal_master_df: pd.DataFrame,
    ohe_df: pd.DataFrame,
    fsd_df: pd.DataFrame = None
):
    """
    Resolve final coordinates for each signal.
    Priority:
    1. FSD coordinates (if available)
    2. OHE coordinates (fallback)

    Returns
    -------
    pd.DataFrame
        Signal dataframe with resolved latitude & longitude.
    """

    resolved_rows = []

    for _, row in signal_master_df.iterrows():
        signal_name = row["SIGNAL_NAME"]
        station = row["STATION"]
        signal_type = row["SIGNAL_TYPE"]
        ohe_id = row["OHE_ID"]
        sequence_no = row["SEQUENCE_NO"]

        lat, lon = None, None

        # 1️⃣ Try FSD
        if fsd_df is not None and "SIGNAL_NAME" in fsd_df.columns:
            match = fsd_df[fsd_df["SIGNAL_NAME"] == signal_name]
            if not match.empty:
                lat = match.iloc[0]["LATITUDE"]
                lon = match.iloc[0]["LONGITUDE"]

        # 2️⃣ Fallback to OHE
        if lat is None:
            ohe_match = ohe_df[ohe_df["OHE_ID"] == ohe_id]
            if not ohe_match.empty:
                lat = ohe_match.iloc[0]["LATITUDE"]
                lon = ohe_match.iloc[0]["LONGITUDE"]

        if lat is None or lon is None:
            raise SignalMappingError(
                f"Coordinates not found for signal: {signal_name}"
            )

        resolved_rows.append({
            "signal_name": signal_name,
            "station": station,
            "signal_type": signal_type,
            "sequence_no": sequence_no,
            "latitude": lat,
            "longitude": lon,
        })

    return pd.DataFrame(resolved_rows)


def apply_direction(signal_df: pd.DataFrame, direction: str):
    """
    Apply UP / DOWN direction logic to signal sequence numbers.

    Parameters
    ----------
    signal_df : pd.DataFrame
        Signal dataframe with sequence_no.
    direction : str
        'UP' or 'DOWN'

    Returns
    -------
    pd.DataFrame
        Direction-adjusted signal dataframe.
    """

    direction = direction.upper()
    if direction not in {"UP", "DOWN"}:
        raise SignalMappingError("Direction must be 'UP' or 'DOWN'.")

    df = signal_df.copy()

    if direction == "UP":
        max_seq = df["sequence_no"].max()
        df["sequence_no"] = max_seq - df["sequence_no"] + 1

    # DOWN → natural order
    df.sort_values("sequence_no", inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


def build_signal_context(
    section_context: dict
):
    """
    Build final, direction-aware signal context for a section.

    Parameters
    ----------
    section_context : dict
        Output from load_section_data()

    Returns
    -------
    pd.DataFrame
        Fully resolved, ordered signal dataframe.
    """

    signal_master_df = section_context["signal_master_df"]
    ohe_df = section_context["ohe_df"]
    fsd_df = section_context["fsd_df"]
    direction = section_context["direction"]

    # 1️⃣ Resolve coordinates
    signal_df = resolve_signal_coordinates(
        signal_master_df=signal_master_df,
        ohe_df=ohe_df,
        fsd_df=fsd_df,
    )

    # 2️⃣ Apply direction
    signal_df = apply_direction(signal_df, direction)

    return signal_df
