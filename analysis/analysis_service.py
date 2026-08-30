import os
import glob

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    PageBreak,
)


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

SESSION_DIR = os.path.join(
    PROJECT_ROOT,
    "sessions"
)

OUTPUT_DIR = os.path.join(
    PROJECT_ROOT,
    "analysis",
    "outputs"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# FIND LATEST SESSION
# ============================================================

def get_latest_session():

    files = glob.glob(
        os.path.join(
            SESSION_DIR,
            "session_*.csv"
        )
    )

    if not files:
        raise FileNotFoundError(
            "No session CSV files found."
        )

    return max(
        files,
        key=os.path.getmtime
    )


# ============================================================
# LOAD SESSION DATA
# ============================================================

def load_session(csv_path):

    data = pd.read_csv(
        csv_path
    )

    required_columns = [
        "Time",
        "BlinkRate",
        "Stress",
        "Distraction",
        "CognitiveLoad",
        "Phase",
        "Stability",
        "AttentionSpan"
    ]

    missing = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing:
        raise ValueError(
            f"Missing columns: {missing}"
        )

    numeric_columns = [
        "Time",
        "BlinkRate",
        "Stress",
        "Distraction",
        "CognitiveLoad",
        "Stability",
        "AttentionSpan"
    ]

    for column in numeric_columns:

        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    # Keep only post-calibration rows
    live_data = data[
        data["CognitiveLoad"].notna()
    ].copy()

    if live_data.empty:

        raise ValueError(
            "No post-calibration data exists in the selected session."
        )

    # Normalize time
    live_data["Time"] = (
        live_data["Time"]
        - live_data["Time"].iloc[0]
    )

    live_data["Phase"] = (
        live_data["Phase"]
        .fillna("Unknown")
    )

    return data, live_data


# ============================================================
# SESSION STATISTICS
# ============================================================

def calculate_statistics(data):

    cli = (
        data["CognitiveLoad"]
        .dropna()
    )

    stability = (
        data["Stability"]
        .dropna()
    )

    attention = (
        data["AttentionSpan"]
        .dropna()
    )

    phase_counts = (
        data["Phase"]
        .value_counts()
    )

    total = len(data)

    focused_count = phase_counts.get(
        "Focused",
        0
    )

    overload_count = phase_counts.get(
        "Overload",
        0
    )

    fatigue_count = phase_counts.get(
        "Fatigue",
        0
    )

    warmup_count = phase_counts.get(
        "Warm-up",
        0
    )

    stats = {

        "samples": total,

        "duration": (
            float(data["Time"].max())
            if not data.empty
            else 0
        ),

        "average_cli": (
            float(cli.mean())
            if not cli.empty
            else 0
        ),

        "peak_cli": (
            float(cli.max())
            if not cli.empty
            else 0
        ),

        "minimum_cli": (
            float(cli.min())
            if not cli.empty
            else 0
        ),

        "average_stability": (
            float(stability.mean())
            if not stability.empty
            else 0
        ),

        "max_attention": (
            float(attention.max())
            if not attention.empty
            else 0
        ),

        "focused_pct": (
            focused_count / total * 100
            if total
            else 0
        ),

        "overload_pct": (
            overload_count / total * 100
            if total
            else 0
        ),

        "fatigue_pct": (
            fatigue_count / total * 100
            if total
            else 0
        ),

        "warmup_pct": (
            warmup_count / total * 100
            if total
            else 0
        ),
    }

    return stats


# ============================================================
# CORRELATION
# ============================================================

def calculate_correlation(data):

    columns = [
        "BlinkRate",
        "Stress",
        "Distraction",
        "CognitiveLoad"
    ]

    return data[
        columns
    ].corr()


# ============================================================
# COGNITIVE LOAD GRAPH
# ============================================================

def create_cli_graph(data):

    output_path = os.path.join(
        OUTPUT_DIR,
        "cognitive_load_timeline.png"
    )

    plt.figure(
        figsize=(12, 6)
    )

    plt.plot(
        data["Time"],
        data["CognitiveLoad"],
        linewidth=2,
        label="Cognitive Load"
    )

    plt.axhline(
        30,
        linestyle="--",
        linewidth=1,
        label="30 - Focus Threshold"
    )

    plt.axhline(
        55,
        linestyle="--",
        linewidth=1,
        label="55 - Overload Threshold"
    )

    plt.axhline(
        75,
        linestyle="--",
        linewidth=1,
        label="75 - Fatigue Threshold"
    )

    plt.xlabel(
        "Time (seconds)"
    )

    plt.ylabel(
        "Cognitive Load Index"
    )

    plt.title(
        "Cognitive Load Over Time"
    )

    plt.grid(
        alpha=0.25
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=180
    )

    plt.close()

    return output_path


# ============================================================
# BEHAVIORAL SIGNAL GRAPH
# ============================================================

def create_signal_graph(data):

    output_path = os.path.join(
        OUTPUT_DIR,
        "behavioral_signals.png"
    )

    plt.figure(
        figsize=(12, 6)
    )

    plt.plot(
        data["Time"],
        data["BlinkRate"],
        label="Blink Rate"
    )

    plt.plot(
        data["Time"],
        data["Stress"],
        label="Stress"
    )

    plt.plot(
        data["Time"],
        data["Distraction"],
        label="Distraction"
    )

    plt.xlabel(
        "Time (seconds)"
    )

    plt.ylabel(
        "Signal Value"
    )

    plt.title(
        "Behavioral Signals Over Time"
    )

    plt.grid(
        alpha=0.25
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=180
    )

    plt.close()

    return output_path


# ============================================================
# PHASE DISTRIBUTION
# ============================================================

def create_phase_graph(data):

    output_path = os.path.join(
        OUTPUT_DIR,
        "phase_distribution.png"
    )

    phase_order = [
        "Warm-up",
        "Focused",
        "Overload",
        "Fatigue"
    ]

    counts = (
        data["Phase"]
        .value_counts()
        .reindex(
            phase_order,
            fill_value=0
        )
    )

    plt.figure(
        figsize=(9, 5)
    )

    plt.bar(
        counts.index,
        counts.values
    )

    plt.xlabel(
        "Cognitive Phase"
    )

    plt.ylabel(
        "Number of Samples"
    )

    plt.title(
        "Cognitive Phase Distribution"
    )

    plt.grid(
        axis="y",
        alpha=0.25
    )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=180
    )

    plt.close()

    return output_path


