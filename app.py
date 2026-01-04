import streamlit as st
import pandas as pd
from datetime import datetime

# ---------------- CORE IMPORTS ----------------
from core.rtis_loader import load_rtis_file
from core.section_loader import load_section_data
from core.signal_mapper import build_signal_context
from core.stop_detector import detect_signal_stops
from core.violation_engine import evaluate_speed_violations
from core.graph_engine import (
    plot_speed_vs_time,
    plot_speed_vs_section_progression,
    plot_pre_stop_analysis,
)
from core.report_engine import generate_pdf_report

# ---------------- UTILS ----------------
from utils.crew_loader import get_crew_by_id

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="RTIS Driving Behaviour Analysis",
    layout="wide",
)

# ---------------- SIDEBAR ----------------
st.sidebar.title("🚆 Analysis Inputs")

# ---- Train details ----
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
    ["NGP-RIG"]  # add more later
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

# ---- Crew (ID-based, auto lookup) ----
st.sidebar.subheader("👨‍✈️ Crew Details")

lp_id = st.sidebar.text_input("LP ID")
alp_id = st.sidebar.text_input("ALP ID")

lp = get_crew_by_id(lp_id) if lp_id else None
alp = get_crew_by_id(alp_id) if alp_id else None

if lp:
    st.sidebar.success(f"LP: {lp['name']} ({lp['group_cli']})")
elif lp_id:
    st.sidebar.warning("LP not found in crew master")

if alp:
    st.sidebar.success(f"ALP: {alp['name']} ({alp['group_cli']})")
elif alp_id:
    st.sidebar.warning("ALP not found in crew master")

# ---------------- MAIN AREA ----------------
st.title("RTIS Speed & Signal Behaviour Analysis")

uploaded_file = st.file_uploader(
    "Upload RTIS File (CSV only)",
    type=["csv"]
)

run_analysis = st.button("🚦 Run Analysis")

# ---------------- ANALYSIS PIPELINE ----------------
if run_analysis and uploaded_file:

    # ---- Basic validation ----
    if not lp or not alp:
        st.error("Valid LP ID and ALP ID are required.")
        st.stop()

    if analysis_start >= analysis_end:
        st.error("Analysis start time must be before end time.")
        st.stop()

    # ---- RTIS ----
    with st.spinner("Loading RTIS data..."):
        rtis_df = load_rtis_file(uploaded_file)
        rtis_df["cum_distance"] = rtis_df["dist_from_speed"].cumsum()

    # ---- Section & Signals ----
    with st.spinner("Loading section and signal data..."):
        section_context = load_section_data(section, direction)
        signal_df = build_signal_context(section_context)

    # ---- Stop Detection ----
    with st.spinner("Detecting signal stops..."):
        stop_events_df = detect_signal_stops(
            rtis_df,
            signal_df
        )

    # ---- Violations ----
    with st.spinner("Evaluating signal violations..."):
        violation_df = evaluate_speed_violations(
            rtis_df,
            signal_df,
            stop_events_df,
            train_type
        )

    # ---------------- VISUALS ----------------
    st.subheader("📊 Speed vs Time")
    fig_time = plot_speed_vs_time(
        rtis_df,
        signal_df,
        stop_events_df,
        violation_df
    )
    st.plotly_chart(fig_time, use_container_width=True)

    st.subheader("🚦 Speed vs Section (Map View)")
    st.plotly_chart(
        plot_speed_on_map(rtis_df, signal_df),
        use_container_width=True
    )

    if not stop_events_df.empty:
        st.subheader("⛔ Pre-Stop Speed Analysis (±2000 m)")
        for _, stop in stop_events_df.iterrows():
            fig_pre = plot_pre_stop_analysis(
                rtis_df,
                stop
            )
            if fig_pre:
                st.plotly_chart(fig_pre, use_container_width=True)

    # ---------------- REPORT ----------------
    st.subheader("📄 Generate Report")

    report_context = {
        "train_number": train_number,
        "loco_number": loco_number,
        "train_type": train_type,
        "max_speed": max_speed,
        "section": section,
        "route": "NGP → RIG (Reference)",
        "direction": direction,
        "analysis_period": f"{analysis_start} to {analysis_end}",
        "lp_id": lp["crew_id"],
        "lp_name": lp["name"],
        "lp_cli": lp["group_cli"],
        "alp_id": alp["crew_id"],
        "alp_name": alp["name"],
        "alp_cli": alp["group_cli"],
    }

    figures = {
        "time_speed": fig_time,
        "section_progress": fig_section,
        "pre_stop": [
            plot_pre_stop_analysis(rtis_df, row)
            for _, row in stop_events_df.iterrows()
            if plot_pre_stop_analysis(rtis_df, row) is not None
        ],
    }

    pdf_path = generate_pdf_report(
        report_context=report_context,
        rtis_summary={},
        stop_events_df=stop_events_df,
        violation_df=violation_df,
        figures=figures,
    )

    with open(pdf_path, "rb") as f:
        st.download_button(
            label="⬇️ Download PDF Report",
            data=f,
            file_name=pdf_path.name,
            mime="application/pdf",
        )

else:
    st.info("Upload an RTIS file and click **Run Analysis** to begin.")
