
import os
import re
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import HexColor
from xml.sax.saxutils import escape


# --------------------------------------------------
# DOCTOR CAR BRAND COLORS
# --------------------------------------------------

NAVY = HexColor("#102B4E")
DARK_NAVY = HexColor("#091D35")
GOLD = HexColor("#D6A84F")
LIGHT_BLUE = HexColor("#EAF1F8")
LIGHT_GREY = HexColor("#F3F5F7")
DARK_GREY = HexColor("#454F5B")
WHITE = colors.white


# --------------------------------------------------
# OPTIONAL FONT SUPPORT
# --------------------------------------------------

def register_custom_font():
    """
    Optional:
    If you later add a Unicode TTF font to your repository,
    you can register it here for additional language support.
    """

    possible_fonts = [
        ("DoctorCarFont", "DejaVuSans.ttf"),
        ("DoctorCarFont", "NotoSans-Regular.ttf")
    ]

    for font_name, font_path in possible_fonts:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(
                    TTFont(font_name, font_path)
                )
                return font_name
            except Exception:
                pass

    return "Helvetica"


FONT_NAME = register_custom_font()


# --------------------------------------------------
# TEXT FORMATTING
# --------------------------------------------------

def safe_text(value, default="N/A"):
    """
    Convert values safely into PDF-compatible text.
    """

    if value is None:
        return default

    text = str(value).strip()

    if not text:
        return default

    return escape(text).replace("\n", "<br/>")


def clean_markdown(text):
    """
    Basic Markdown formatting support.
    """

    if not text:
        return ""

    text = str(text)

    # Escape HTML/XML special characters first
    text = escape(text)

    # Convert bold Markdown
    text = re.sub(
        r"\*\*(.*?)\*\*",
        r"<b>\1</b>",
        text
    )

    # Convert italic Markdown
    text = re.sub(
        r"(?<!\*)\*([^*]+)\*(?!\*)",
        r"<i>\1</i>",
        text
    )

    # Convert inline code
    text = re.sub(
        r"`([^`]+)`",
        r"<font name='Courier'>\1</font>",
        text
    )

    return text


# --------------------------------------------------
# REPORT STYLES
# --------------------------------------------------

def create_styles():

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="DoctorCarTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=23,
            leading=28,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=3 * mm
        )
    )

    styles.add(
        ParagraphStyle(
            name="DoctorCarSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=DARK_GREY,
            alignment=TA_CENTER,
            spaceAfter=2 * mm
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=NAVY,
            spaceBefore=5 * mm,
            spaceAfter=2 * mm
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodyTextCustom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=DARK_GREY,
            spaceAfter=2 * mm
        )
    )

    styles.add(
        ParagraphStyle(
            name="SmallTextCustom",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7,
            leading=10,
            textColor=DARK_GREY
        )
    )

    styles.add(
        ParagraphStyle(
            name="BulletCustom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            leftIndent=10,
            firstLineIndent=-7,
            textColor=DARK_GREY,
            spaceAfter=1.5 * mm
        )
    )

    return styles


# --------------------------------------------------
# VEHICLE INFORMATION TABLE
# --------------------------------------------------

def create_vehicle_table(
    vehicle,
    customer_name,
    complaint,
    report_id
):

    vehicle = vehicle or {}

    rows = [
        [
            "Report ID",
            safe_text(report_id),
            "Report Date",
            datetime.now().strftime("%d %b %Y")
        ],
        [
            "Customer",
            safe_text(customer_name),
            "Make",
            safe_text(vehicle.get("make"))
        ],
        [
            "Model",
            safe_text(vehicle.get("model")),
            "Year",
            safe_text(vehicle.get("year"))
        ],
        [
            "VIN",
            safe_text(vehicle.get("vin")),
            "Mileage",
            safe_text(vehicle.get("mileage"))
        ],
        [
            "Vehicle Specification",
            safe_text(vehicle.get("specification")),
            "Fuel Type",
            safe_text(vehicle.get("fuel_type"))
        ],
        [
            "Engine",
            safe_text(
                vehicle.get("engine")
                or vehicle.get("engine_capacity")
            ),
            "Transmission",
            safe_text(vehicle.get("transmission"))
        ],
        [
            "Drivetrain",
            safe_text(vehicle.get("drivetrain")),
            "Engine Code",
            safe_text(vehicle.get("engine_code"))
        ],
        [
            "Customer Complaint",
            Paragraph(
                safe_text(complaint),
                ParagraphStyle(
                    "ComplaintCell",
                    fontName="Helvetica",
                    fontSize=7.5,
                    leading=10
                )
            ),
            "",
            ""
        ]
    ]

    table = Table(
        rows,
        colWidths=[
            31 * mm,
            49 * mm,
            31 * mm,
            49 * mm
        ],
        repeatRows=0
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), LIGHT_BLUE),
            ("BACKGROUND", (2, 0), (2, -1), LIGHT_BLUE),

            ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
            ("TEXTCOLOR", (2, 0), (2, -1), NAVY),

            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),

            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTNAME", (3, 0), (3, -1), "Helvetica"),

            ("FONTSIZE", (0, 0), (-1, -1), 7.5),

            ("VALIGN", (0, 0), (-1, -1), "TOP"),

            ("GRID", (0, 0), (-1, -1), 0.35, HexColor("#D5DCE4")),

            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),

            ("SPAN", (1, 7), (3, 7))
        ])
    )

    return table