# ============================================================
# CORRELATION MATRIX
# ============================================================

def create_correlation_graph(corr):

    output_path = os.path.join(
        OUTPUT_DIR,
        "correlation_matrix.png"
    )

    plt.figure(
        figsize=(7, 6)
    )

    image = plt.imshow(
        corr,
        cmap="coolwarm",
        vmin=-1,
        vmax=1
    )

    plt.colorbar(
        image,
        label="Pearson Correlation"
    )

    plt.xticks(
        range(len(corr.columns)),
        corr.columns,
        rotation=45,
        ha="right"
    )

    plt.yticks(
        range(len(corr.columns)),
        corr.columns
    )

    plt.title(
        "Correlation Between Cognitive Signals"
    )

    # Write correlation values
    # inside heatmap cells

    for i in range(
        len(corr.columns)
    ):

        for j in range(
            len(corr.columns)
        ):

            value = corr.iloc[i, j]

            plt.text(
                j,
                i,
                f"{value:.2f}",
                ha="center",
                va="center"
            )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=180
    )

    plt.close()

    return output_path


# ============================================================
# INSIGHTS
# ============================================================

def generate_insights(
    data,
    stats,
    corr
):

    insights = []

    avg_cli = stats[
        "average_cli"
    ]

    peak_cli = stats[
        "peak_cli"
    ]

    stability = stats[
        "average_stability"
    ]

    focused = stats[
        "focused_pct"
    ]

    overload = stats[
        "overload_pct"
    ]

    fatigue = stats[
        "fatigue_pct"
    ]

    # --------------------------------------------------------
    # CLI
    # --------------------------------------------------------

    if avg_cli < 30:

        insights.append(
            "The average cognitive-load level remained relatively low."
        )

    elif avg_cli < 55:

        insights.append(
            "The session showed a moderate cognitive-load pattern."
        )

    elif avg_cli < 75:

        insights.append(
            "The session showed elevated cognitive-load levels."
        )

    else:

        insights.append(
            "The session showed high cognitive-load levels."
        )

    # --------------------------------------------------------
    # Peak
    # --------------------------------------------------------

    if peak_cli >= 75:

        insights.append(
            "The session reached the high-load fatigue threshold."
        )

    elif peak_cli >= 55:

        insights.append(
            "The session reached the overload range."
        )

    # --------------------------------------------------------
    # Focus
    # --------------------------------------------------------

    if focused >= 50:

        insights.append(
            "Focused behavior represented a substantial portion of the session."
        )

    # --------------------------------------------------------
    # Overload
    # --------------------------------------------------------

    if overload >= 20:

        insights.append(
            "A noticeable portion of the session was classified as overload."
        )

    # --------------------------------------------------------
    # Fatigue
    # --------------------------------------------------------

    if fatigue >= 10:

        insights.append(
            "Fatigue-level behavior appeared during the session."
        )

    # --------------------------------------------------------
    # Stability
    # --------------------------------------------------------

    if stability >= 80:

        insights.append(
            "The cognitive-load signal remained relatively stable."
        )

    elif stability < 60:

        insights.append(
            "The cognitive-load signal showed considerable variation."
        )

    # --------------------------------------------------------
    # Correlation insights
    # --------------------------------------------------------

    for feature in [
        "BlinkRate",
        "Stress",
        "Distraction"
    ]:

        value = corr.loc[
            feature,
            "CognitiveLoad"
        ]

        if value >= 0.7:

            insights.append(
                f"{feature} showed a strong positive linear association with CognitiveLoad in this session."
            )

        elif value >= 0.4:

            insights.append(
                f"{feature} showed a moderate positive linear association with CognitiveLoad in this session."
            )

        elif value <= -0.4:

            insights.append(
                f"{feature} showed a negative linear association with CognitiveLoad in this session."
            )

    if not insights:

        insights.append(
            "The session did not contain enough variation for strong analytical insights."
        )

    return insights


