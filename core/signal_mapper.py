# core/signal_mapper.py

import pandas as pd


class SignalMappingError(Exception):
    pass


def _infer_asset_type_and_emoji(signal_name: str):
    name = signal_name.upper()

    if "L XING" in name:
        return "LEVEL_CROSSING", "🚧"
    if "NEU SEC" in name:
        return "NEUTRAL_SECTION", "⚡"
    if "HOME" in name:
        return "HOME", "🚦"
    if any(k in name for k in ["STARTER", "STR", "ADV"]):
        return "STARTER", "🚦"
    if any(k in name for k in ["DIST", "DNT"]):
        return "DISTANT", "🚦"

    return "SIGNAL", "🚦"


def build_signal_context(section_context: dict):
    """
    Build direction-aware signal context from single signal master CSV.
    """

    df = section_context["signal_master_df"].copy()
    direction = section_context["direction"]

    # Preserve physical order as sequence
    df["sequence_no"] = range(1, len(df) + 1)

    # Apply UP / DOWN logic
    if direction == "UP":
        max_seq = df["sequence_no"].max()
        df["sequence_no"] = max_seq - df["sequence_no"] + 1

    df.sort_values("sequence_no", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Infer asset type & emoji
    asset_types = []
    emojis = []

    for name in df["Signal_Name"]:
        asset, emoji = _infer_asset_type_and_emoji(name)
        asset_types.append(asset)
        emojis.append(emoji)

    df["asset_type"] = asset_types
    df["emoji"] = emojis

    # Final rename for consistency
    df.rename(
        columns={
            "Signal_Name": "signal_name",
            "Latitude": "latitude",
            "Longitude": "longitude",
        },
        inplace=True,
    )

    return df[
        [
            "sequence_no",
            "signal_name",
            "asset_type",
            "emoji",
            "latitude",
            "longitude",
        ]
    ]
