
import os
import re
from io import BytesIO
from datetime import datetime
from xml.sax.saxutils import escape

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
    KeepTogether
)
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ==================================================
# DOCTOR CAR BRAND COLORS
# ==================================================

NAVY = HexColor("#102B4E")
DARK_NAVY = HexColor("#091D35")
GOLD = HexColor("#D6A84F")
LIGHT_BLUE = HexColor("#EAF1F8")
LIGHT_GREY = HexColor("#F3F5F7")
DARK_GREY = HexColor("#454F5B")
BORDER = HexColor("#D5DCE4")
WHITE = colors.white


# ==================================================
# FONT SUPPORT
# ==================================================

FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"


def register_custom_fonts():

    """
    Optional Unicode font support.

    Add font files to the repository later if required.
    """

    global FONT_REGULAR, FONT_BOLD

    font_files = [
        (
            "DoctorCarRegular",
            "DejaVuSans.ttf"
        ),
        (
            "DoctorCarBold",
            "DejaVuSans-Bold.ttf"
        )
    ]

    registered = {}

    for font_name, font_path in font_files:

        if os.path.exists(font_path):

            try:

                pdfmetrics.registerFont(
                    TTFont(font_name, font_path)
                )

                registered[font_name] = True

            except Exception:
                pass

    if "DoctorCarRegular" in registered:
        FONT_REGULAR = "DoctorCarRegular"

    if "DoctorCarBold" in registered:
        FONT_BOLD = "DoctorCarBold"


register_custom_fonts()


# ==================================================
# TEXT HELPERS
# ==================================================

def safe_text(value, default="N/A"):

    if value is None:
        return default

    text = str(value).strip()

    if not text:
        return default

    return escape(text).replace("\n", "<br/>")


def markdown_to_reportlab(text):

    """
    Convert basic Markdown into ReportLab-compatible text.
    """

    if text is None:
        return ""

    text = escape(str(text))

    # Bold
    text = re.sub(
        r"\*\*(.*?)\*\*",
        r"<b>\1</b>",
        text
    )

    # Italic
    text = re.sub(
        r"(?<!\*)\*([^*]+)\*(?!\*)",
        r"<i>\1</i>",
        text
    )

    # Inline code
    text = re.sub(
        r"`([^`]+)`",
        r"<font name='Courier'>\1</font>",
        text
    )

    return text


# ==================================================
# REPORT STYLES
# ==================================================

def create_styles():

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="DoctorCarTitle",
            fontName=FONT_BOLD,
            fontSize=25,
            leading=30,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=2 * mm
        )
    )

    styles.add(
        ParagraphStyle(
            name="DoctorCarSubtitle",
            fontName=FONT_REGULAR,
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
            fontName=FONT_BOLD,
            fontSize=11,
            leading=15,
            textColor=NAVY,
            spaceBefore=5 * mm,
            spaceAfter=2.5 * mm,
            keepWithNext=True
        )
    )

    styles.add(
        ParagraphStyle(
            name="SubHeading",
            fontName=FONT_BOLD,
            fontSize=9,
            leading=12,
            textColor=NAVY,
            spaceBefore=3 * mm,
            spaceAfter=1.5 * mm,
            keepWithNext=True
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodyTextCustom",
            fontName=FONT_REGULAR,
            fontSize=8.5,
            leading=12,
            textColor=DARK_GREY,
            spaceAfter=2 * mm
        )
    )

    styles.add(
        ParagraphStyle(
            name="SmallTextCustom",
            fontName=FONT_REGULAR,
            fontSize=7,
            leading=10,
            textColor=DARK_GREY
        )
    )

    styles.add(
        ParagraphStyle(
            name="BulletCustom",
            fontName=FONT_REGULAR,
            fontSize=8.5,
            leading=12,
            leftIndent=10,
            firstLineIndent=-7,
            textColor=DARK_GREY,
            spaceAfter=1.5 * mm
        )
    )

    styles.add(
        ParagraphStyle(
            name="TableHeaderCustom",
            fontName=FONT_BOLD,
            fontSize=7.5,
            leading=10,
            textColor=WHITE
        )
    )

    styles.add(
        ParagraphStyle(
            name="TableCellCustom",
            fontName=FONT_REGULAR,
            fontSize=7.2,
            leading=10,
            textColor=DARK_GREY
        )
    )

    return styles


# ==================================================
# VEHICLE INFORMATION TABLE
# ==================================================

