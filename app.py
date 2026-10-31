import streamlit as st
import pandas as pd
import sqlite3
import uuid
import os
import re

from datetime import datetime

from csv_analyzer import (
    analyze_csv,
    get_csv_text_for_ai
)

from diagnostic_engine import (
    generate_diagnostic_questions,
    analyze_vehicle
)

from report_generator import generate_pdf


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Doctor Car AI Diagnostic System",
    page_icon="🚘",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --------------------------------------------------
# BRANDING
# --------------------------------------------------

st.markdown("""
<style>
.stApp {
    background-color: #F6F8FB;
}
.main-title {
    color: #102B46;
    font-size: 32px;
    font-weight: 800;
}
.subtitle {
    color: #C99A36;
    font-size: 14px;
    font-weight: 600;
}
div.stButton > button {
    background-color: #102B46;
    color: white;
    border-radius: 8px;
    border: 1px solid #C99A36;
    min-height: 42px;
}
div.stButton > button:hover {
    background-color: #1769AA;
    color: white;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

DB_FILE = "doctor_car_history.db"


def initialize_database():
    connection = sqlite3.connect(DB_FILE)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS inspections (
            id TEXT PRIMARY KEY,
            created_at TEXT,
            customer_name TEXT,
            vehicle TEXT,
            complaint TEXT,
            diagnosis TEXT,
            report_pdf BLOB
        )
    """)

    connection.commit()
    connection.close()


