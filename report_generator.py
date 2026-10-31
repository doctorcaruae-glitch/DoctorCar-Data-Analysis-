"""
Doctor Car - Professional PDF Report Generator

Features:
- English-only customer-facing reports
- Navy and gold corporate theme
- Vehicle and customer details
- Evidence-based diagnostic findings
- Confirmed / Suspected / Possible status separation
- Recommended tests and limitations
- PDF returned as bytes

Uses ReportLab Platypus.
"""

import io
import re
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)


# =========================================================
# 1. BRAND SETTINGS
# =========================================================

NAVY = colors.HexColor("#102B50")
DARK_NAVY = colors.HexColor("#0A1D35")
GOLD = colors.HexColor("#C9A34E")
LIGHT_GOLD = colors.HexColor("#F5EEDC")
LIGHT_BLUE = colors.HexColor("#EAF0F7")
LIGHT_GREY = colors.HexColor("#F3F5F7")
DARK_GREY = colors.HexColor("#333333")
MID_GREY = colors.HexColor("#687386")
WHITE = colors.white

COMPANY_NAME = "DOCTOR CAR"

COMPANY_TAGLINE = (
    "Professional Pre-Purchase Vehicle Inspection"
)

COMPANY_FOOTER = (
    "Doctor Car | Professional Automotive Inspection | UAE"
)


# =========================================================
# 2. TEXT HELPERS
# =========================================================

def safe_text(value, default="Not provided"):

    if value is None:
        return default

    text = str(value).strip()

    return text if text else default


def escape_xml(value):

    text = safe_text(value)

    text = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )

    return text


def clean_report_text(value):

    """
    Convert Markdown-like AI output into readable report text.
    This is formatting only; it does not verify diagnostic claims.
    """

    text = safe_text(value, "")

    if not text:
        return "No diagnostic information provided."

    text = text.replace("\r\n", "\n")

    text = re.sub(
        r"```.*?```",
        "",
        text,
        flags=re.DOTALL
    )

    return text.strip()


def parse_markdown_line(line):

    line = line.strip()

    if not line:
        return None

    if line.startswith("# "):
        return "heading", line[2:].strip()

    if line.startswith("## "):
        return "subheading", line[3:].strip()

    if line.startswith("### "):
        return "minor_heading", line[4:].strip()

    if line.startswith("- ") or line.startswith("* "):
        return "bullet", line[2:].strip()

    if re.match(r"^\d+\.\s+", line):
        return "number", re.sub(r"^\d+\.\s+", "", line)

    return "paragraph", line


def format_inline_markdown(text):

    text = escape_xml(text)

    text = re.sub(
        r"\*\*(.*?)\*\*",
        r"<b>\1</b>",
        text
    )

    text = re.sub(
        r"\*(.*?)\*",
        r"<i>\1</i>",
        text
    )

    return text


# =========================================================
# 3. STYLES
# =========================================================

def build_styles():

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="DoctorTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=25,
            leading=30,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=4 * mm,
        )
    )

    styles.add(
        ParagraphStyle(
            name="DoctorTagline",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=MID_GREY,
            alignment=TA_CENTER,
            spaceAfter=5 * mm,
        )
    )

    styles.add(
        ParagraphStyle(
            name="DoctorSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=NAVY,
            spaceBefore=5 * mm,
            spaceAfter=2 * mm,
            keepWithNext=True,
        )
    )

    styles.add(
        ParagraphStyle(
            name="DoctorSubheading",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=DARK_NAVY,
            spaceBefore=3 * mm,
            spaceAfter=1.5 * mm,
            keepWithNext=True,
        )
    )

    styles.add(
        ParagraphStyle(
            name="DoctorBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.8,
            leading=13,
            textColor=DARK_GREY,
            spaceAfter=2 * mm,
        )
    )

    styles.add(
        ParagraphStyle(
            name="DoctorSmall",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=MID_GREY,
        )
    )

    styles.add(
        ParagraphStyle(
            name="DoctorBullet",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            leftIndent=12,
            firstLineIndent=-8,
            textColor=DARK_GREY,
            spaceAfter=1.5 * mm,
        )
    )

    styles.add(
        ParagraphStyle(
            name="DoctorStatus",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=NAVY,
        )
    )

    styles.add(
        ParagraphStyle(
            name="DoctorWhite",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=WHITE,
        )
    )

    return styles


# =========================================================
# 4. PAGE HEADER AND FOOTER
# =========================================================

def draw_page(canvas, document):

    canvas.saveState()

    page_width, page_height = A4

    # Top accent line
    canvas.setFillColor(NAVY)

    canvas.rect(
        0,
        page_height - 5 * mm,
        page_width,
        5 * mm,
        fill=1,
        stroke=0,
    )

    # Bottom separator
    canvas.setStrokeColor(GOLD)

    canvas.setLineWidth(0.8)

    canvas.line(
        15 * mm,
        14 * mm,
        page_width - 15 * mm,
        14 * mm,
    )

    canvas.setFont("Helvetica", 7)

    canvas.setFillColor(MID_GREY)

    canvas.drawString(
        15 * mm,
        9 * mm,
        COMPANY_FOOTER,
    )

    canvas.drawRightString(
        page_width - 15 * mm,
        9 * mm,
        f"Page {document.page}",
    )

    canvas.restoreState()


