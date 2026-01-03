# core/report_engine.py

from pathlib import Path
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import plotly.io as pio
import tempfile
import pandas as pd


class ReportEngineError(Exception):
    """Custom exception for report generation errors."""
    pass


OUTPUT_DIR = Path("outputs/temp_reports")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _plotly_to_image(fig, width=900, height=450):
    """
    Convert Plotly figure to PNG image and return file path.
    """
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    pio.write_image(fig, tmp.name, width=width, height=height)
    return tmp.name


def generate_pdf_report(
    report_context: dict,
    rtis_summary: dict,
    stop_events_df: pd.DataFrame,
    violation_df: pd.DataFrame,
    figures: dict,
):
    """
    Generate structured RTIS analysis PDF report.

    Parameters
    ----------
    report_context : dict
        Train, crew, section, route, time details.
    rtis_summary : dict
        Aggregate stats (distance, stops, violations).
    stop_events_df : pd.DataFrame
        Signal stop events.
    violation_df : pd.DataFrame
        Speed violation events.
    figures : dict
        {
            'time_speed': fig,
            'section_progress': fig,
            'pre_stop': [fig1, fig2, ...]
        }

    Returns
    -------
    Path
        Path to generated PDF file.
    """

    output_file = OUTPUT_DIR / f"RTIS_Report_{report_context['train_number']}.pdf"

    styles = getSampleStyleSheet()
    story = []

    # ---------------------------
    # PAGE 1 — HEADER & METADATA
    # ---------------------------
    story.append(Paragraph("<b>RTIS Driving Behaviour Analysis Report</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    meta_table_data = [
        ["Train Number", report_context["train_number"]],
        ["Loco Number", report_context["loco_number"]],
        ["Train Type", report_context["train_type"]],
        ["Max Permissible Speed", f"{report_context['max_speed']} kmph"],
        ["Section", report_context["section"]],
        ["Route (Reference)", report_context["route"]],
        ["Direction", report_context["direction"]],
        ["Analysis Period", report_context["analysis_period"]],
    ]

    meta_table = Table(meta_table_data, colWidths=[180, 300])
    meta_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ])
    )

    story.append(meta_table)
    story.append(Spacer(1, 20))

    crew_table_data = [
        ["Role", "ID", "Name", "Group CLI"],
        ["LP", report_context["lp_id"], report_context["lp_name"], report_context["lp_cli"]],
        ["ALP", report_context["alp_id"], report_context["alp_name"], report_context["alp_cli"]],
    ]

    crew_table = Table(crew_table_data, colWidths=[60, 80, 180, 160])
    crew_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ])
    )

    story.append(crew_table)
    story.append(PageBreak())

    # ---------------------------
    # PAGE 2 — STOP SUMMARY
    # ---------------------------
    story.append(Paragraph("<b>Signal Stop Summary</b>", styles["Heading2"]))
    story.append(Spacer(1, 12))

    stop_table_data = [["Station", "Signal", "Start Time", "End Time", "Duration (s)"]]
    for _, row in stop_events_df.iterrows():
        stop_table_data.append([
            row["station"],
            row["signal_name"],
            str(row["stop_start_time"]),
            str(row["stop_end_time"]),
            int(row["stop_duration_sec"]),
        ])

    stop_table = Table(stop_table_data, repeatRows=1)
    stop_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ])
    )

    story.append(stop_table)
    story.append(PageBreak())

    # ---------------------------
    # PAGE 3 — TIME vs SPEED GRAPH
    # ---------------------------
    story.append(Paragraph("<b>Speed vs Time</b>", styles["Heading2"]))
    story.append(Spacer(1, 12))

    img_path = _plotly_to_image(figures["time_speed"])
    story.append(Image(img_path, width=500, height=250))
    story.append(PageBreak())

    # ---------------------------
    # PAGE 4 — SECTION PROGRESSION
    # ---------------------------
    story.append(Paragraph("<b>Speed vs Section Progression</b>", styles["Heading2"]))
    story.append(Spacer(1, 12))

    img_path = _plotly_to_image(figures["section_progress"])
    story.append(Image(img_path, width=500, height=250))
    story.append(PageBreak())

    # ---------------------------
    # PAGE 5+ — PRE-STOP ANALYSIS
    # ---------------------------
    for fig in figures.get("pre_stop", []):
        img_path = _plotly_to_image(fig)
        story.append(Paragraph("<b>Pre-stop Speed Analysis</b>", styles["Heading2"]))
        story.append(Spacer(1, 12))
        story.append(Image(img_path, width=500, height=250))
        story.append(PageBreak())

    # ---------------------------
    # FINAL PAGE — VIOLATIONS
    # ---------------------------
    story.append(Paragraph("<b>Violation Summary</b>", styles["Heading2"]))
    story.append(Spacer(1, 12))

    if violation_df.empty:
        story.append(Paragraph("No speed violations observed.", styles["Normal"]))
    else:
        viol_table_data = [["Type", "Signal", "Station", "Allowed", "Observed"]]
        for _, row in violation_df.iterrows():
            viol_table_data.append([
                row["violation_type"],
                row["signal_name"],
                row["station"],
                row["allowed_speed"],
                row["observed_speed"],
            ])

        viol_table = Table(viol_table_data, repeatRows=1)
        viol_table.setStyle(
            TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ])
        )
        story.append(viol_table)

    # ---------------------------
    # BUILD PDF
    # ---------------------------
    doc = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    doc.build(story)

    return output_file
