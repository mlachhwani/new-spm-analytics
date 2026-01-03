# core/section_loader.py

from pathlib import Path
import pandas as pd


SECTIONS_BASE_PATH = Path("sections")


class SectionLoaderError(Exception):
    """Custom exception for section loading errors."""
    pass


def load_section_data(section_name: str, direction: str):
    """
    Load all backend datasets for a given section and attach direction context.

    Parameters
    ----------
    section_name : str
        Section selected by user (e.g. 'NGP-BSP').
    direction : str
        'UP' or 'DOWN'

    Returns
    -------
    dict
        {
            'section_name': str,
            'direction': str,
            'ohe_df': pd.DataFrame,
            'signal_master_df': pd.DataFrame,
            'fsd_df': pd.DataFrame or None
        }
    """

    # 1️⃣ Validate direction
    direction = direction.upper()
    if direction not in {"UP", "DOWN"}:
        raise SectionLoaderError(
            "Direction must be either 'UP' or 'DOWN'."
        )

    # 2️⃣ Resolve section folder
    section_path = SECTIONS_BASE_PATH / section_name
    if not section_path.exists():
        raise SectionLoaderError(
            f"Section folder not found: {section_name}"
        )

    # 3️⃣ Required files
    ohe_file = section_path / "ohe_coordinates.xlsx"
    signal_file = section_path / "signal_master.xlsx"
    fsd_file = section_path / "fsd_signals.xlsx"

    if not ohe_file.exists():
        raise SectionLoaderError(
            f"OHE coordinates file missing in section: {section_name}"
        )

    if not signal_file.exists():
        raise SectionLoaderError(
            f"Signal master file missing in section: {section_name}"
        )

    # 4️⃣ Load datasets
    try:
        ohe_df = pd.read_excel(ohe_file)
        signal_master_df = pd.read_excel(signal_file)
        fsd_df = pd.read_excel(fsd_file) if fsd_file.exists() else None
    except Exception as e:
        raise SectionLoaderError(
            f"Failed to load section files: {e}"
        )

    # 5️⃣ Minimal validation (structure only)
    required_ohe_cols = {"OHE_ID", "Latitude", "Longitude"}
    required_signal_cols = {
        "Station",
        "Signal_Name",
        "Signal_Type",
        "OHE_ID",
        "Sequence_No",
    }

    if not required_ohe_cols.issubset(ohe_df.columns):
        raise SectionLoaderError(
            f"OHE file must contain columns: {required_ohe_cols}"
        )

    if not required_signal_cols.issubset(signal_master_df.columns):
        raise SectionLoaderError(
            f"Signal master must contain columns: {required_signal_cols}"
        )

    # 6️⃣ Standardize column names (upper for consistency)
    ohe_df.columns = ohe_df.columns.str.upper()
    signal_master_df.columns = signal_master_df.columns.str.upper()