# ============================================================
# PDF CREATION
# ============================================================

def create_pdf(
    source_csv,
    stats,
    corr,
    insights,
    cli_graph,
    signal_graph,
    phase_graph,
    corr_graph
):

    output_path = os.path.join(
        OUTPUT_DIR,
        "Advanced_Cognitive_Report.pdf"
    )

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        leading=27,
        spaceAfter=14
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=20
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=15,
        leading=18,
        spaceBefore=10,
        spaceAfter=10
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14
    )

    elements = []

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    elements.append(
        Paragraph(
            "Advanced Cognitive Analysis Report",
            title_style
        )
    )

    elements.append(
        Paragraph(
            f"Generated from {os.path.basename(source_csv)}",
            subtitle_style
        )
    )

    # --------------------------------------------------------
    # SESSION SUMMARY
    # --------------------------------------------------------

    elements.append(
        Paragraph(
            "1. Session Summary",
            heading_style
        )
    )

    summary_data = [
        [
            "Metric",
            "Value"
        ],

        [
            "Session Duration",
            f"{stats['duration']:.1f} seconds"
        ],

        [
            "Recorded Samples",
            str(stats["samples"])
        ],

        [
            "Average Cognitive Load",
            f"{stats['average_cli']:.2f}"
        ],

        [
            "Peak Cognitive Load",
            f"{stats['peak_cli']:.0f}"
        ],

        [
            "Minimum Cognitive Load",
            f"{stats['minimum_cli']:.0f}"
        ],

        [
            "Average Stability",
            f"{stats['average_stability']:.2f}%"
        ],

        [
            "Maximum Attention Span",
            f"{stats['max_attention']:.1f} seconds"
        ]
    ]

    table = Table(
        summary_data,
        colWidths=[
            3.0 * inch,
            2.5 * inch
        ]
    )

    table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#1f2937")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                9
            ),

            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.whitesmoke,
                    colors.HexColor("#eef2f7")
                ]
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7
            )
        ])
    )

    elements.append(
        table
    )

    elements.append(
        Spacer(1, 20)
    )

    # --------------------------------------------------------
    # PHASE DISTRIBUTION
    # --------------------------------------------------------

    elements.append(
        Paragraph(
            "2. Cognitive Phase Distribution",
            heading_style
        )
    )

    phase_data = [
        [
            "Phase",
            "Percentage"
        ],

        [
            "Warm-up",
            f"{stats['warmup_pct']:.2f}%"
        ],

        [
            "Focused",
            f"{stats['focused_pct']:.2f}%"
        ],

        [
            "Overload",
            f"{stats['overload_pct']:.2f}%"
        ],

        [
            "Fatigue",
            f"{stats['fatigue_pct']:.2f}%"
        ]
    ]

    phase_table = Table(
        phase_data,
        colWidths=[
            3.0 * inch,
            2.5 * inch
        ]
    )

    phase_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#1f2937")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                9
            ),

            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.whitesmoke,
                    colors.HexColor("#eef2f7")
                ]
            )
        ])
    )

    elements.append(
        phase_table
    )

    elements.append(
        Spacer(1, 15)
    )

    elements.append(
        Image(
            phase_graph,
            width=6.2 * inch,
            height=3.4 * inch
        )
    )

    elements.append(
        PageBreak()
    )

    # --------------------------------------------------------
    # COGNITIVE LOAD
    # --------------------------------------------------------

    elements.append(
        Paragraph(
            "3. Cognitive Load Trend",
            heading_style
        )
    )

    elements.append(
        Paragraph(
            "The timeline below shows how the estimated Cognitive Load Index changed throughout the live session.",
            body_style
        )
    )

    elements.append(
        Spacer(1, 10)
    )

    elements.append(
        Image(
            cli_graph,
            width=6.7 * inch,
            height=3.4 * inch
        )
    )

    elements.append(
        Spacer(1, 15)
    )

    # --------------------------------------------------------
    # BEHAVIORAL SIGNALS
    # --------------------------------------------------------

    elements.append(
        Paragraph(
            "4. Behavioral Signal Analysis",
            heading_style
        )
    )

    elements.append(
        Image(
            signal_graph,
            width=6.7 * inch,
            height=3.4 * inch
        )
    )

    elements.append(
        PageBreak()
    )

    # --------------------------------------------------------
    # CORRELATION
    # --------------------------------------------------------

    elements.append(
        Paragraph(
            "5. Correlation Analysis",
            heading_style
        )
    )

    elements.append(
        Paragraph(
            "Pearson correlation is used to examine linear relationships between the recorded behavioral signals and the estimated Cognitive Load Index.",
            body_style
        )
    )

    elements.append(
        Spacer(1, 10)
    )

    elements.append(
        Image(
            corr_graph,
            width=5.7 * inch,
            height=4.7 * inch
        )
    )

    elements.append(
        Spacer(1, 15)
    )

    correlation_table = [
        [
            "Signal",
            "Correlation with CLI"
        ]
    ]

    for feature in [
        "BlinkRate",
        "Stress",
        "Distraction"
    ]:

        value = corr.loc[
            feature,
            "CognitiveLoad"
        ]

        correlation_table.append(
            [
                feature,
                f"{value:.3f}"
            ]
        )

    corr_table = Table(
        correlation_table,
        colWidths=[
            3.0 * inch,
            2.5 * inch
        ]
    )

    corr_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#1f2937")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "ALIGN",
                (1, 1),
                (1, -1),
                "CENTER"
            ),

            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.whitesmoke,
                    colors.HexColor("#eef2f7")
                ]
            )
        ])
    )

    elements.append(
        corr_table
    )

    elements.append(
        PageBreak()
    )

    # --------------------------------------------------------
    # INSIGHTS
    # --------------------------------------------------------

    elements.append(
        Paragraph(
            "6. Automated Behavioral Insights",
            heading_style
        )
    )

    for index, insight in enumerate(
        insights,
        start=1
    ):

        elements.append(
            Paragraph(
                f"<b>{index}.</b> {insight}",
                body_style
            )
        )

        elements.append(
            Spacer(1, 7)
        )

    # --------------------------------------------------------
    # METHODOLOGY
    # --------------------------------------------------------

    elements.append(
        Spacer(1, 15)
    )

    elements.append(
        Paragraph(
            "7. Methodology",
            heading_style
        )
    )

    methodology = (
        "The system receives behavioral features extracted from "
        "webcam-based facial landmark analysis. Blink rate, gaze "
        "deviation and head movement are normalized against a "
        "personalized calibration baseline. These signals are "
        "combined using a weighted heuristic Cognitive Load Index "
        "and evaluated over time to determine behavioral phases "
        "and stability."
    )

    elements.append(
        Paragraph(
            methodology,
            body_style
        )
    )

    elements.append(
        Spacer(1, 15)
    )

    elements.append(
        Paragraph(
            "Disclaimer: The reported values are heuristic "
            "behavioral indicators derived from visual signals "
            "and should not be interpreted as clinical or "
            "medical measurements.",
            body_style
        )
    )

    # --------------------------------------------------------
    # BUILD PDF
    # --------------------------------------------------------

    doc.build(
        elements
    )

    return output_path