def create_vehicle_table(
    vehicle,
    customer_name,
    customer_phone,
    complaint,
    report_id
):

    vehicle = vehicle or {}

    styles = create_styles()

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
            "Phone",
            safe_text(customer_phone)
        ],
        [
            "Make",
            safe_text(vehicle.get("make")),
            "Model",
            safe_text(vehicle.get("model"))
        ],
        [
            "Year",
            safe_text(vehicle.get("year")),
            "Mileage",
            safe_text(vehicle.get("mileage"))
        ],
        [
            "VIN",
            safe_text(vehicle.get("vin")),
            "Specification",
            safe_text(vehicle.get("specification"))
        ],
        [
            "Fuel Type",
            safe_text(vehicle.get("fuel_type")),
            "Transmission",
            safe_text(vehicle.get("transmission"))
        ],
        [
            "Engine",
            safe_text(
                vehicle.get("engine")
                or vehicle.get("engine_capacity")
            ),
            "Engine Code",
            safe_text(vehicle.get("engine_code"))
        ],
        [
            "Drivetrain",
            safe_text(vehicle.get("drivetrain")),
            "Engine Power",
            safe_text(vehicle.get("engine_power"))
        ],
        [
            "Customer Complaint",
            Paragraph(
                safe_text(complaint),
                styles["TableCellCustom"]
            ),
            "",
            ""
        ]
    ]

    table = Table(
        rows,
        colWidths=[
            30 * mm,
            50 * mm,
            30 * mm,
            50 * mm
        ]
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), LIGHT_BLUE),
            ("BACKGROUND", (2, 0), (2, -1), LIGHT_BLUE),

            ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
            ("TEXTCOLOR", (2, 0), (2, -1), NAVY),

            ("FONTNAME", (0, 0), (0, -1), FONT_BOLD),
            ("FONTNAME", (2, 0), (2, -1), FONT_BOLD),

            ("FONTNAME", (1, 0), (1, -1), FONT_REGULAR),
            ("FONTNAME", (3, 0), (3, -1), FONT_REGULAR),

            ("FONTSIZE", (0, 0), (-1, -1), 7.2),

            ("VALIGN", (0, 0), (-1, -1), "TOP"),

            ("GRID", (0, 0), (-1, -1), 0.4, BORDER),

            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),

            ("SPAN", (1, 8), (3, 8))
        ])
    )

    return table


# ==================================================
# MARKDOWN TABLE DETECTION
# ==================================================

def is_markdown_table_row(line):

    line = line.strip()

    return (
        line.startswith("|")
        and line.endswith("|")
        and line.count("|") >= 2
    )


def parse_markdown_table(lines):

    rows = []

    for line in lines:

        cells = [
            cell.strip()
            for cell in line.strip().strip("|").split("|")
        ]

        # Ignore Markdown separator rows
        if all(
            re.fullmatch(r":?-{3,}:?", cell.replace(" ", ""))
            for cell in cells
        ):
            continue

        rows.append(cells)

    return rows


def create_markdown_table(rows, styles):

    if not rows:
        return None

    column_count = max(len(row) for row in rows)

    normalized_rows = []

    for row in rows:

        row = row + [""] * (column_count - len(row))

        normalized_row = []

        for index, cell in enumerate(row):

            style = (
                styles["TableHeaderCustom"]
                if len(normalized_rows) == 0
                else styles["TableCellCustom"]
            )

            normalized_row.append(
                Paragraph(
                    markdown_to_reportlab(cell),
                    style
                )
            )

        normalized_rows.append(normalized_row)

    available_width = 180 * mm
    column_width = available_width / column_count

    table = Table(
        normalized_rows,
        colWidths=[column_width] * column_count,
        repeatRows=1,
        hAlign="LEFT"
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),

            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                WHITE,
                LIGHT_GREY
            ]),

            ("GRID", (0, 0), (-1, -1), 0.35, BORDER),

            ("VALIGN", (0, 0), (-1, -1), "TOP"),

            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5)
        ])
    )

    return table


# ==================================================
# DIAGNOSIS CONTENT
# ==================================================

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

    index = 0

    while index < len(lines):

        line = lines[index].strip()

        if not line:

            story.append(Spacer(1, 1.5 * mm))
            index += 1
            continue

        # Markdown table
        if is_markdown_table_row(line):

            table_lines = []

            while (
                index < len(lines)
                and is_markdown_table_row(lines[index].strip())
            ):

                table_lines.append(lines[index].strip())
                index += 1

            rows = parse_markdown_table(table_lines)

            table = create_markdown_table(
                rows,
                styles
            )

            if table:
                story.append(table)
                story.append(Spacer(1, 3 * mm))

            continue

        # Main headings
        if line.startswith("# "):

            heading = markdown_to_reportlab(line[2:])

            story.append(
                Paragraph(
                    heading,
                    styles["SectionHeading"]
                )
            )

            index += 1
            continue

        if line.startswith("## ") or line.startswith("### "):

            heading = markdown_to_reportlab(
                line.split(" ", 1)[1]
            )

            story.append(
                Paragraph(
                    heading,
                    styles["SubHeading"]
                )
            )

            index += 1
            continue

        # Bullet points
        if line.startswith("- ") or line.startswith("* "):

            bullet_text = markdown_to_reportlab(line[2:])

            story.append(
                Paragraph(
                    "&#8226; " + bullet_text,
                    styles["BulletCustom"]
                )
            )

            index += 1
            continue

        # Numbered points
        numbered_match = re.match(
            r"^(\d+)[.)]\s+(.*)$",
            line
        )

        if numbered_match:

            number = numbered_match.group(1)

            content = markdown_to_reportlab(
                numbered_match.group(2)
            )

            story.append(
                Paragraph(
                    f"{number}. {content}",
                    styles["BulletCustom"]
                )
            )

            index += 1
            continue

        # Normal paragraph
        story.append(
            Paragraph(
                markdown_to_reportlab(line),
                styles["BodyTextCustom"]
            )
        )

        index += 1


