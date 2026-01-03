# core/section_loader.py

from pathlib import Path
import pandas as pd


SECTIONS_BASE_PATH = Path("sections")


class SectionLoaderError(Exception):
    pass


def load_section_data(section_name: str, direction: str):
    """
    Load section signal master (CSV only) and attach direction context.
    """

    direction = direction.upper()
    if direction not in {"UP", "DOWN"}:
        raise SectionLoaderError("Direction must be UP or DOWN")

    section_path = SECTIONS_BASE_PATH / section_name
    if not section_path.exists():
        raise SectionLoaderError(f"Section folder not found: {section_name}")

    signal_file = section_path / "signal_master.csv"
    if not signal_file.exists():
        raise SectionLoaderError(
            f"signal_master.csv missing in section: {section_name}"
        )

    try:
        signal_df = pd.read_csv(signal_file)
    except Exception as e:
        raise SectionLoaderError(f"Failed to read signal_master.csv: {e}")

    required_cols = {"Signal_Name", "Latitude", "Longitude"}
    if not required_cols.issubset(signal_df.columns):
        raise SectionLoaderError(
            f"signal_master.csv must contain columns: {required_cols}"
        )

    # Standardise
    signal_df = signal_df.copy()
    signal_df["Signal_Name"] = signal_df["Signal_Name"].astype(str)
    signal_df["Latitude"] = pd.to_numeric(signal_df["Latitude"], errors="coerce")
    signal_df["Longitude"] = pd.to_numeric(signal_df["Longitude"], errors="coerce")
    signal_df.dropna(subset=["Latitude", "Longitude"], inplace=True)

    return {
        "section_name": section_name,
        "direction": direction,
        "signal_master_df": signal_df.reset_index(drop=True),
    }