# =========================================================
# 5. VEHICLE INFORMATION TABLE
# =========================================================

def build_vehicle_table(
    vehicle,
    customer_name,
    customer_phone,
    report_id,
    report_date,
    styles
):

    vehicle_text = safe_text(vehicle)

    rows = [
        [
            Paragraph("<b>REPORT ID</b>", styles["DoctorSmall"]),
            Paragraph("<b>REPORT DATE</b>", styles["DoctorSmall"]),
        ],
        [
            Paragraph(
                escape_xml(report_id),
                styles["DoctorBody"]
            ),
            Paragraph(
                escape_xml(report_date),
                styles["DoctorBody"]
            ),
        ],
        [
            Paragraph("<b>CUSTOMER</b>", styles["DoctorSmall"]),
            Paragraph("<b>CONTACT</b>", styles["DoctorSmall"]),
        ],
        [
            Paragraph(
                escape_xml(customer_name),
                styles["DoctorBody"]
            ),
            Paragraph(
                escape_xml(customer_phone),
                styles["DoctorBody"]
            ),
        ],
        [
            Paragraph("<b>VEHICLE</b>", styles["DoctorSmall"]),
            Paragraph("<b>INSPECTION TYPE</b>", styles["DoctorSmall"]),
        ],
        [
            Paragraph(
                escape_xml(vehicle_text),
                styles["DoctorBody"]
            ),
            Paragraph(
                "Diagnostic Assessment",
                styles["DoctorBody"]
            ),
        ],
    ]

    table = Table(
        rows,
        colWidths=[88 * mm, 88 * mm],
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
            ("BACKGROUND", (0, 2), (-1, 2), LIGHT_BLUE),
            ("BACKGROUND", (0, 4), (-1, 4), LIGHT_BLUE),
            ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D6DDE6")),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D6DDE6")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )

    return table


# =========================================================
# 6. DIAGNOSIS CONTENT
# =========================================================

def build_diagnosis_content(diagnosis, styles):

    content = []

    text = clean_report_text(diagnosis)

    lines = text.split("\n")

    for line in lines:

        parsed = parse_markdown_line(line)

        if not parsed:
            content.append(Spacer(1, 1.5 * mm))
            continue

        kind, value = parsed

        formatted = format_inline_markdown(value)

        if kind == "heading":

            content.append(
                Paragraph(
                    formatted,
                    styles["DoctorSection"]
                )
            )

        elif kind == "subheading":

            content.append(
                Paragraph(
                    formatted,
                    styles["DoctorSection"]
                )
            )

        elif kind == "minor_heading":

            content.append(
                Paragraph(
                    formatted,
                    styles["DoctorSubheading"]
                )
            )

        elif kind == "bullet":

            content.append(
                Paragraph(
                    f"&bull; {formatted}",
                    styles["DoctorBullet"]
                )
            )

        elif kind == "number":

            content.append(
                Paragraph(
                    formatted,
                    styles["DoctorBullet"]
                )
            )

        else:

            content.append(
                Paragraph(
                    formatted,
                    styles["DoctorBody"]
                )
            )

    return content


# =========================================================
# 7. REPORT STATUS
# =========================================================

def detect_overall_status(diagnosis):

    text = safe_text(diagnosis).lower()

    if "root cause not confirmed" in text:
        return "Further Diagnosis Required"

    if "overall status: confirmed" in text:
        return "Confirmed"

    if "overall status: strongly suspected" in text:
        return "Strongly Suspected"

    if "overall status: possible" in text:
        return "Possible"

    if "overall status: further diagnosis required" in text:
        return "Further Diagnosis Required"

    return "Further Diagnosis Required"


def build_status_banner(status, styles):

    if status == "Confirmed":

        background = colors.HexColor("#E4F1E7")
        foreground = colors.HexColor("#205C32")

    elif status == "Strongly Suspected":

        background = colors.HexColor("#FFF1D6")
        foreground = colors.HexColor("#805500")

    elif status == "Possible":

        background = colors.HexColor("#E9F1FA")
        foreground = NAVY

    else:

        background = LIGHT_GREY
        foreground = DARK_GREY

    table = Table(
        [[
            Paragraph(
                f"<b>OVERALL DIAGNOSTIC STATUS: "
                f"{escape_xml(status).upper()}</b>",
                styles["DoctorStatus"]
            )
        ]],
        colWidths=[176 * mm],
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), background),
            ("TEXTCOLOR", (0, 0), (-1, -1), foreground),
            ("BOX", (0, 0), (-1, -1), 0.7, foreground),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    return table


# =========================================================
# 8. COMPLETE PDF GENERATION
# =========================================================

