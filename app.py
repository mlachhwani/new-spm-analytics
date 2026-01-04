import streamlit as st
import pandas as pd
from datetime import datetime

from core.rtis_loader import load_rtis_file
from core.section_loader import load_section_data
from core.signal_mapper import build_signal_context
from core.stop_detector import detect_signal_stops
from core.violation_engine import evaluate_speed_violations
from core.graph_engine import (
    plot_speed_vs_time,
    plot_speed_on_map,
    plot_pre_stop_analysis,
)
from core.report_engine import generate_pdf_report
from utils.crew_loader import get_crew_by_id

st.set_page_config(
    page_title="RTIS Driving Behaviour Analysis",
    layout="wide",
)

# ---------------- SIDEBAR ----------------
st.sidebar.title("🚆 Analysis Inputs")

train_number = st.sidebar.text_input("Train Number")
loco_number = st.sidebar.text_input("Loco Number")

train_type = st.sidebar.selectbox(
    "Train Type",
    ["VANDE BHARAT", "COACHING", "FREIGHT"]
)

direction = st.sidebar.selectbox(
    "Direction",
    ["DOWN", "UP"]
)

max_speed = st.sidebar.selectbox(
    "Max Permissible Speed (kmph)",
    list(range(30, 135, 5))
)

section = st.sidebar.selectbox(
    "Section",
    ["NGP-RIG"]
)

analysis_start = st.sidebar.datetime_input(
    "Analysis Start Date & Time",
    value=datetime.now()
)

analysis_end = st.sidebar.datetime_input(
    "Analysis End Date & Time",
    value=datetime.now()
)

st.sidebar.markdown("---")
st.sidebar.subheader("👨‍✈️ Crew Details")

lp_id = st.sidebar.text_input("LP ID")
alp_id = st.sidebar.text_input("ALP ID")

lp = get_crew_by_id(lp_id) if lp_id else None
alp = get_crew_by_id(alp_id) if alp_id else None

if lp:
    st.sidebar.success(f"LP: {lp['name']} ({lp['group_cli']})")
elif lp_id:
    st.sidebar.warning("LP not found")

if alp:
    st.sidebar.success(f"ALP: {alp['name']} ({alp['group_cli']})")
elif alp_id:
    st.sidebar.warning("ALP not found")

# ---------------- MAIN ----------------
st.title("RTIS Speed & Signal Behaviour Analysis")

uploaded_file = st.file_uploader(
    "Upload RTIS File (CSV only)",
    type=["csv"]
)

run_analysis = st.button("🚦 Run Analysis")

if run_analysis and uploaded_file:

    if not lp or not alp:
        st.error("Valid LP and ALP IDs are required.")
        st.stop()

    if analysis_start >= analysis_end:
        st.error("Invalid analysis time range.")
        st.stop()

    with st.spinner("Loading RTIS data..."):
        rtis_df = load_rtis_file(uploaded_file)
        rtis_df["cum_distance"] = rtis_df["dist_from_speed"].cumsum()

    with st.spinner("Loading section & signals..."):
        section_context = load_section_data(section, direction)
        signal_df = build_signal_context(section_context)

    with st.spinner("Detecting stops..."):
        stop_events_df = detect_signal_stops(rtis_df, signal_df)

    with st.spinner("Evaluating violations..."):
        violation_df = evaluate_speed_violations(
            rtis_df,
            signal_df,
            stop_events_df,
            train_type
        )

    st.subheader("📊 Speed vs Time")
    fig_time = plot_speed_vs_time(rtis_df, signal_df)
    st.plotly_chart(fig_time, use_container_width=True)

    st.subheader("🚦 Speed vs Section (Map View)")
    st.plotly_chart(
        plot_speed_on_map(rtis_df, signal_df),
        use_container_width=True
    )

    st.subheader("⛔ Pre-Stop Speed Analysis (±2000 m)")
    if stop_events_df.empty:
        st.info("No signal-based stops detected.")
    else:
        stop_events_df["label"] = (
            stop_events_df["emoji"]
            + " "
            + stop_events_df["signal_name"]
            + " @ "
            + stop_events_df["stop_start_time"].astype(str)
        )

        selected_label = st.selectbox(
            "Select a stop to analyze",
            stop_events_df["label"]
        )

        selected_stop = stop_events_df[
            stop_events_df["label"] == selected_label
        ].iloc[0]

        fig_pre = plot_pre_stop_analysis(rtis_df, selected_stop)
        if fig_pre:
            st.plotly_chart(fig_pre, use_container_width=True)

else:
    st.info("Upload an RTIS file and click **Run Analysis** to begin.")
