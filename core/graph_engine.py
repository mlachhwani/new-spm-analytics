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
def plot_speed_vs_time(rtis_df, signal_df, stop_events_df, violation_df):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=rtis_df["logging_time"],
            y=rtis_df["speed"],
            mode="lines",
            name="Speed (kmph)",
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
def plot_speed_vs_section_progression(rtis_df, signal_df):
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

    for _, sig in signal_df.iterrows():
        fig.add_vline(
            x=sig["sequence_no"],
            line_dash="dot",
            line_color="grey",
        )
        fig.add_annotation(
            x=sig["sequence_no"],
            y=y_max,
            text=sig["emoji"],
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
def plot_pre_stop_analysis(rtis_df, stop_event, distance_column="dist_from_speed"):
    stop_time = stop_event["stop_start_time"]

    stop_idx = rtis_df[rtis_df["logging_time"] == stop_time].index.min()
    if pd.isna(stop_idx):
        return None

    window_df = rtis_df.iloc[max(0, stop_idx - 500):stop_idx]

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
        title=f"Pre-stop Speed Analysis ⛔ {stop_event['signal_name']}",
        xaxis_title="Distance before stop (m)",
        yaxis_title="Speed (kmph)",
    )

    return fig