# --------------------------------------------------
# DIAGNOSIS CONTENT
# --------------------------------------------------

def add_diagnosis_content(story, diagnosis, styles):

    if not diagnosis:
        story.append(
            Paragraph(
                "No diagnostic analysis was provided.",
                styles["BodyTextCustom"]
            )
        )
        return

    lines = str(diagnosis).splitlines()

    for line in lines:

        line = line.strip()

        if not line:
            story.append(Spacer(1, 2 * mm))
            continue

        # Markdown headings
        if line.startswith("### "):
            heading = clean_markdown(line[4:])
            story.append(
                Paragraph(
                    heading,
                    styles["SectionHeading"]
                )
            )
            continue

        if line.startswith("## "):
            heading = clean_markdown(line[3:])
            story.append(
                Paragraph(
                    heading,
                    styles["SectionHeading"]
                )
            )
            continue

        if line.startswith("# "):
            heading = clean_markdown(line[2:])
            story.append(
                Paragraph(
                    heading,
                    styles["SectionHeading"]
                )
            )
            continue

        # Bullet points
        if line.startswith("- ") or line.startswith("* "):
            bullet_text = clean_markdown(line[2:])

            story.append(
                Paragraph(
                    "• " + bullet_text,
                    styles["BulletCustom"]
                )
            )
            continue

        # Numbered points
        numbered_match = re.match(
            r"^(\d+)[.)]\s+(.*)$",
            line
        )

        if numbered_match:
            number = numbered_match.group(1)
            content = clean_markdown(
                numbered_match.group(2)
            )

            story.append(
                Paragraph(
                    number + ". " + content,
                    styles["BulletCustom"]
                )
            )
            continue

        # Normal paragraph
        story.append(
            Paragraph(
                clean_markdown(line),
                styles["BodyTextCustom"]
            )
        )


# --------------------------------------------------
# PDF HEADER AND FOOTER
# --------------------------------------------------

def draw_page(canvas, doc):

    canvas.saveState()

    page_width, page_height = A4

    # Top brand line
    canvas.setFillColor(NAVY)
    canvas.rect(
        0,
        page_height - 5 * mm,
        page_width,
        5 * mm,
        fill=1,
        stroke=0
    )

    # Gold accent line
    canvas.setFillColor(GOLD)
    canvas.rect(
        0,
        page_height - 6 * mm,
        page_width,
        1 * mm,
        fill=1,
        stroke=0
    )

    # Footer line
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(0.7)

    canvas.line(
        15 * mm,
        15 * mm,
        page_width - 15 * mm,
        15 * mm
    )

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(DARK_GREY)

    canvas.drawString(
        15 * mm,
        10 * mm,
        "DOCTOR CAR | Professional Vehicle Inspection"
    )

    canvas.drawRightString(
        page_width - 15 * mm,
        10 * mm,
        f"Page {doc.page}"
    )

    canvas.restoreState()


# --------------------------------------------------
# MAIN PDF GENERATOR
# --------------------------------------------------