# ==================================================
# HEADER AND FOOTER
# ==================================================

def draw_page(canvas, doc):

    canvas.saveState()

    page_width, page_height = A4

    # Top navy line
    canvas.setFillColor(NAVY)

    canvas.rect(
        0,
        page_height - 5 * mm,
        page_width,
        5 * mm,
        fill=1,
        stroke=0
    )

    # Gold accent
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

    canvas.setFont(FONT_REGULAR, 7)
    canvas.setFillColor(DARK_GREY)

    canvas.drawString(
        15 * mm,
        10 * mm,
        "DOCTOR CAR | Professional Vehicle Diagnostics"
    )

    canvas.drawRightString(
        page_width - 15 * mm,
        10 * mm,
        f"Page {doc.page}"
    )

    canvas.restoreState()


# ==================================================
# DISCLAIMER
# ==================================================

def create_disclaimer(styles):

    disclaimer = (
        "This report is based on the vehicle information, "
        "scanner data, diagnostic trouble codes, visual evidence "
        "and inspection information available at the time of "
        "inspection. Findings are limited by the quality and "
        "availability of the supplied data. A diagnostic trouble "
        "code alone does not prove that a component has failed. "
        "Further testing may be required to confirm the root cause. "
        "No guarantee is made regarding future vehicle reliability "
        "or condition. Repair decisions should be made only after "
        "appropriate verification by a qualified automotive technician."
    )

    box = Table(
        [[
            Paragraph(
                disclaimer,
                styles["SmallTextCustom"]
            )
        ]],
        colWidths=[180 * mm]
    )

    box.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER),

            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8)
        ])
    )

    return box


# ==================================================
# MAIN PDF GENERATOR
# ==================================================

def generate_pdf(
    vehicle,
    customer_name,
    complaint,
    diagnosis,
    report_id,
    customer_phone=""
):

    """
    Generate Doctor Car professional diagnostic PDF.

    Existing app.py compatibility is preserved.

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
    # REPORT HEADER
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
            "PROFESSIONAL VEHICLE DIAGNOSTICS",
            styles["DoctorCarSubtitle"]
        )
    )

    story.append(
        Paragraph(
            "AI-Assisted Diagnostic Report",
            ParagraphStyle(
                "ReportSubtitle",
                fontName=FONT_BOLD,
                fontSize=10,
                leading=13,
                textColor=NAVY,
                alignment=TA_CENTER,
                spaceAfter=3 * mm
            )
        )
    )

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
    story.append(Spacer(1, 4 * mm))

    # --------------------------------------------------
    # VEHICLE INFORMATION
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
            customer_phone,
            complaint,
            report_id
        )
    )

    story.append(Spacer(1, 3 * mm))

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

    story.append(Spacer(1, 4 * mm))

    # --------------------------------------------------
    # DISCLAIMER
    # --------------------------------------------------

    story.append(
        Paragraph(
            "IMPORTANT INFORMATION & DISCLAIMER",
            styles["SectionHeading"]
        )
    )

    story.append(
        create_disclaimer(styles)
    )

    story.append(Spacer(1, 5 * mm))

    # --------------------------------------------------
    # REPORT END
    # --------------------------------------------------

    story.append(
        Paragraph(
            "Prepared by Doctor Car",
            ParagraphStyle(
                "PreparedBy",
                fontName=FONT_BOLD,
                fontSize=9,
                leading=12,
                textColor=NAVY,
                alignment=TA_CENTER,
                spaceBefore=3 * mm
            )
        )
    )

    story.append(
        Paragraph(
            "Professional Pre-Purchase Vehicle Inspection | UAE",
            ParagraphStyle(
                "CompanyTagline",
                fontName=FONT_REGULAR,
                fontSize=7,
                leading=10,
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
