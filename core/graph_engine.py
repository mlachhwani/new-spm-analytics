# core/graph_engine.py

import plotly.graph_objects as go
import pandas as pd


# -------------------------------------------------
# Helper: signal annotation shapes
# -------------------------------------------------
def _add_signal_annotations(fig, signal_events, y_max):
    """
    Add vertical lines & labels for signals.
    """
    for sig in signal_events:
        fig.add_vline(
            x=sig["x"],
            line_width=1,
            line_dash="dot",
            line_color=sig.get("color", "gray"),
        )
        fig.add_annotation(
            x=sig["x"],
            y=y_max,
            text=sig["label"],
            showarrow=False,
            yanchor="bottom",
            font=dict(size=10),
        )


# -------------------------------------------------
# GRAPH 1 — Time vs Speed
# -------------------------------------------------
def plot_speed_vs_time(
    rtis_df: pd.DataFrame,
    signal_df: pd.DataFrame,
    stop_events_df: pd.DataFrame,
    violation_df: pd.DataFrame,
):
    """
    Master graph: Speed vs Time with signal & stop annotations.
    """

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

    # Signal annotations (RED stops only)
    signal_events = []
    for _, stop in stop_events_df.iterrows():
        signal_events.append({
            "x": stop["stop_start_time"],
            "label": f'{stop["signal_name"]} (RED)',
            "color": "red",
        })

    _add_signal_annotations(fig, signal_events, y_max)

    # Violation markers
    if not violation_df.empty:
        fig.add_trace(
            go.Scatter(
                x=violation_df["timestamp"],
                y=violation_df["observed_speed"],
                mode="markers",
                name="Violation",
                marker=dict(color="orange", size=8),
                text=violation_df["violation_type"],
            )
        )

    fig.update_layout(
        title="Speed vs Time",
        xaxis_title="Time",
        yaxis_title="Speed (kmph)",
        hovermode="x unified",
    )

    return fig


# -------------------------------------------------
# GRAPH 2 — Speed vs Signal Sequence (Section Progression)
# -------------------------------------------------
def plot_speed_vs_section_progression(
    rtis_df: pd.DataFrame,
    signal_df: pd.DataFrame,
):
    """
    Speed vs logical section progression using signal sequence.
    """

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

    # Signal sequence annotations
    signal_events = []
    for _, sig in signal_df.iterrows():
        signal_events.append({
            "x": sig["sequence_no"],
            "label": sig["signal_name"],
            "color": "blue",
        })

    _add_signal_annotations(fig, signal_events, y_max)

    fig.update_layout(
        title="Speed vs Section Progression",
        xaxis_title="Section Progress (logical)",
        yaxis_title="Speed (kmph)",
    )

    return fig


# -------------------------------------------------
# GRAPH 3 — Pre-stop ±2000 m analysis
# -------------------------------------------------
def plot_pre_stop_analysis(
    rtis_df: pd.DataFrame,
    stop_event: dict,
    distance_column: str = "dist_from_speed",
    window_m: int = 2000,
):
    """
    Speed vs distance before a RED signal stop.
    """

    stop_time = stop_event["stop_start_time"]

    # Use dist_from_speed as reference (as agreed)
    df = rtis_df.copy()

    # Identify stop index
    stop_idx = df[df["timestamp"] == stop_time].index.min()
    if pd.isna(stop_idx):
        return None

    # Slice window
    window_df = df.iloc[max(0, stop_idx - 500):stop_idx]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=window_df[distance_column],
            y=window_df["speed"],
            mode="lines",
            name="Speed (kmph)",
        )
    )

    fig.add_vline(
        x=window_df[distance_column].iloc[-1],
        line_width=2,
        line_color="red",
    )

    fig.update_layout(
        title=f'Pre-stop Speed Analysis – {stop_event["signal_name"]}',
        xaxis_title="Distance before signal (m)",
        yaxis_title="Speed (kmph)",
    )

    return fig
