# core/graph_engine.py

import plotly.graph_objects as go
import pandas as pd


# -------------------------------------------------
# Helper — infer station spans
# -------------------------------------------------
def _infer_station_spans(signal_df: pd.DataFrame):
    spans = []
    current_home = None

    for _, row in signal_df.iterrows():
        if row["asset_type"] == "HOME":
            current_home = row
        elif row["asset_type"] == "STARTER":
            if current_home is not None:
                spans.append((current_home, row))
                current_home = None
            else:
                spans.append((row, row))

    if current_home is not None:
        spans.append((current_home, current_home))

    return spans


# -------------------------------------------------
# GRAPH 1 — Speed vs Time
# -------------------------------------------------
def plot_speed_vs_time(
    rtis_df: pd.DataFrame,
    signal_df: pd.DataFrame,
    stop_events_df: pd.DataFrame,
    violation_df: pd.DataFrame,
):
    fig = go.Figure()

    # Speed trace
    fig.add_trace(
        go.Scatter(
            x=rtis_df["timestamp"],
            y=rtis_df["speed"],
            mode="lines",
            name="Speed (kmph)",
        )
    )

    y_max = rtis_df["speed"].max() + 10

    # Station spans (visual only)
    spans = _infer_station_spans(signal_df)
    for start, end in spans:
        fig.add_vrect(
            x0=start["sequence_no"],
            x1=end["sequence_no"],
            fillcolor="lightgrey",
            opacity=0.15,
            layer="below",
            line_width=0,
        )

    # Signal annotations
    for _, sig in signal_df.iterrows():
        fig.add_annotation(
            x=sig["sequence_no"],
            y=y_max,
            text=f'{sig["emoji"]} {sig["signal_name"]}',
            showarrow=False,
            font=dict(size=10),
        )

    # Stop markers
    for _, stop in stop_events_df.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[stop["stop_start_time"]],
                y=[0],
                mode="markers",
                marker=dict(color="red", size=10),
                name="Stop",
                text=f'⛔ {stop["signal_name"]}',
            )
        )

    # Violation markers
    if not violation_df.empty:
        fig.add_trace(
            go.Scatter(
                x=violation_df["reference_time"],
                y=violation_df["observed_speed"],
                mode="markers",
                marker=dict(color="orange", size=9),
                name="Violation",
                text="⚠️ Speed Violation",
            )
        )

    fig.update_layout(
        title="Speed vs Time (Signal & Station Aware)",
        xaxis_title="Time",
        yaxis_title="Speed (kmph)",
        hovermode="x unified",
    )

    return fig


# -------------------------------------------------
# GRAPH 2 — Speed vs Section Progression
# -------------------------------------------------
def plot_speed_vs_section_progression(
    rtis_df: pd.DataFrame,
    signal_df: pd.DataFrame,
):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=rtis_df.index,
            y=rtis_df["speed"],
            mode="lines",
            name="Speed (kmph)",
        )
    )

    y_max = rtis_df["speed"].max() + 10

    # Signal markers
    for _, sig in signal_df.iterrows():
        fig.add_vline(
            x=sig["sequence_no"],
            line_dash="dot",
            line_color="grey",
        )
        fig.add_annotation(
            x=sig["sequence_no"],
            y=y_max,
            text=f'{sig["emoji"]}',
            showarrow=False,
            font=dict(size=12),
        )

    fig.update_layout(
        title="Speed vs Section Progression",
        xaxis_title="Section Progress (Logical)",
        yaxis_title="Speed (kmph)",
    )

    return fig


# -------------------------------------------------
# GRAPH 3 — Pre-stop ±2000 m
# -------------------------------------------------
def plot_pre_stop_analysis(
    rtis_df: pd.DataFrame,
    stop_event: dict,
    distance_column: str = "dist_from_speed",
):
    stop_time = stop_event["stop_start_time"]

    stop_idx = rtis_df[rtis_df["timestamp"] == stop_time].index.min()
    if pd.isna(stop_idx):
        return None

    window_df = rtis_df.iloc[max(0, stop_idx - 500):stop_idx]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=window_df[distance_column_]()_
