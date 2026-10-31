from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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
    PageBreak
)


NAVY = colors.HexColor("#102B46")
BLUE = colors.HexColor("#1769AA")
GOLD = colors.HexColor("#C99A36")
LIGHT = colors.HexColor("#F1F5F9")
GREY = colors.HexColor("#5C6773")


def markdown_to_paragraphs(text, styles):
    elements = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            elements.append(Spacer(1, 4))
            continue

        if line.startswith("# "):
            elements.append(
                Paragraph(
                    escape(line[2:]),
                    styles["Heading1"]
                )
            )

        elif line.startswith("## "):
            elements.append(
                Paragraph(
                    escape(line[3:]),
                    styles["Heading2"]
                )
            )

        elif line.startswith("### "):
            elements.append(
                Paragraph(
                    escape(line[4:]),
                    styles["Heading3"]
                )
            )

        elif line.startswith("- ") or line.startswith("* "):
            elements.append(
                Paragraph(
                    "• " + escape(line[2:]),
                    styles["BodyText"]
                )
            )

        elif line.startswith("|"):
            continue

        else:
            safe = escape(line)
            safe = safe.replace("**", "")
            elements.append(
                Paragraph(safe, styles["BodyText"])
            )

    return elements


def generate_pdf(
    vehicle,
    customer_name,
    complaint,
    diagnosis,
    report_id
):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=17 * mm,
        leftMargin=17 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="DoctorTitle",
        parent=styles["Title"],
        textColor=NAVY,
        fontSize=22,
        alignment=TA_CENTER,
        spaceAfter=5
    ))

    styles.add(ParagraphStyle(
        name="DoctorSubtitle",
        parent=styles["Normal"],
        textColor=GOLD,
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=15
    ))

    styles["Heading1"].textColor = NAVY
    styles["Heading2"].textColor = BLUE
    styles["Heading3"].textColor = GOLD
    styles["BodyText"].leading = 14
    styles["BodyText"].spaceAfter = 5

    story = []

    story.append(
        Paragraph("DOCTOR CAR", styles["DoctorTitle"])
    )

    story.append(
        Paragraph(
            "PROFESSIONAL VEHICLE DIAGNOSTIC REPORT",
            styles["DoctorSubtitle"]
        )
    )

    vehicle_rows = [
        ["Report ID", report_id],
        ["Customer", customer_name or "Not provided"],
        ["Make", vehicle.get("make", "")],
        ["Model", vehicle.get("model", "")],
        ["Year", vehicle.get("year", "")],
        ["VIN", vehicle.get("vin", "")],
        ["Mileage", vehicle.get("mileage", "")],
        ["Specification", vehicle.get("specification", "")],
        ["Engine", vehicle.get("engine", "")],
        ["Transmission", vehicle.get("transmission", "")],
        ["Complaint", complaint]
    ]

    table = Table(
        vehicle_rows,
        colWidths=[43 * mm, 130 * mm]
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT),
        ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.black),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D5DCE3")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 7)
    ]))

    story.append(table)
    story.append(Spacer(1, 15))

    story.extend(
        markdown_to_paragraphs(diagnosis, styles)
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "<b>IMPORTANT DISCLAIMER</b><br/>"
            "This report is based on the vehicle information, "
            "scanner data, uploaded documents and inspection "
            "evidence supplied at the time of assessment. "
            "Diagnostic conclusions are subject to verification "
            "through appropriate physical and manufacturer-specific "
            "tests. This report is not a guarantee of future vehicle "
            "condition. Parts should not be replaced solely on the "
            "basis of a DTC or AI-generated possibility.",
            styles["BodyText"]
        )
    )

    def footer(canvas, document):
        canvas.saveState()

        canvas.setStrokeColor(GOLD)
        canvas.setLineWidth(1)
        canvas.line(
            17 * mm,
            14 * mm,
            193 * mm,
            14 * mm
        )

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(GREY)

        canvas.drawString(
            17 * mm,
            9 * mm,
            "Doctor Car | Professional Vehicle Inspection"
        )

        canvas.drawRightString(
            193 * mm,
            9 * mm,
            f"Page {document.page}"
        )

        canvas.restoreState()

    doc.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer
    )

    buffer.seek(0)
    return buffer.getvalue()
