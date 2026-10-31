"""
Doctor Car - Main Application

Streamlit interface for evidence-based automotive diagnosis.

Connects:
- parameter_database.py
- smart_parameter_mapper.py
- csv_analyzer.py
- diagnostic_engine.py
- report_generator.py

Customer-facing reports are generated in English.
"""

import io
import os
import json
import uuid
import sqlite3
from datetime import datetime

import streamlit as st

from parameter_database import (
    PARAMETERS,
    default_parameter_requirements,
    suggest_modules,
    get_recommended_tests,
    get_complaint_diagnostic_summary,
)

from csv_analyzer import (
    analyze_csv,
    get_csv_text_for_ai,
)

from diagnostic_engine import (
    generate_diagnostic_questions,
    analyze_vehicle,
)

from report_generator import generate_pdf


# =========================================================
# 1. APPLICATION CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Doctor Car | AI Diagnostics",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_FILE = "doctor_car_history.db"


# =========================================================
# 2. DATABASE
# =========================================================

def get_db_connection():

    return sqlite3.connect(
        DB_FILE,
        check_same_thread=False
    )


def initialize_history_database():

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS diagnosis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT UNIQUE,
            created_at TEXT,
            customer_name TEXT,
            customer_phone TEXT,
            vehicle TEXT,
            complaint TEXT,
            diagnosis TEXT,
            analysis_mode TEXT
        )
    """)

    connection.commit()
    connection.close()


def save_diagnosis(
    report_id,
    customer_name,
    customer_phone,
    vehicle,
    complaint,
    diagnosis,
    analysis_mode
):

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO diagnosis_history (
            report_id,
            created_at,
            customer_name,
            customer_phone,
            vehicle,
            complaint,
            diagnosis,
            analysis_mode
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        report_id,
        datetime.now().isoformat(timespec="seconds"),
        customer_name,
        customer_phone,
        json.dumps(vehicle, ensure_ascii=False),
        complaint,
        diagnosis,
        analysis_mode,
    ))

    connection.commit()
    connection.close()


def get_diagnosis_history():

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            report_id,
            created_at,
            customer_name,
            vehicle,
            complaint,
            analysis_mode
        FROM diagnosis_history
        ORDER BY id DESC
        LIMIT 200
    """)

    rows = cursor.fetchall()

    connection.close()

    return rows