def generate_pdf(
    vehicle,
    customer_name,
    complaint,
    diagnosis,
    report_id,
    customer_phone=""
):

    """
    Generate a professional Doctor Car PDF report.

    Returns:
        bytes: PDF document bytes.
    """

    if isinstance(vehicle, dict):

        vehicle_parts = [
            vehicle.get("year", ""),
            vehicle.get("make", ""),
            vehicle.get("model", ""),
            vehicle.get("engine", ""),
        ]

        vehicle = " ".join(
            str(part)
            for part in vehicle_parts
            if part
        )

    vehicle = safe_text(vehicle)

    customer_name = safe_text(customer_name)

    customer_phone = safe_text(
        customer_phone,
        "Not provided"
    )

    complaint = safe_text(complaint)

    diagnosis = clean_report_text(diagnosis)

    report_id = safe_text(report_id)

    report_date = datetime.now().strftime(
        "%d %B %Y"
    )

    status = detect_overall_status(
        diagnosis
    )

    styles = build_styles()

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=17 * mm,
        leftMargin=17 * mm,
        topMargin=17 * mm,
        bottomMargin=20 * mm,
        title=f"Doctor Car Diagnostic Report {report_id}",
        author=COMPANY_NAME,
        subject="Automotive Diagnostic Assessment",
    )

    story = []

    # -----------------------------------------------------
    # COMPANY HEADER
    # -----------------------------------------------------

    story.append(
        Spacer(1, 5 * mm)
    )

    story.append(
        Paragraph(
            COMPANY_NAME,
            styles["DoctorTitle"]
        )
    )

    story.append(
        Paragraph(
            COMPANY_TAGLINE,
            styles["DoctorTagline"]
        )
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=GOLD,
            spaceBefore=1 * mm,
            spaceAfter=5 * mm,
        )
    )

    story.append(
        Paragraph(
            "VEHICLE DIAGNOSTIC REPORT",
            styles["DoctorSection"]
        )
    )

    # -----------------------------------------------------
    # VEHICLE DETAILS
    # -----------------------------------------------------

    story.append(
        build_vehicle_table(
            vehicle=vehicle,
            customer_name=customer_name,
            customer_phone=customer_phone,
            report_id=report_id,
            report_date=report_date,
            styles=styles,
        )
    )

    story.append(
        Spacer(1, 5 * mm)
    )

    # -----------------------------------------------------
    # CUSTOMER COMPLAINT
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "CUSTOMER REPORTED COMPLAINT",
            styles["DoctorSection"]
        )
    )

    story.append(
        Paragraph(
            escape_xml(complaint),
            styles["DoctorBody"]
        )
    )

    story.append(
        Spacer(1, 2 * mm)
    )

    # -----------------------------------------------------
    # OVERALL STATUS
    # -----------------------------------------------------

    story.append(
        build_status_banner(
            status,
            styles
        )
    )

    story.append(
        Spacer(1, 3 * mm)
    )

    # -----------------------------------------------------
    # DIAGNOSTIC ANALYSIS
    # -----------------------------------------------------

    story.extend(
        build_diagnosis_content(
            diagnosis,
            styles
        )
    )

    # -----------------------------------------------------
    # FINAL DISCLAIMER
    # -----------------------------------------------------

    story.append(
        Spacer(1, 5 * mm)
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=0.8,
            color=GOLD,
            spaceBefore=2 * mm,
            spaceAfter=3 * mm,
        )
    )

    story.append(
        Paragraph(
            "IMPORTANT DIAGNOSTIC DISCLAIMER",
            styles["DoctorSubheading"]
        )
    )

    disclaimer = (
        "This report is based on the information, scanner data "
        "and inspection findings made available at the time of "
        "assessment. Diagnostic conclusions may require further "
        "testing and verification against manufacturer-specific "
        "procedures and specifications. A stored diagnostic trouble "
        "code does not, by itself, confirm failure of a particular "
        "component. This report should not be treated as a guarantee "
        "of future vehicle performance or as a substitute for "
        "necessary repair verification."
    )

    story.append(
        Paragraph(
            escape_xml(disclaimer),
            styles["DoctorSmall"]
        )
    )

    story.append(
        Spacer(1, 5 * mm)
    )

    story.append(
        Paragraph(
            "Prepared by Doctor Car",
            styles["DoctorBody"]
        )
    )

    # -----------------------------------------------------
    # BUILD PDF
    # -----------------------------------------------------

    document.build(
        story,
        onFirstPage=draw_page,
        onLaterPages=draw_page,
    )

    buffer.seek(0)

    return buffer.getvalue()


# =========================================================
# 9. SELF TEST
# =========================================================

def run_report_generator_self_test():

    sample_pdf = generate_pdf(
        vehicle="2020 Toyota Camry 2.5L",
        customer_name="Sample Customer",
        customer_phone="",
        complaint="Engine warning light is ON.",
        diagnosis=(
            "# Executive Diagnostic Summary\n"
            "Further testing is required.\n"
            "## Confirmed Findings\n"
            "- No component failure confirmed.\n"
            "## Further Tests Required\n"
            "- Inspect the relevant system.\n"
            "Overall Status: Further Diagnosis Required"
        ),
        report_id="DC-TEST-001",
    )

    return {
        "success": (
            isinstance(sample_pdf, bytes)
            and sample_pdf.startswith(b"%PDF")
        ),
        "file_size": len(sample_pdf),
    }