def generate_pdf(
    vehicle,
    customer_name,
    complaint,
    diagnosis,
    report_id
):

    """
    Generate a Doctor Car PDF diagnostic report.

    Compatible with:
    generate_pdf(
        vehicle,
        customer_name,
        complaint,
        diagnosis,
        report_id
    )

    Returns:
        PDF file bytes
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=21 * mm,
        title=f"Doctor Car Diagnostic Report - {report_id}",
        author="Doctor Car",
        subject="Vehicle Diagnostic Inspection Report"
    )

    styles = create_styles()

    story = []

    # --------------------------------------------------
    # COVER HEADER
    # --------------------------------------------------

    story.append(Spacer(1, 5 * mm))

    story.append(
        Paragraph(
            "DOCTOR CAR",
            styles["DoctorCarTitle"]
        )
    )

    story.append(
        Paragraph(
            "PROFESSIONAL VEHICLE INSPECTION",
            styles["DoctorCarSubtitle"]
        )
    )

    story.append(
        Paragraph(
            "AI-Assisted Vehicle Diagnostic Report",
            ParagraphStyle(
                "ReportSubtitle",
                parent=styles["DoctorCarSubtitle"],
                fontSize=10,
                textColor=NAVY
            )
        )
    )

    story.append(Spacer(1, 4 * mm))

    # Gold separator
    separator = Table(
        [[""]],
        colWidths=[180 * mm],
        rowHeights=[1.2 * mm]
    )

    separator.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), GOLD)
        ])
    )

    story.append(separator)

    story.append(Spacer(1, 5 * mm))

    # --------------------------------------------------
    # REPORT INFORMATION
    # --------------------------------------------------

    story.append(
        Paragraph(
            "1. VEHICLE & CUSTOMER INFORMATION",
            styles["SectionHeading"]
        )
    )

    story.append(
        create_vehicle_table(
            vehicle,
            customer_name,
            complaint,
            report_id
        )
    )

    story.append(Spacer(1, 4 * mm))

    # --------------------------------------------------
    # DIAGNOSTIC FINDINGS
    # --------------------------------------------------

    story.append(
        Paragraph(
            "2. DIAGNOSTIC ANALYSIS & FINDINGS",
            styles["SectionHeading"]
        )
    )

    add_diagnosis_content(
        story,
        diagnosis,
        styles
    )

    story.append(Spacer(1, 5 * mm))

    # --------------------------------------------------
    # DISCLAIMER
    # --------------------------------------------------

    story.append(
        Paragraph(
            "IMPORTANT INFORMATION & DISCLAIMER",
            styles["SectionHeading"]
        )
    )

    disclaimer = (
        "This report is based on the vehicle information, "
        "scanner data, diagnostic trouble codes, visual evidence "
        "and other inspection information provided at the time "
        "of inspection. Diagnostic conclusions are limited by "
        "the availability and quality of the supplied data. "
        "An identified trouble code does not, by itself, prove "
        "that a component has failed. Further testing may be "
        "required to confirm the root cause. This report does "
        "not guarantee future vehicle reliability or condition. "
        "Repair decisions should be made after appropriate "
        "verification by a qualified automotive technician."
    )

    disclaimer_box = Table(
        [[
            Paragraph(
                disclaimer,
                styles["SmallTextCustom"]
            )
        ]],
        colWidths=[180 * mm]
    )

    disclaimer_box.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
            ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#D5DCE4")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8)
        ])
    )

    story.append(disclaimer_box)

    story.append(Spacer(1, 5 * mm))

    # --------------------------------------------------
    # REPORT END
    # --------------------------------------------------

    story.append(
        Paragraph(
            "Prepared by Doctor Car",
            ParagraphStyle(
                "PreparedBy",
                fontName="Helvetica-Bold",
                fontSize=9,
                textColor=NAVY,
                alignment=TA_CENTER,
                spaceBefore=4 * mm
            )
        )
    )

    story.append(
        Paragraph(
            "Professional Pre-Purchase Vehicle Inspection | UAE",
            ParagraphStyle(
                "CompanyTagline",
                fontName="Helvetica",
                fontSize=7,
                textColor=DARK_GREY,
                alignment=TA_CENTER
            )
        )
    )

    # --------------------------------------------------
    # BUILD PDF
    # --------------------------------------------------

    document.build(
        story,
        onFirstPage=draw_page,
        onLaterPages=draw_page
    )

    buffer.seek(0)

    return buffer.getvalue()
