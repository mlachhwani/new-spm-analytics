# core/route_reference.py

from pathlib import Path
import pandas as pd


ROUTE_MASTER_DIR = Path("route_masters")
SECTION_ROUTE_MAP_FILE = Path("mappings/section_route_map.xlsx")


class RouteReferenceError(Exception):
    """Custom exception for route reference issues."""
    pass


def get_route_for_section(section_name: str):
    """
    Returns route metadata for a given section.

    Parameters
    ----------
    section_name : str
        Section selected by user (e.g. 'NGP-BSP').

    Returns
    -------
    dict
        {
            'route_name': str,
            'route_master_file': Path,
            'route_df': pd.DataFrame
        }
    """

    # 1️⃣ Load section → route mapping
    if not SECTION_ROUTE_MAP_FILE.exists():
        raise RouteReferenceError(
            "Section-to-route mapping file not found."
        )

    mapping_df = pd.read_excel(SECTION_ROUTE_MAP_FILE)

    required_cols = {"Section", "Route_Master"}
    if not required_cols.issubset(mapping_df.columns):
        raise RouteReferenceError(
            f"Mapping file must contain columns: {required_cols}"
        )

    # 2️⃣ Find route master for section
    row = mapping_df[mapping_df["Section"] == section_name]
    if row.empty:
        raise RouteReferenceError(
            f"No route mapping found for section: {section_name}"
        )

    route_master_filename = row.iloc[0]["Route_Master"]
    route_master_path = ROUTE_MASTER_DIR / route_master_filename

    if not route_master_path.exists():
        raise RouteReferenceError(
            f"Route master file not found: {route_master_filename}"
        )

    # 3️⃣ Load route master (reference only)
    try:
        route_df = pd.read_csv(route_master_path)
    except Exception as e:
        raise RouteReferenceError(
            f"Failed to load route master file: {e}"
        )

    # 4️⃣ Basic validation
    expected_cols = {"stationCode", "Latitude", "Longitude"}
    if not expected_cols.issubset(route_df.columns):
        raise RouteReferenceError(
            f"Route master must contain columns: {expected_cols}"
        )

    # 5️⃣ Clean & standardize
    route_df = route_df.copy()
    route_df.rename(
        columns={
            "stationCode": "station_code",
            "Latitude": "latitude",
            "Longitude": "longitude",
        },
        inplace=True,
    )

    route_df["latitude"] = pd.to_numeric(route_df["latitude"], errors="coerce")
    route_df["longitude"] = pd.to_numeric(route_df["longitude"], errors="coerce")
    route_df.dropna(subset=["latitude", "longitude"], inplace=True)

    return {
        "route_name": route_master_filename.replace(".csv", ""),
        "route_master_file": route_master_path,
        "route_df": route_df.reset_index(drop=True),
    }
