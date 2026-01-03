# utils/crew_loader.py

import pandas as pd
from pathlib import Path


CREW_MASTER_PATH = Path("crew/crew_master.csv")


class CrewLoaderError(Exception):
    pass


def load_crew_master():
    if not CREW_MASTER_PATH.exists():
        raise CrewLoaderError("crew_master.csv not found")

    df = pd.read_csv(CREW_MASTER_PATH)

    required_cols = {"crew_id", "crew_role", "name", "group_cli"}
    if not required_cols.issubset(df.columns):
        raise CrewLoaderError(
            f"crew_master.csv must contain columns: {required_cols}"
        )

    return df


def get_crew_by_id(crew_id: str):
    df = load_crew_master()
    row = df[df["crew_id"] == crew_id]

    if row.empty:
        return None

    return {
        "crew_id": crew_id,
        "crew_role": row.iloc[0]["crew_role"],
        "name": row.iloc[0]["name"],
        "group_cli": row.iloc[0]["group_cli"],
    }