def get_history_record(report_id):

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM diagnosis_history
        WHERE report_id = ?
    """, (report_id,))

    record = cursor.fetchone()

    connection.close()

    return record


initialize_history_database()


# =========================================================
# 3. SESSION STATE
# =========================================================

DEFAULT_STATE = {
    "diagnosis_result": None,
    "report_id": None,
    "pdf_bytes": None,
    "csv_results": {},
    "uploaded_scan_text": "",
    "selected_page": "New Diagnosis",
}


for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# 4. HELPER FUNCTIONS
# =========================================================

def safe_string(value):

    if value is None:
        return ""

    return str(value).strip()


def vehicle_description(vehicle):

    parts = [
        vehicle.get("year", ""),
        vehicle.get("make", ""),
        vehicle.get("model", ""),
        vehicle.get("engine", ""),
    ]

    return " ".join(
        str(part)
        for part in parts
        if part
    )


def safe_recommendation(function, *args):

    try:
        return function(*args)

    except Exception:
        return None


def extract_pdf_text(uploaded_pdf):

    if uploaded_pdf is None:
        return ""

    try:

        from pypdf import PdfReader

        uploaded_pdf.seek(0)

        reader = PdfReader(uploaded_pdf)

        pages = []

        for page in reader.pages:

            text = page.extract_text()

            if text:
                pages.append(text)

        return "\n\n".join(pages)

    except Exception as error:

        return (
            "PDF text extraction failed: "
            + str(error)
        )


def make_report_id():

    timestamp = datetime.now().strftime("%Y%m%d")

    unique_part = uuid.uuid4().hex[:6].upper()

    return f"DC-{timestamp}-{unique_part}"


def normalize_pdf_output(result):

    if result is None:
        return None

    if isinstance(result, bytes):
        return result

    if isinstance(result, bytearray):
        return bytes(result)

    if hasattr(result, "getvalue"):

        try:
            return result.getvalue()
        except Exception:
            pass

    if isinstance(result, str):

        if os.path.exists(result):

            with open(result, "rb") as file:
                return file.read()

    return None


def show_status(status):

    if status == "Confirmed":
        st.success(status)

    elif status == "Strongly Suspected":
        st.warning(status)

    elif status == "Possible":
        st.info(status)

    else:
        st.warning(status)


def reset_diagnosis():

    st.session_state.diagnosis_result = None
    st.session_state.report_id = None
    st.session_state.pdf_bytes = None
    st.session_state.csv_results = {}
    st.session_state.uploaded_scan_text = ""


# =========================================================
# 5. SIDEBAR
# =========================================================

with st.sidebar:

    st.image(
        "https://placehold.co/400x120/102B50/FFFFFF?text=DOCTOR+CAR",
        use_container_width=True
    )

    st.title("Doctor Car")

    st.caption(
        "Professional Automotive Diagnostic Platform"
    )

    selected_page = st.radio(
        "Navigation",
        [
            "New Diagnosis",
            "Diagnosis History",
            "System Information",
        ],
        key="navigation",
    )

    st.divider()

    st.caption("Evidence-Based Vehicle Diagnostics")

    st.caption("AI-Assisted Analysis")


# =========================================================
# 6. NEW DIAGNOSIS PAGE
# =========================================================

if selected_page == "New Diagnosis":

    st.title("New Vehicle Diagnosis")

    st.caption(
        "Enter vehicle details and collect diagnostic evidence."
    )

    if st.button(
        "Start New Diagnosis",
        use_container_width=False
    ):

        reset_diagnosis()

    # -----------------------------------------------------
    # CUSTOMER DETAILS
    # -----------------------------------------------------

    st.subheader("1. Customer Information")

    col1, col2 = st.columns(2)

    with col1:

        customer_name = st.text_input(
            "Customer Name"
        )

    with col2:

        customer_phone = st.text_input(
            "Customer Phone"
        )

    # -----------------------------------------------------
    # VEHICLE DETAILS
    # -----------------------------------------------------

    st.subheader("2. Vehicle Information")

    col1, col2 = st.columns(2)

    with col1:

        year = st.text_input(
            "Manufacturing Year"
        )

        make = st.text_input(
            "Vehicle Make"
        )

        model = st.text_input(
            "Vehicle Model"
        )

        engine = st.text_input(
            "Engine"
        )

    with col2:

        vin = st.text_input(
            "VIN / Chassis Number"
        )

        mileage = st.text_input(
            "Odometer Reading"
        )

        fuel_type = st.selectbox(
            "Fuel Type",
            [
                "Petrol",
                "Diesel",
                "Hybrid",
                "Electric",
                "Other",
                "Unknown",
            ]
        )

        transmission = st.selectbox(
            "Transmission",
            [
                "Automatic",
                "Manual",
                "CVT",
                "DCT",
                "Other",
                "Unknown",
            ]
        )

    vehicle = {
        "year": year,
        "make": make,
        "model": model,
        "engine": engine,
        "vin": vin,
        "mileage": mileage,
        "fuel_type": fuel_type,
        "transmission": transmission,
    }

    # -----------------------------------------------------
    # COMPLAINT
    # -----------------------------------------------------

    st.subheader("3. Customer Complaint")

    complaint = st.text_area(
        "Describe the problem",
        height=130,
        placeholder=(
            "Example: Engine stalls while driving. "
            "Low fuel pressure DTC is stored. "
            "Engine restarts after adding fuel."
        )
    )

    categories = []

    required_parameters = []

    if complaint.strip():

        try:

            profile_summary = (
                get_complaint_diagnostic_summary(
                    complaint
                )
            )

            st.markdown("**Diagnostic Profile**")

            st.write(
                profile_summary
            )

        except Exception:

            profile_summary = None

        try:

            required_parameters = (
                default_parameter_requirements(
                    "",
                    complaint
                )
            )

        except Exception:

            required_parameters = []

        try:

            suggested = suggest_modules(
                complaint
            )

            st.markdown("**Suggested Diagnostic Modules**")

            st.write(suggested)

        except Exception:

            suggested = []

        try:

            recommended_tests = get_recommended_tests(
                complaint
            )

            st.markdown("**Recommended Tests**")

            st.write(recommended_tests)

        except Exception:

            recommended_tests = []

        question_data = generate_diagnostic_questions(
            vehicle_description(vehicle),
            complaint
        )

        with st.expander(
            "Diagnostic Questions",
            expanded=True
        ):

            for question in question_data.get(
                "questions",
                []
            ):

                st.write(f"• {question}")

    else:

        suggested = []
        recommended_tests = []

    # -----------------------------------------------------
    # ANSWERS
    # -----------------------------------------------------

    st.subheader("4. Diagnostic Observations")

    answers = st.text_area(
        "Answers to diagnostic questions",
        height=120,
        placeholder=(
            "Enter the customer's answers and "
            "inspector observations."
        )
    )

    # -----------------------------------------------------
    # DTC AND FREEZE FRAME
    # -----------------------------------------------------

    st.subheader("5. DTC and Freeze Frame")

    dtc_text = st.text_area(
        "Diagnostic Trouble Codes",
        height=120,
        placeholder=(
            "Example: P0087 - Fuel Rail/System Pressure Too Low"
        )
    )

    freeze_frame_text = st.text_area(
        "Freeze Frame Data",
        height=120,
        placeholder=(
            "Enter RPM, coolant temperature, load, "
            "fuel pressure and other recorded conditions."
        )
    )

    # -----------------------------------------------------
    # SCANNER DATA
    # -----------------------------------------------------

    st.subheader("6. Scanner Live Data")

    scan_text = st.text_area(
        "Additional Scanner Data",
        height=120,
        placeholder=(
            "Paste scanner readings that are not included "
            "in the CSV uploads."
        )
    )

    # -----------------------------------------------------
    # CSV FILE UPLOADS
    # -----------------------------------------------------

    st.subheader("7. Upload Scanner CSV Files")

    st.caption(
        "Upload multiple CSV files. Use a separate module name "
        "for each file where applicable."
    )

    csv_count = st.number_input(
        "Number of CSV files",
        min_value=0,
        max_value=10,
        value=1,
        step=1
    )

    module_data = {}

    for index in range(int(csv_count)):

        st.markdown(
            f"**CSV File {index + 1}**"
        )

        col1, col2 = st.columns(2)

        with col1:

            module_name = st.text_input(
                "Module / System",
                key=f"module_{index}",
                placeholder="Example: Engine / ECM"
            )

        with col2:

            csv_file = st.file_uploader(
                "Upload CSV",
                type=["csv"],
                key=f"csv_{index}"
            )

        if csv_file is not None:

            try:

                csv_analysis = analyze_csv(
                    csv_file,
                    required_parameters=(
                        required_parameters
                    ),
                    module=module_name,
                    complaint=complaint
                )

                module_key = (
                    module_name.strip()
                    if module_name.strip()
                    else f"CSV Module {index + 1}"
                )

                module_data[module_key] = csv_analysis

                st.success(
                    f"{csv_file.name}: CSV analysis completed."
                )

                summary = csv_analysis.get(
                    "summary",
                    {}
                )

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Confirmed",
                    summary.get(
                        "confirmed_parameters",
                        0
                    )
                )

                c2.metric(
                    "Needs Review",
                    summary.get(
                        "parameters_needing_review",
                        0
                    )
                )

                c3.metric(
                    "Unmapped",
                    summary.get(
                        "unmapped_parameters",
                        0
                    )
                )

                with st.expander(
                    f"View {csv_file.name} analysis"
                ):

                    st.json(summary)

                    st.write(
                        "Missing required parameters:",
                        csv_analysis.get(
                            "required_parameters",
                            {}
                        ).get(
                            "missing",
                            []
                        )
                    )

            except Exception as error:

                st.error(
                    f"CSV analysis error: {error}"
                )

    # -----------------------------------------------------
    # SCAN REPORT PDF
    # -----------------------------------------------------

    st.subheader("8. Upload Scanner PDF")

    scanner_pdf = st.file_uploader(
        "Upload scanner report PDF",
        type=["pdf"],
        key="scanner_pdf"
    )

    if scanner_pdf is not None:

        uploaded_scan_text = extract_pdf_text(
            scanner_pdf
        )

        if uploaded_scan_text.startswith(
            "PDF text extraction failed:"
        ):

            st.warning(uploaded_scan_text)

        elif uploaded_scan_text:

            st.success(
                "PDF text extracted successfully."
            )

            with st.expander("View extracted PDF text"):

                st.text(uploaded_scan_text[:15000])

            scan_text = (
                scan_text
                + "\n\n"
                + uploaded_scan_text
            )

    # -----------------------------------------------------
    # PHYSICAL FINDINGS
    # -----------------------------------------------------

    st.subheader("9. Physical Inspection Findings")

    physical_notes = st.text_area(
        "Physical Test Results",
        height=150,
        placeholder=(
            "Enter measured values and physical observations. "
            "Include test method, operating condition and results."
        )
    )

    # -----------------------------------------------------
    # IMAGES AND VIDEOS
    # -----------------------------------------------------

    st.subheader("10. Photos and Videos")

    image_files = st.file_uploader(
        "Upload diagnostic photos",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp",
        ],
        accept_multiple_files=True,
        key="diagnostic_images"
    )

    video_files = st.file_uploader(
        "Upload reference videos",
        type=[
            "mp4",
            "mov",
            "avi",
        ],
        accept_multiple_files=True,
        key="diagnostic_videos"
    )

    if video_files:

        st.info(
            "Videos are stored only as uploaded reference material "
            "in this interface. This diagnostic engine does not "
            "automatically analyze video content."
        )

    # -----------------------------------------------------
    # RUN DIAGNOSIS
    # -----------------------------------------------------

    st.divider()

    st.subheader("11. Run Diagnostic Analysis")

    st.caption(
        "Review all entered information before starting."
    )

    if st.button(
        "Analyze Vehicle",
        type="primary",
        use_container_width=True
    ):

        if not make.strip() or not model.strip():

            st.error(
                "Please enter vehicle make and model."
            )

        elif not complaint.strip():

            st.error(
                "Please enter the customer complaint."
            )

        else:

            with st.spinner(
                "Analyzing diagnostic evidence..."
            ):

                try:

                    result = analyze_vehicle(
                        vehicle=vehicle,
                        complaint=complaint,
                        answers=answers,
                        module_data=module_data,
                        dtc_text=dtc_text,
                        freeze_frame_text=freeze_frame_text,
                        scan_text=scan_text,
                        physical_notes=physical_notes,
                        image_files=image_files,
                    )

                    st.session_state.diagnosis_result = result

                    st.session_state.csv_results = module_data

                    st.session_state.report_id = make_report_id()

                    st.success(
                        "Diagnostic analysis completed."
                    )

                except Exception as error:

                    st.error(
                        f"Diagnostic analysis failed: {error}"
                    )

    # -----------------------------------------------------
    # DISPLAY DIAGNOSIS
    # -----------------------------------------------------

    result = st.session_state.diagnosis_result

    if result:

        st.divider()

        st.header("Diagnostic Results")

        st.write(
            f"**Analysis Mode:** {result.get('analysis_mode')}"
        )

        if result.get("ai_available"):

            st.success(
                "AI-assisted analysis is available."
            )

        else:

            st.warning(
                "AI analysis was unavailable. "
                "Showing local rule-based analysis."
            )

            if result.get("ai_error"):

                st.caption(
                    result.get("ai_error")
                )

        st.markdown(
            result.get("diagnosis", "")
        )

        # -------------------------------------------------
        # CSV EVIDENCE
        # -------------------------------------------------

        st.subheader("CSV Evidence Summary")

        for module_name, csv_result in (
            result.get("evidence", {}).items()
        ):

            if module_name != "csv_data":
                continue

            st.text(
                csv_result[:12000]
            )

        # -------------------------------------------------
        # PHYSICAL TESTS
        # -------------------------------------------------

        st.subheader(
            "Recommended Physical Tests"
        )

        for index, test in enumerate(
            result.get(
                "physical_test_recommendations",
                []
            ),
            start=1
        ):

            st.write(
                f"{index}. {test}"
            )

        # -------------------------------------------------
        # PDF REPORT
        # -------------------------------------------------

        st.divider()

        st.header("Generate Customer Report")

        if st.button(
            "Generate PDF Report",
            type="primary"
        ):

            try:

                report_id = (
                    st.session_state.report_id
                    or make_report_id()
                )

                pdf_result = generate_pdf(
                    vehicle=vehicle_description(vehicle),
                    customer_name=customer_name,
                    complaint=complaint,
                    diagnosis=result.get("diagnosis", ""),
                    report_id=report_id,
                    customer_phone=customer_phone,
                )

                pdf_bytes = normalize_pdf_output(
                    pdf_result
                )

                if not pdf_bytes:

                    st.error(
                        "PDF generator did not return a valid PDF file."
                    )

                else:

                    st.session_state.pdf_bytes = pdf_bytes

                    st.session_state.report_id = report_id

                    save_diagnosis(
                        report_id=report_id,
                        customer_name=customer_name,
                        customer_phone=customer_phone,
                        vehicle=vehicle,
                        complaint=complaint,
                        diagnosis=result.get(
                            "diagnosis",
                            ""
                        ),
                        analysis_mode=result.get(
                            "analysis_mode",
                            ""
                        ),
                    )

                    st.success(
                        "PDF report generated and diagnosis saved."
                    )

            except Exception as error:

                st.error(
                    f"PDF generation failed: {error}"
                )

        if st.session_state.pdf_bytes:

            st.download_button(
                label="Download Customer PDF Report",
                data=st.session_state.pdf_bytes,
                file_name=(
                    f"{st.session_state.report_id}.pdf"
                ),
                mime="application/pdf",
                type="primary",
            )


# =========================================================
# 7. DIAGNOSIS HISTORY
# =========================================================

elif selected_page == "Diagnosis History":

    st.title("Diagnosis History")

    records = get_diagnosis_history()

    if not records:

        st.info(
            "No saved diagnosis records found."
        )

    else:

        st.caption(
            f"{len(records)} recent records"
        )

        for record in records:

            (
                report_id,
                created_at,
                customer_name,
                vehicle_json,
                complaint,
                analysis_mode,
            ) = record

            try:

                vehicle_data = json.loads(
                    vehicle_json
                )

                vehicle_name = vehicle_description(
                    vehicle_data
                )

            except Exception:

                vehicle_name = vehicle_json

            with st.expander(
                f"{report_id} | {vehicle_name}"
            ):

                st.write(
                    f"**Date:** {created_at}"
                )

                st.write(
                    f"**Customer:** {customer_name}"
                )

                st.write(
                    f"**Complaint:** {complaint}"
                )

                st.write(
                    f"**Analysis Mode:** {analysis_mode}"
                )

                if st.button(
                    "View Saved Diagnosis",
                    key=f"view_{report_id}"
                ):

                    saved = get_history_record(
                        report_id
                    )

                    if saved:

                        st.markdown(
                            saved[7]
                        )


# =========================================================
# 8. SYSTEM INFORMATION
# =========================================================

elif selected_page == "System Information":

    st.title("System Information")

    st.subheader("Doctor Car Diagnostic Platform")

    st.write(
        "Evidence-based automotive diagnostic software."
    )

    st.markdown("""
    **Core Modules**

    - Parameter Database
    - Smart Parameter Mapper
    - CSV Analyzer
    - Diagnostic Engine
    - PDF Report Generator
    - Diagnosis History
    """)

    st.subheader("Diagnostic Evidence Principles")

    st.markdown("""
    - DTC alone does not confirm component failure.
    - Freeze-frame data must be preserved.
    - Live-data values require correct units and conditions.
    - Missing data is not zero or normal.
    - Physical confirmation tests are important.
    - OEM specifications must be verified.
    """)

    st.subheader("AI Configuration")

    if os.getenv("OPENAI_API_KEY"):

        st.success(
            "OpenAI API environment variable detected."
        )

    else:

        try:

            import streamlit as st

            if st.secrets.get(
                "OPENAI_API_KEY",
                ""
            ):

                st.success(
                    "OpenAI API key detected in Streamlit secrets."
                )

            else:

                st.warning(
                    "OpenAI API key not detected. "
                    "Rule-based analysis can still operate."
                )

        except Exception:

            st.warning(
                "OpenAI API key not detected. "
                "Rule-based analysis can still operate."
            )

    st.caption(
        "AI analysis is an assistant to the inspector. "
        "Final diagnostic decisions require technical verification."
    )


# =========================================================
# 9. FOOTER
# =========================================================

st.divider()

st.caption(
    "Doctor Car | Professional Automotive Diagnostics | UAE"
)
