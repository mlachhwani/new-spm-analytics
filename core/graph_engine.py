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
def plot_speed_vs_time(rtis_df, signal_df):
    import plotly.graph_objects as go
    from core.signal_mapper import map_signals_to_time

    fig = go.Figure()

    # ---- Speed line ----
    fig.add_trace(
        go.Scatter(
            x=rtis_df["logging_time"],
            y=rtis_df["speed"],
            mode="lines",
            name="Speed (kmph)",
        )
    )

    y_max = rtis_df["speed"].max() + 10

    # ---- Map signals to time ----
    mapped_signals = map_signals_to_time(signal_df, rtis_df)

    for sig in mapped_signals:
        fig.add_vline(
            x=sig["logging_time"],
            line_dash="dot",
            line_color="grey",
            opacity=0.6,
        )

        fig.add_annotation(
            x=sig["logging_time"],
            y=y_max,
            text=f"{sig['emoji']} {sig['signal_name']}",
            showarrow=False,
            font=dict(size=10),
        )

    fig.update_layout(
        title="Speed vs Time with Signals",
        xaxis_title="Time",
        yaxis_title="Speed (kmph)",
        hovermode="x unified",
    )

    return fig

# -------------------------------------------------
# GRAPH 2 — Speed vs Section Progression
# -------------------------------------------------
def plot_speed_on_map(rtis_df, signal_df):
    import plotly.graph_objects as go

    fig = go.Figure()

    # ---- Train path ----
    fig.add_trace(
        go.Scattermapbox(
            lat=rtis_df["latitude"],
            lon=rtis_df["longitude"],
            mode="lines+markers",
            marker=dict(
                size=6,
                color=rtis_df["speed"],
                colorscale="Turbo",
                colorbar=dict(title="Speed (kmph)"),
            ),
            line=dict(width=3),
            text=[
                f"Speed: {s} kmph<br>Time: {t}"
                for s, t in zip(rtis_df["speed"], rtis_df["logging_time"])
            ],
            hoverinfo="text",
            name="Train Movement",
        )
    )

    # ---- Signal markers ----
    fig.add_trace(
        go.Scattermapbox(
            lat=signal_df["Latitude"],
            lon=signal_df["Longitude"],
            mode="markers+text",
            marker=dict(size=14, color="red"),
            text=[
                f"{e} {n}"
                for e, n in zip(signal_df["emoji"], signal_df["Signal_Name"])
            ],
            textposition="top center",
            hoverinfo="text",
            name="Signals",
        )
    )

    # ---- Layout ----
    fig.update_layout(
        title="Speed vs Section (Map View)",
        mapbox=dict(
            style="open-street-map",
            zoom=9,
            center=dict(
                lat=rtis_df["latitude"].mean(),
                lon=rtis_df["longitude"].mean(),
            ),
        ),
        margin=dict(l=0, r=0, t=40, b=0),
    )

    return fig

# -------------------------------------------------
# GRAPH 3 — Pre-stop ±2000 m
# -------------------------------------------------
def plot_pre_stop_analysis(
    rtis_df,
    stop_event,
    distance_col="distFromSpeed",
    window_m=2000,
):
    stop_time = stop_event["stop_start_time"]

    stop_idx = rtis_df[rtis_df["logging_time"] == stop_time].index.min()
    if pd.isna(stop_idx):
        return None

    # Walk backwards until 2000 m is covered
    cumulative = 0
    rows = []

    for i in range(stop_idx, -1, -1):
        cumulative += rtis_df.loc[i, distance_col]
        rows.append(i)
        if cumulative >= window_m:
            break

    window_df = rtis_df.loc[sorted(rows)]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=window_df[distance_col].cumsum(),
            y=window_df["speed"],
            mode="lines+markers",
            name="Speed",
        )
    )

    fig.add_vline(
        x=window_df[distance_col].cumsum().iloc[-1],
        line_color="red",
        line_width=2,
    )

    fig.update_layout(
        title=f"Pre-Stop Speed Analysis ⛔ {stop_event['signal_name']}",
        xaxis_title="Distance before stop (meters)",
        yaxis_title="Speed (kmph)",
    )

    return fig
