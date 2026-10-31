
import os
import re
import uuid
import sqlite3
from datetime import datetime
from io import BytesIO

import streamlit as st
import pandas as pd

from pypdf import PdfReader

from csv_analyzer import analyze_csv
from csv_analyzer import get_csv_text_for_ai

from diagnostic_engine import (
    generate_diagnostic_questions,
    analyze_vehicle
)

from report_generator import generate_pdf


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Doctor Car AI Diagnostic System",
    page_icon="🚗",
    layout="wide"
)


# ==================================================
# BRAND DESIGN
# ==================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #F5F7FA;
    }

    h1, h2, h3 {
        color: #102B4E;
    }

    .main-title {
        color: #102B4E;
        font-size: 34px;
        font-weight: 800;
        text-align: center;
    }

    .sub-title {
        color: #D6A84F;
        text-align: center;
        font-size: 15px;
        font-weight: 600;
    }

    .section-box {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #DCE3EA;
        margin-bottom: 12px;
    }

    .stButton > button {
        background-color: #102B4E;
        color: white;
        border-radius: 7px;
        border: none;
        font-weight: 600;
    }

    .stButton > button:hover {
        background-color: #D6A84F;
        color: #102B4E;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ==================================================
# DATABASE
# ==================================================

DB_NAME = "doctor_car_history.db"


def get_connection():

    return sqlite3.connect(
        DB_NAME,
        check_same_thread=False
    )


def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT UNIQUE,
            created_at TEXT,
            customer_name TEXT,
            customer_phone TEXT,
            make TEXT,
            model TEXT,
            year TEXT,
            vin TEXT,
            mileage TEXT,
            specification TEXT,
            complaint TEXT,
            diagnosis TEXT
        )
        """
    )

    connection.commit()
    connection.close()


def save_inspection(
    report_id,
    customer_name,
    customer_phone,
    vehicle,
    complaint,
    diagnosis
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO inspections (
            report_id,
            created_at,
            customer_name,
            customer_phone,
            make,
            model,
            year,
            vin,
            mileage,
            specification,
            complaint,
            diagnosis
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            customer_name,
            customer_phone,
            vehicle.get("make"),
            vehicle.get("model"),
            vehicle.get("year"),
            vehicle.get("vin"),
            vehicle.get("mileage"),
            vehicle.get("specification"),
            complaint,
            diagnosis
        )
    )

    connection.commit()
    connection.close()


initialize_database()


# ==================================================
# SESSION STATE
# ==================================================

if "diagnostic_questions" not in st.session_state:
    st.session_state.diagnostic_questions = ""

if "diagnostic_result" not in st.session_state:
    st.session_state.diagnostic_result = ""

if "generated_pdf" not in st.session_state:
    st.session_state.generated_pdf = None

if "current_report_id" not in st.session_state:
    st.session_state.current_report_id = None


# ==================================================
# HEADER
# ==================================================

st.markdown(
    '<div class="main-title">DOCTOR CAR</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">AI-POWERED VEHICLE DIAGNOSTIC SYSTEM</div>',
    unsafe_allow_html=True
)

st.divider()


# ==================================================
# SIDEBAR
# ==================================================

st.sidebar.title("Doctor Car")

page = st.sidebar.radio(
    "Navigation",
    [
        "New Diagnosis",
        "Inspection History",
        "System Information"
    ]
)


# ==================================================
# PDF TEXT EXTRACTION
# ==================================================

def extract_pdf_text(pdf_file):

    try:

        reader = PdfReader(pdf_file)

        extracted_text = []

        for page_number, page in enumerate(reader.pages):

            page_text = page.extract_text() or ""

            if page_text.strip():

                extracted_text.append(
                    f"PAGE {page_number + 1}\n{page_text}"
                )

        return "\n\n".join(extracted_text)

    except Exception as error:

        st.error(
            f"Unable to read PDF: {error}"
        )

        return ""


# ==================================================
# VEHICLE DATA
# ==================================================

def get_vehicle_data():

    vehicle = {}

    st.subheader("1. Vehicle Information")

    col1, col2, col3 = st.columns(3)

    with col1:

        vehicle["make"] = st.text_input(
            "Vehicle Make *",
            placeholder="Toyota, Nissan, BMW..."
        )

        vehicle["model"] = st.text_input(
            "Vehicle Model *",
            placeholder="Camry, Patrol, X5..."
        )

        vehicle["year"] = st.text_input(
            "Model Year *",
            placeholder="2020"
        )

        vehicle["vin"] = st.text_input(
            "VIN / Chassis Number",
            placeholder="17-character VIN"
        )

    with col2:

        vehicle["mileage"] = st.text_input(
            "Current Mileage",
            placeholder="85000 km"
        )

        vehicle["specification"] = st.selectbox(
            "Vehicle Specification",
            [
                "GCC",
                "USA",
                "Canada",
                "Japan",
                "Europe",
                "Korea",
                "Other / Unknown"
            ]
        )

        vehicle["fuel_type"] = st.selectbox(
            "Fuel Type",
            [
                "Petrol",
                "Diesel",
                "Hybrid",
                "Plug-in Hybrid",
                "Electric",
                "Other / Unknown"
            ]
        )

        vehicle["engine_capacity"] = st.text_input(
            "Engine Capacity",
            placeholder="2.0L / 3.5L"
        )

    with col3:

        vehicle["engine_code"] = st.text_input(
            "Engine Code",
            placeholder="2AR-FE / QR25DE"
        )

        vehicle["engine_power"] = st.text_input(
            "Engine Power",
            placeholder="HP / kW (if known)"
        )

        vehicle["transmission"] = st.selectbox(
            "Transmission",
            [
                "Automatic",
                "Manual",
                "CVT",
                "DCT",
                "AMT",
                "Other / Unknown"
            ]
        )

        vehicle["drivetrain"] = st.selectbox(
            "Drivetrain",
            [
                "FWD",
                "RWD",
                "AWD",
                "4WD",
                "Other / Unknown"
            ]
        )

    return vehicle


# ==================================================
# CUSTOMER DATA
# ==================================================

def get_customer_data():

    st.subheader("2. Customer Information")

    col1, col2 = st.columns(2)

    with col1:

        customer_name = st.text_input(
            "Customer Name *"
        )

    with col2:

        customer_phone = st.text_input(
            "Customer Phone"
        )

    return customer_name, customer_phone


# ==================================================
# NEW DIAGNOSIS PAGE
# ==================================================

if page == "New Diagnosis":

    st.title("New Vehicle Diagnosis")

    with st.form("vehicle_information_form"):

        vehicle = get_vehicle_data()

        customer_name, customer_phone = get_customer_data()

        st.subheader("3. Customer Complaint")

        complaint = st.text_area(
            "Describe the vehicle problem / customer complaint",
            height=120,
            placeholder=(
                "Example: Engine vibration at idle, "
                "check engine light ON, poor acceleration..."
            )
        )

        basic_submit = st.form_submit_button(
            "Save Vehicle Information"
        )

    if basic_submit:

        if not vehicle["make"] or not vehicle["model"] or not vehicle["year"]:

            st.error(
                "Please enter Make, Model and Year."
            )

        elif not customer_name.strip():

            st.error(
                "Please enter customer name."
            )

        elif not complaint.strip():

            st.error(
                "Please enter customer complaint."
            )

        else:

            st.session_state.vehicle = vehicle

            st.session_state.customer_name = customer_name

            st.session_state.customer_phone = customer_phone

            st.session_state.complaint = complaint

            st.session_state.diagnostic_questions = ""

            st.session_state.diagnostic_result = ""

            st.session_state.generated_pdf = None

            st.success(
                "Vehicle and customer information saved for this session."
            )

    # --------------------------------------------------
    # CONTINUE ONLY AFTER BASIC INFORMATION
    # --------------------------------------------------

    if "vehicle" in st.session_state:

        vehicle = st.session_state.vehicle

        customer_name = st.session_state.customer_name

        customer_phone = st.session_state.customer_phone

        complaint = st.session_state.complaint

        st.divider()

        st.subheader("4. AI Diagnostic Questions")

        st.caption(
            "AI will prepare questions based on the vehicle and complaint."
        )

        if st.button(
            "Generate Diagnostic Questions",
            key="generate_questions"
        ):

            with st.spinner(
                "AI is preparing diagnostic questions..."
            ):

                try:

                    questions = generate_diagnostic_questions(
                        vehicle,
                        complaint
                    )

                    st.session_state.diagnostic_questions = questions

                except Exception as error:

                    st.error(
                        f"Question generation failed: {error}"
                    )

        if st.session_state.diagnostic_questions:

            st.markdown(
                st.session_state.diagnostic_questions
            )

        st.subheader("5. Inspector Answers")

        answers = st.text_area(
            "Enter answers to the AI questions",
            height=160,
            placeholder=(
                "Enter customer answers, test results, "
                "symptoms and inspection observations..."
            ),
            key="inspector_answers"
        )

        st.divider()

        # --------------------------------------------------
        # MODULE CSV UPLOAD
        # --------------------------------------------------

        st.subheader("6. THINKDIAG 2 Live Data CSV Files")

        st.info(
            "Upload the recorded CSV files separately for each "
            "vehicle module. Upload only the modules relevant "
            "to the complaint and available scanner data."
        )

        modules = [
            "Engine",
            "Transmission",
            "ABS/ESC",
            "SRS",
            "EPS",
            "HVAC",
            "AWD/4WD",
            "ADAS",
            "BCM/Body Electrical",
            "Battery/Charging",
            "Hybrid/EV",
            "TPMS",
            "Other OEM Modules"
        ]

        module_data = {}

        for module in modules:

            with st.expander(
                f"{module} - CSV Upload",
                expanded=(module == "Engine")
            ):

                uploaded_csv = st.file_uploader(
                    f"Upload {module} CSV",
                    type=["csv"],
                    key=f"csv_{module}"
                )

                if uploaded_csv is not None:

                    try:

                        parsed = analyze_csv(uploaded_csv)

                        module_data[module] = parsed

                        st.success(
                            f"{module} CSV uploaded successfully."
                        )

                        st.write(
                            "Detected Parameters:",
                            len(parsed.get("detected", []))
                        )

                        summary = parsed.get("summary", [])

                        if summary:

                            summary_df = pd.DataFrame(summary)

                            st.dataframe(
                                summary_df,
                                use_container_width=True,
                                hide_index=True
                            )

                        unmapped = parsed.get("unmapped", [])

                        if unmapped:

                            with st.expander(
                                "Unmapped CSV Columns"
                            ):

                                st.write(unmapped)

                        quality = parsed.get(
                            "data_quality",
                            {}
                        )

                        if quality:

                            st.caption(
                                f"Data quality: {quality}"
                            )

                    except Exception as error:

                        st.error(
                            f"Could not process {module} CSV: {error}"
                        )

        # --------------------------------------------------
        # FULL SCAN PDF
        # --------------------------------------------------

        st.divider()

        st.subheader("7. Full Vehicle Scan Report")

        scan_pdf = st.file_uploader(
            "Upload full scanner scan report PDF",
            type=["pdf"],
            key="full_scan_pdf"
        )

        scan_text = ""

        if scan_pdf is not None:

            scan_text = extract_pdf_text(scan_pdf)

            if scan_text:

                st.success(
                    "PDF text extracted successfully."
                )

                with st.expander(
                    "View Extracted Scan Information"
                ):

                    st.text(
                        scan_text[:10000]
                    )

            else:

                st.warning(
                    "No readable text was extracted. "
                    "This may be a scanned/image-only PDF. "
                    "OCR is not included in this version."
                )

        # --------------------------------------------------
        # DTC AND FREEZE FRAME
        # --------------------------------------------------

        st.subheader("8. DTC Information")

        dtc_text = st.text_area(
            "Diagnostic Trouble Codes (DTCs)",
            height=120,
            placeholder=(
                "Example:\n"
                "P0301 - Cylinder 1 Misfire\n"
                "P0171 - System Too Lean\n"
                "Include module name and status if available."
            )
        )

        freeze_frame_text = st.text_area(
            "Freeze Frame Data",
            height=120,
            placeholder=(
                "Paste freeze frame values including "
                "RPM, coolant temperature, vehicle speed, "
                "load, fuel trims and other available readings."
            )
        )

        # --------------------------------------------------
        # PHYSICAL INSPECTION NOTES
        # --------------------------------------------------

        st.subheader("9. Physical Inspection Evidence")

        physical_notes = st.text_area(
            "Inspector Notes / Physical Test Readings",
            height=150,
            placeholder=(
                "Example:\n"
                "Battery voltage: 12.5V\n"
                "Charging voltage: 14.2V\n"
                "Coolant leak observed: No\n"
                "Engine vibration: Present at idle\n"
                "Test drive observations..."
            )
        )

        # --------------------------------------------------
        # PHOTO UPLOAD
        # --------------------------------------------------

        st.subheader("10. Photo Evidence")

        image_files = st.file_uploader(
            "Upload diagnostic photos",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
            key="diagnostic_photos"
        )

        if image_files:

            st.caption(
                f"{len(image_files)} photo(s) uploaded."
            )

            photo_columns = st.columns(4)

            for index, photo in enumerate(image_files):

                with photo_columns[index % 4]:

                    st.image(
                        photo,
                        caption=photo.name,
                        use_container_width=True
                    )

        # --------------------------------------------------
        # VIDEO UPLOAD
        # --------------------------------------------------

        st.subheader("11. Optional Video Evidence")

        video_files = st.file_uploader(
            "Upload inspection videos for reference",
            type=["mp4", "mov", "avi"],
            accept_multiple_files=True,
            key="diagnostic_videos"
        )

        if video_files:

            st.info(
                f"{len(video_files)} video(s) uploaded. "
                "Video storage and AI video-frame analysis "
                "are not implemented in this version."
            )

        st.divider()

        # --------------------------------------------------
        # ANALYSIS BUTTON
        # --------------------------------------------------

        st.subheader("12. AI Diagnostic Analysis")

        st.warning(
            "Check that the vehicle details, scanner data, "
            "DTCs and inspection evidence are correct before "
            "starting the analysis."
        )

        if st.button(
            "RUN AI DIAGNOSTIC ANALYSIS",
            type="primary",
            use_container_width=True
        ):

            with st.spinner(
                "AI is analyzing vehicle data and evidence..."
            ):

                try:

                    diagnosis = analyze_vehicle(
                        vehicle=vehicle,
                        complaint=complaint,
                        answers=answers,
                        module_data=module_data,
                        dtc_text=dtc_text,
                        freeze_frame_text=freeze_frame_text,
                        scan_text=scan_text,
                        physical_notes=physical_notes,
                        image_files=image_files
                    )

                    st.session_state.diagnostic_result = diagnosis

                    report_id = (
                        "DC-"
                        + datetime.now().strftime("%Y%m%d")
                        + "-"
                        + uuid.uuid4().hex[:6].upper()
                    )

                    pdf_bytes = generate_pdf(
                        vehicle=vehicle,
                        customer_name=customer_name,
                        complaint=complaint,
                        diagnosis=diagnosis,
                        report_id=report_id
                    )

                    save_inspection(
                        report_id=report_id,
                        customer_name=customer_name,
                        customer_phone=customer_phone,
                        vehicle=vehicle,
                        complaint=complaint,
                        diagnosis=diagnosis
                    )

                    st.session_state.generated_pdf = pdf_bytes

                    st.session_state.current_report_id = report_id

                    st.success(
                        "AI diagnostic analysis and PDF report generated."
                    )

                except Exception as error:

                    st.error(
                        f"Analysis failed: {error}"
                    )

                    st.info(
                        "Check your OpenAI API key, model settings, "
                        "uploaded files and application logs."
                    )

        # --------------------------------------------------
        # DISPLAY RESULT
        # --------------------------------------------------

        if st.session_state.diagnostic_result:

            st.divider()

            st.subheader("13. Diagnostic Result")

            st.markdown(
                st.session_state.diagnostic_result
            )

        # --------------------------------------------------
        # PDF DOWNLOAD
        # --------------------------------------------------

        if st.session_state.generated_pdf:

            st.divider()

            st.subheader("14. Doctor Car PDF Report")

            st.success(
                f"Report ID: {st.session_state.current_report_id}"
            )

            st.download_button(
                label="Download Doctor Car PDF Report",
                data=st.session_state.generated_pdf,
                file_name=(
                    f"{st.session_state.current_report_id}.pdf"
                ),
                mime="application/pdf",
                use_container_width=True
            )


# ==================================================
# INSPECTION HISTORY
# ==================================================

elif page == "Inspection History":

    st.title("Inspection History")

    try:

        connection = get_connection()

        history = pd.read_sql_query(
            """
            SELECT
                report_id,
                created_at,
                customer_name,
                customer_phone,
                make,
                model,
                year,
                vin,
                mileage,
                specification
            FROM inspections
            ORDER BY id DESC
            """,
            connection
        )

        connection.close()

        if history.empty:

            st.info(
                "No inspection records available yet."
            )

        else:

            st.dataframe(
                history,
                use_container_width=True,
                hide_index=True
            )

            selected_report = st.selectbox(
                "Select Report ID to view diagnosis",
                history["report_id"].tolist()
            )

            if selected_report:

                connection = get_connection()

                selected_data = pd.read_sql_query(
                    """
                    SELECT *
                    FROM inspections
                    WHERE report_id = ?
                    """,
                    connection,
                    params=(selected_report,)
                )

                connection.close()

                if not selected_data.empty:

                    record = selected_data.iloc[0]

                    st.subheader(
                        f"Report: {selected_report}"
                    )

                    st.write(
                        "**Customer:**",
                        record["customer_name"]
                    )

                    st.write(
                        "**Vehicle:**",
                        f"{record['make']} {record['model']} "
                        f"{record['year']}"
                    )

                    st.write(
                        "**Complaint:**",
                        record["complaint"]
                    )

                    st.subheader(
                        "Saved Diagnostic Result"
                    )

                    st.markdown(
                        record["diagnosis"]
                    )

    except Exception as error:

        st.error(
            f"History error: {error}"
        )


# ==================================================
# SYSTEM INFORMATION
# ==================================================

elif page == "System Information":

    st.title("System Information")

    st.markdown(
        """
        ### Doctor Car AI Diagnostic System

        **Current application features**

        - Vehicle and customer information
        - AI-generated diagnostic questions
        - THINKDIAG 2 CSV analysis
        - Multiple vehicle module uploads
        - Full scan PDF text extraction
        - DTC and freeze-frame analysis
        - Physical inspection notes
        - Photo evidence analysis
        - AI-assisted diagnostic findings
        - PDF report generation
        - Local inspection history

        ### Important Limitations

        1. This is an initial prototype, not a production-ready system.
        2. Exact THINKDIAG 2 CSV compatibility must be tested with real exported files.
        3. Generic parameter recognition does not replace vehicle-specific OEM specifications.
        4. Scanned PDF OCR is not included.
        5. Uploaded videos are not analyzed by AI in this version.
        6. SQLite storage is local and may not persist reliably on cloud hosting.
        7. User login, inspector permissions and report approval workflow are not yet implemented.
        8. AI findings must be verified by a qualified inspector before repair decisions.

        ### Doctor Car

        Professional Pre-Purchase Vehicle Inspection  
        AI-Assisted Diagnostic Reports  
        Mobile Inspection Service Across UAE
        """
    )


# ==================================================
# END
# ==================================================