# ============================================================
# MAIN PIPELINE
# ============================================================

def generate_latest_report():

    session_path = (
        get_latest_session()
    )

    print(
        f"Using session: {session_path}"
    )

    _, data = load_session(
        session_path
    )

    stats = calculate_statistics(
        data
    )

    corr = calculate_correlation(
        data
    )

    cli_graph = create_cli_graph(
        data
    )

    signal_graph = create_signal_graph(
        data
    )

    phase_graph = create_phase_graph(
        data
    )

    corr_graph = create_correlation_graph(
        corr
    )

    insights = generate_insights(
        data,
        stats,
        corr
    )

    pdf = create_pdf(
        source_csv=session_path,
        stats=stats,
        corr=corr,
        insights=insights,
        cli_graph=cli_graph,
        signal_graph=signal_graph,
        phase_graph=phase_graph,
        corr_graph=corr_graph
    )

    print()
    print(
        "=========================================="
    )
    print(
        "ANALYSIS COMPLETE"
    )
    print(
        "=========================================="
    )

    print(
        f"Average CLI       : {stats['average_cli']:.2f}"
    )

    print(
        f"Peak CLI          : {stats['peak_cli']:.0f}"
    )

    print(
        f"Average Stability : {stats['average_stability']:.2f}%"
    )

    print(
        f"Focused           : {stats['focused_pct']:.2f}%"
    )

    print(
        f"Overload          : {stats['overload_pct']:.2f}%"
    )

    print(
        f"Fatigue           : {stats['fatigue_pct']:.2f}%"
    )

    print()

    print(
        f"PDF: {pdf}"
    )

    print(
        f"Outputs: {OUTPUT_DIR}"
    )

    # ========================================================
    # CRITICAL FIX
    #
    # FastAPI needs the actual PDF path.
    # Without this return statement, Python returns None.
    # ========================================================

    return pdf


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    generate_latest_report()