def save_inspection(
    report_id,
    customer_name,
    vehicle,
    complaint,
    diagnosis,
    pdf_bytes
):
    connection = sqlite3.connect(DB_FILE)

    connection.execute("""
        INSERT INTO inspections
        (id, created_at, customer_name, vehicle,
         complaint, diagnosis, report_pdf)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        report_id,
        datetime.now().isoformat(timespec="seconds"),
        customer_name,
        str(vehicle),
        complaint,
        diagnosis,
        pdf_bytes
    ))

    connection.commit()
    connection.close()


def get_inspection_history():
    connection = sqlite3.connect(DB_FILE)

    df = pd.read_sql_query("""
        SELECT id, created_at, customer_name,
               vehicle, complaint
        FROM inspections
        ORDER BY created_at DESC
    """, connection)

    connection.close()
    return df


# --------------------------------------------------
# PDF TEXT EXTRACTION
# --------------------------------------------------

def extract_pdf_text(uploaded_pdf):
    from pypdf import PdfReader
    from io import BytesIO

    reader = PdfReader(
        BytesIO(uploaded_pdf.getvalue())
    )

    pages = []

    for page in reader.pages:
        pages.append(page.extract_text() or "")

    return "\n".join(pages)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def make_vehicle_data():
    return {
        "make": make,
        "model": model,
        "year": year,
        "vin": vin,
        "mileage": mileage,
        "specification": specification,
        "fuel": fuel,
        "engine": engine,
        "engine_code": engine_code,
        "engine_capacity": engine_capacity,
        "engine_power": engine_power,
        "transmission": transmission,
        "drivetrain": drivetrain
    }


def safe_filename(value):
    value = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        str(value)
    )
    return value[:60] or "report"


initialize_database()


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown(
    '<div class="main-title">🚘 DOCTOR CAR</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AI-POWERED MULTI-SYSTEM VEHICLE DIAGNOSTICS'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "New Inspection",
        "Inspection History",
        "System Information"
    ]
)


# ==================================================
# NEW INSPECTION
# ==================================================

if page == "New Inspection":

    st.header("1. Vehicle & Inspection Information")

    with st.form("vehicle_form"):

        col1, col2, col3 = st.columns(3)

        with col1:
            customer_name = st.text_input(
                "Customer Name"
            )

            customer_phone = st.text_input(
                "Customer Phone"
            )

            make = st.text_input(
                "Vehicle Make",
                placeholder="Toyota"
            )

            model = st.text_input(
                "Vehicle Model",
                placeholder="Camry"
            )

            year = st.text_input(
                "Model Year",
                placeholder="2022"
            )

        with col2:
            vin = st.text_input("VIN")

            mileage = st.text_input(
                "Mileage (km)"
            )

            specification = st.selectbox(
                "Vehicle Specification",
                [
                    "GCC",
                    "USA",
                    "Canada",
                    "Japan",
                    "Europe",
                    "Korea",
                    "Other",
                    "Unknown"
                ]
            )

            fuel = st.selectbox(
                "Fuel Type",
                [
                    "Petrol",
                    "Diesel",
                    "Hybrid",
                    "Plug-in Hybrid",
                    "Electric",
                    "Other",
                    "Unknown"
                ]
            )

            engine_capacity = st.text_input(
                "Engine Capacity"
            )

        with col3:
            engine = st.text_input(
                "Engine Description"
            )

            engine_code = st.text_input(
                "Engine Code (if known)"
            )

            engine_power = st.text_input(
                "Engine Power (if known)"
            )

            transmission = st.selectbox(
                "Transmission",
                [
                    "Automatic",
                    "Manual",
                    "CVT",
                    "DCT",
                    "Other",
                    "Unknown"
                ]
            )

            drivetrain = st.selectbox(
                "Drivetrain",
                [
                    "FWD",
                    "RWD",
                    "AWD",
                    "4WD",
                    "Unknown"
                ]
            )

        st.markdown("### Customer Complaint")

        complaint = st.text_area(
            "Describe the exact complaint",
            placeholder=(
                "Example: Engine power loss during acceleration. "
                "Vehicle struggles uphill."
            ),
            height=100
        )

        submitted = st.form_submit_button(
            "Save Vehicle Information",
            use_container_width=True
        )

    if submitted:

        if not make or not model or not complaint:
            st.error(
                "Make, Model and Customer Complaint are required."
            )

        else:
            st.session_state["vehicle"] = make_vehicle_data()
            st.session_state["customer_name"] = customer_name
            st.session_state["customer_phone"] = customer_phone
            st.session_state["complaint"] = complaint

            st.success(
                "Vehicle information saved for this inspection."
            )

    if "vehicle" in st.session_state:

        vehicle = st.session_state["vehicle"]
        complaint = st.session_state["complaint"]

        st.divider()

        # ------------------------------------------
        # AI QUESTIONS
        # ------------------------------------------

        st.header("2. AI Diagnostic Questions")

        if st.button(
            "Generate Vehicle-Specific Diagnostic Questions",
            use_container_width=True
        ):

            with st.spinner(
                "AI is preparing diagnostic questions..."
            ):

                try:
                    questions = generate_diagnostic_questions(
                        vehicle,
                        complaint
                    )

                    st.session_state["ai_questions"] = questions

                except Exception as error:
                    st.error(f"AI Error: {error}")

        if "ai_questions" in st.session_state:

            st.markdown(
                st.session_state["ai_questions"]
            )

        answers = st.text_area(
            "Inspector Questionnaire Answers",
            placeholder=(
                "Enter customer answers, when the problem occurs, "
                "cold/hot condition, warning lights, recent repairs, "
                "driving conditions and other findings."
            ),
            height=140
        )

        # ------------------------------------------
        # MODULE DATA UPLOAD
        # ------------------------------------------

        st.divider()

        st.header("3. Module-Wise Live Data Upload")

        st.info(
            "Upload the CSV files exported from THINKDIAG 2. "
            "Upload each module separately wherever possible. "
            "Unsupported or unavailable parameters will not be "
            "treated as zero."
        )

        modules = [
            "Engine / ECM / PCM",
            "Transmission / TCM",
            "ABS / ESC",
            "SRS / Airbag",
            "Steering / EPS",
            "HVAC / Air Conditioning",
            "AWD / 4WD",
            "ADAS",
            "BCM / Body Electrical",
            "Battery / Charging",
            "Hybrid / EV",
            "TPMS",
            "Other Module"
        ]

        module_data = {}

        for module in modules:

            with st.expander(module):

                uploaded_csv = st.file_uploader(
                    f"Upload {module} CSV",
                    type=["csv", "txt"],
                    key=f"csv_{module}"
                )

                if uploaded_csv:

                    try:
                        result = analyze_csv(
                            uploaded_csv
                        )

                        module_data[module] = {
                            "filename": uploaded_csv.name,
                            "rows": result["rows"],
                            "columns": result["columns"],
                            "summary": result["summary"],
                            "csv_text": get_csv_text_for_ai(
                                result
                            )
                        }

                        st.success(
                            f"File read successfully: "
                            f"{result['rows']} rows"
                        )

                        st.write(
                            "**Detected Parameters**"
                        )

                        if result["summary"]:

                            summary_df = pd.DataFrame(
                                result["summary"]
                            )

                            st.dataframe(
                                summary_df,
                                use_container_width=True
                            )

                        else:
                            st.warning(
                                "No known parameter names "
                                "were automatically recognized. "
                                "Raw CSV data is retained for AI review."
                            )

                        if result["unmapped"]:
                            st.caption(
                                "Other columns: "
                                + ", ".join(
                                    result["unmapped"][:30]
                                )
                            )

                    except Exception as error:
                        st.error(
                            f"CSV Error: {error}"
                        )

        # ------------------------------------------
        # SCAN REPORT
        # ------------------------------------------

        st.divider()

        st.header("4. Full Vehicle Scan Report")

        scan_pdf = st.file_uploader(
            "Upload Full Vehicle Scan PDF",
            type=["pdf"],
            key="full_scan_pdf"
        )

        scan_text = ""

        if scan_pdf:

            try:
                scan_text = extract_pdf_text(
                    scan_pdf
                )

                st.success(
                    "PDF text extracted successfully."
                )

                with st.expander(
                    "View extracted scan report text"
                ):
                    st.text(
                        scan_text[:15000]
                    )

            except Exception as error:
                st.error(
                    f"PDF extraction error: {error}"
                )

        dtc_text = st.text_area(
            "DTC Codes and Descriptions",
            placeholder=(
                "Example:\n"
                "P0299 - Turbocharger Underboost\n"
                "P0101 - Mass Air Flow Range/Performance"
            ),
            height=100
        )

        freeze_frame = st.text_area(
            "Freeze Frame Data",
            placeholder=(
                "Paste freeze-frame readings here, "
                "including units and operating conditions."
            ),
            height=100
        )

        # ------------------------------------------
        # PHYSICAL EVIDENCE
        # ------------------------------------------

        st.divider()

        st.header("5. Physical Inspection & Evidence")

        physical_notes = st.text_area(
            "Inspector Physical Test Results",
            placeholder=(
                "Enter pressure test readings, smoke test, "
                "mechanical noise, leakage, road test findings, "
                "voltage readings and other physical evidence."
            ),
            height=120
        )

        photos = st.file_uploader(
            "Upload Inspection Photos",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp"
            ],
            accept_multiple_files=True,
            key="inspection_photos"
        )

        videos = st.file_uploader(
            "Upload Inspection Videos",
            type=[
                "mp4",
                "mov",
                "avi"
            ],
            accept_multiple_files=True,
            key="inspection_videos"
        )

        if photos:
            st.write(
                f"{len(photos)} photos uploaded."
            )

            image_columns = st.columns(4)

            for index, photo in enumerate(photos):
                with image_columns[index % 4]:
                    st.image(
                        photo,
                        caption=photo.name,
                        use_container_width=True
                    )

        if videos:
            st.info(
                f"{len(videos)} video file(s) uploaded. "
                "This version records their presence but does "
                "not yet extract and analyze video frames."
            )

        # ------------------------------------------
        # ANALYSIS
        # ------------------------------------------

        st.divider()

        st.header("6. AI Diagnostic Analysis")

        st.warning(
            "Review the uploaded data and inspection notes "
            "before generating the final diagnosis."
        )

        if st.button(
            "RUN COMPLETE AI DIAGNOSTIC ANALYSIS",
            type="primary",
            use_container_width=True
        ):

            if not module_data and not scan_text and not dtc_text:
                st.warning(
                    "Upload at least one scan/CSV file or "
                    "provide DTC information before analysis."
                )

            else:

                with st.spinner(
                    "Doctor Car AI is analyzing all available evidence..."
                ):

                    try:

                        diagnosis = analyze_vehicle(
                            vehicle=vehicle,
                            complaint=complaint,
                            answers=answers,
                            module_data=module_data,
                            dtc_text=dtc_text,
                            freeze_frame=freeze_frame,
                            scan_text=scan_text,
                            physical_notes=physical_notes,
                            image_files=photos
                        )

                        report_id = (
                            "DC-"
                            + datetime.now().strftime("%Y%m%d")
                            + "-"
                            + uuid.uuid4().hex[:6].upper()
                        )

                        pdf_bytes = generate_pdf(
                            vehicle=vehicle,
                            customer_name=st.session_state.get(
                                "customer_name",
                                ""
                            ),
                            complaint=complaint,
                            diagnosis=diagnosis,
                            report_id=report_id
                        )

                        save_inspection(
                            report_id=report_id,
                            customer_name=st.session_state.get(
                                "customer_name",
                                ""
                            ),
                            vehicle=vehicle,
                            complaint=complaint,
                            diagnosis=diagnosis,
                            pdf_bytes=pdf_bytes
                        )

                        st.session_state["last_diagnosis"] = diagnosis
                        st.session_state["last_pdf"] = pdf_bytes
                        st.session_state["last_report_id"] = report_id

                        st.success(
                            "AI analysis completed and report saved."
                        )

                    except Exception as error:

                        st.error(
                            f"Diagnostic analysis failed: {error}"
                        )

        # ------------------------------------------
        # RESULTS
        # ------------------------------------------

        if "last_diagnosis" in st.session_state:

            st.divider()

            st.header("7. Diagnostic Findings")

            st.markdown(
                st.session_state["last_diagnosis"]
            )

            st.download_button(
                label="Download Doctor Car PDF Report",
                data=st.session_state["last_pdf"],
                file_name=(
                    safe_filename(
                        st.session_state["last_report_id"]
                    )
                    + ".pdf"
                ),
                mime="application/pdf",
                use_container_width=True
            )

            st.caption(
                "Report ID: "
                + st.session_state["last_report_id"]
            )


# ==================================================
# INSPECTION HISTORY
# ==================================================

elif page == "Inspection History":

    st.header("Inspection History")

    history = get_inspection_history()

    if history.empty:

        st.info(
            "No saved inspections found."
        )

    else:

        st.dataframe(
            history,
            use_container_width=True
        )

        selected_id = st.selectbox(
            "Select Report ID",
            history["id"].tolist()
        )

        if st.button("Download Selected Report"):

            connection = sqlite3.connect(DB_FILE)

            result = connection.execute(
                "SELECT report_pdf FROM inspections WHERE id = ?",
                (selected_id,)
            ).fetchone()

            connection.close()

            if result and result[0]:

                st.download_button(
                    "Download PDF",
                    data=result[0],
                    file_name=f"{selected_id}.pdf",
                    mime="application/pdf"
                )

            else:
                st.error(
                    "PDF not found."
                )


# ==================================================
# SYSTEM INFORMATION
# ==================================================

elif page == "System Information":

    st.header("Doctor Car AI Diagnostic System")

    st.markdown("""
    ### Supported Diagnostic Modules

    - Engine / ECM / PCM
    - Transmission / TCM
    - ABS / ESC
    - SRS / Airbag
    - Steering / EPS
    - HVAC
    - AWD / 4WD
    - ADAS
    - BCM / Body Electrical
    - Battery / Charging
    - Hybrid / EV
    - TPMS
    - Other vehicle-specific modules

    ### Scanner

    THINKDIAG 2 CSV exports are supported through
    the flexible CSV reader. Exact parameter mapping
    depends on the labels and format exported by the scanner.

    ### Diagnostic Limitations

    - Not every vehicle exposes every parameter.
    - Missing data is not considered zero.
    - DTCs alone do not confirm component failure.
    - OEM specifications must be verified.
    - Physical tests may still be required.
    - Uploaded videos are not frame-analyzed in this version.

    ### Report

    Doctor Car branded PDF report with findings,
    evidence, next tests and disclaimer.
    """)

    st.info(
        "AI-generated diagnostic output must be reviewed "
        "and approved by a qualified inspector before "
        "being shared as a final customer report."
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Doctor Car | AI-Powered Vehicle Diagnostics | UAE"
)
