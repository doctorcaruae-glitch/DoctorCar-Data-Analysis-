
import os
import uuid
import sqlite3
from datetime import datetime

import streamlit as st
import pandas as pd

from pypdf import PdfReader

from csv_analyzer import analyze_csv

from diagnostic_engine import (
    generate_diagnostic_questions,
    analyze_vehicle
)

from report_generator import generate_pdf

from parameter_database import (
    suggest_modules,
    default_parameter_requirements,
    get_recommended_tests,
    get_complaint_diagnostic_summary
)


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

DEFAULT_STATE = {
    "diagnostic_questions": "",
    "diagnostic_result": "",
    "generated_pdf": None,
    "current_report_id": None,
    "vehicle": None,
    "customer_name": "",
    "customer_phone": "",
    "complaint": "",
    "recommendations_loaded": False
}

for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def safe_display(value):
    """
    Display recommendation data safely,
    whether it is text, list or dictionary.
    """

    if value is None:
        st.write("No information available.")
    elif isinstance(value, (dict, list, tuple)):
        st.json(value)
    else:
        st.write(value)


def extract_pdf_text(pdf_file):

    try:

        pdf_file.seek(0)
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

        st.error(f"Unable to read PDF: {error}")
        return ""


def reset_diagnosis():

    st.session_state.diagnostic_questions = ""
    st.session_state.diagnostic_result = ""
    st.session_state.generated_pdf = None
    st.session_state.current_report_id = None
    st.session_state.recommendations_loaded = False


def get_complaint_recommendations(vehicle, complaint):

    recommendations = {}

    try:
        recommendations["modules"] = suggest_modules(complaint)
    except Exception as error:
        recommendations["modules_error"] = str(error)

    try:
        recommendations["parameters"] = (
            default_parameter_requirements(
                vehicle,
                complaint
            )
        )
    except Exception as error:
        recommendations["parameters_error"] = str(error)

    try:
        recommendations["tests"] = get_recommended_tests(complaint)
    except Exception as error:
        recommendations["tests_error"] = str(error)

    try:
        recommendations["summary"] = (
            get_complaint_diagnostic_summary(complaint)
        )
    except Exception as error:
        recommendations["summary_error"] = str(error)

    return recommendations


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
# VEHICLE INFORMATION
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
# CUSTOMER INFORMATION
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

        if (
            not vehicle["make"].strip()
            or not vehicle["model"].strip()
            or not vehicle["year"].strip()
        ):

            st.error("Please enter Make, Model and Year.")

        elif not customer_name.strip():

            st.error("Please enter customer name.")

        elif not complaint.strip():

            st.error("Please enter customer complaint.")

        else:

            st.session_state.vehicle = vehicle
            st.session_state.customer_name = customer_name
            st.session_state.customer_phone = customer_phone
            st.session_state.complaint = complaint

            reset_diagnosis()

            st.success(
                "Vehicle and customer information saved."
            )

    # --------------------------------------------------
    # CONTINUE AFTER SAVING BASIC INFORMATION
    # --------------------------------------------------

    if st.session_state.vehicle is not None:

        vehicle = st.session_state.vehicle
        customer_name = st.session_state.customer_name
        customer_phone = st.session_state.customer_phone
        complaint = st.session_state.complaint

        st.divider()

        # --------------------------------------------------
        # COMPLAINT-BASED RECOMMENDATIONS
        # --------------------------------------------------

        st.subheader("4. Complaint-Based Diagnostic Plan")

        st.caption(
            "The system recommends relevant modules, "
            "Live Data parameters and tests based on the complaint."
        )

        if st.button(
            "Generate Recommended Diagnostic Plan",
            key="generate_recommendations"
        ):

            with st.spinner(
                "Preparing complaint-based recommendations..."
            ):

                st.session_state.recommendations = (
                    get_complaint_recommendations(
                        vehicle,
                        complaint
                    )
                )

                st.session_state.recommendations_loaded = True

        if st.session_state.recommendations_loaded:

            recommendations = st.session_state.get(
                "recommendations",
                {}
            )

            with st.expander(
                "Recommended Vehicle Modules",
                expanded=True
            ):

                if "modules_error" in recommendations:
                    st.warning(
                        recommendations["modules_error"]
                    )
                else:
                    safe_display(
                        recommendations.get("modules")
                    )

            with st.expander(
                "Recommended Live Data Parameters",
                expanded=True
            ):

                if "parameters_error" in recommendations:
                    st.warning(
                        recommendations["parameters_error"]
                    )
                else:
                    safe_display(
                        recommendations.get("parameters")
                    )

            with st.expander(
                "Recommended Confirmation Tests"
            ):

                if "tests_error" in recommendations:
                    st.warning(
                        recommendations["tests_error"]
                    )
                else:
                    safe_display(
                        recommendations.get("tests")
                    )

            with st.expander(
                "Diagnostic Profile Summary"
            ):

                if "summary_error" in recommendations:
                    st.warning(
                        recommendations["summary_error"]
                    )
                else:
                    safe_display(
                        recommendations.get("summary")
                    )

            st.info(
                "These are diagnostic recommendations, not confirmed "
                "faults. Select only parameters supported by the "
                "vehicle and scanner."
            )

        st.divider()

        # --------------------------------------------------
        # AI DIAGNOSTIC QUESTIONS
        # --------------------------------------------------

        st.subheader("5. AI Diagnostic Questions")

        st.caption(
            "AI prepares questions based on the vehicle and complaint."
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

        answers = st.text_area(
            "Inspector Answers / Customer Answers",
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
            "Upload separate CSV files for the relevant vehicle "
            "modules. Use the recommended diagnostic plan above "
            "to decide which parameters to record."
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

                        uploaded_csv.seek(0)
                        parsed = analyze_csv(uploaded_csv)

                        module_data[module] = parsed

                        st.success(
                            f"{module} CSV processed successfully."
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

        st.divider()

        # --------------------------------------------------
        # FULL SCAN PDF
        # --------------------------------------------------

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
                    "This may be an image-only PDF. OCR is not "
                    "included in this version."
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
            ),
            key="dtc_information"
        )

        freeze_frame_text = st.text_area(
            "Freeze Frame Data",
            height=120,
            placeholder=(
                "RPM, coolant temperature, vehicle speed, "
                "engine load, fuel trims and other available readings."
            ),
            key="freeze_frame_information"
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
            ),
            key="physical_inspection_notes"
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

                    photo.seek(0)

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
                "Video AI analysis is not implemented yet."
            )

        st.divider()

        # --------------------------------------------------
        # AI ANALYSIS
        # --------------------------------------------------

        st.subheader("12. AI Diagnostic Analysis")

        st.warning(
            "Verify the vehicle details, scanner data, DTCs "
            "and physical inspection evidence before analysis."
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

                    # Reset file positions before sending images.
                    if image_files:

                        for photo in image_files:
                            photo.seek(0)

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

                    st.session_state.diagnostic_result = diagnosis
                    st.session_state.generated_pdf = pdf_bytes
                    st.session_state.current_report_id = report_id

                    st.success(
                        "AI analysis and PDF report generated successfully."
                    )

                except Exception as error:

                    st.error(
                        f"Analysis failed: {error}"
                    )

                    st.info(
                        "Check API key, model settings, billing/quota, "
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
                "Select Report ID",
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
                        "**Date:**",
                        record["created_at"]
                    )

                    st.write(
                        "**Customer:**",
                        record["customer_name"]
                    )

                    st.write(
                        "**Phone:**",
                        record["customer_phone"]
                    )

                    st.write(
                        "**Vehicle:**",
                        f"{record['make']} {record['model']} "
                        f"{record['year']}"
                    )

                    st.write(
                        "**VIN:**",
                        record["vin"]
                    )

                    st.write(
                        "**Mileage:**",
                        record["mileage"]
                    )

                    st.write(
                        "**Specification:**",
                        record["specification"]
                    )

                    st.subheader("Customer Complaint")

                    st.write(record["complaint"])

                    st.subheader("Saved Diagnostic Result")

                    st.markdown(record["diagnosis"])

                    # Regenerate a PDF from saved diagnosis.
                    if st.button(
                        "Regenerate PDF for This Report",
                        key="regenerate_history_pdf"
                    ):

                        try:

                            saved_vehicle = {
                                "make": record["make"],
                                "model": record["model"],
                                "year": record["year"],
                                "vin": record["vin"],
                                "mileage": record["mileage"],
                                "specification": record["specification"]
                            }

                            history_pdf = generate_pdf(
                                vehicle=saved_vehicle,
                                customer_name=record["customer_name"],
                                complaint=record["complaint"],
                                diagnosis=record["diagnosis"],
                                report_id=selected_report
                            )

                            st.download_button(
                                label="Download Historical PDF",
                                data=history_pdf,
                                file_name=f"{selected_report}.pdf",
                                mime="application/pdf",
                                key="history_pdf_download"
                            )

                        except Exception as error:

                            st.error(
                                f"Could not regenerate PDF: {error}"
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
        - Complaint-based diagnostic recommendations
        - Recommended vehicle modules
        - Recommended Live Data parameters
        - Recommended confirmation tests
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

        1. This is a prototype, not a production-ready system.
        2. Exact THINKDIAG 2 CSV compatibility must be tested with real exports.
        3. Generic parameter recognition does not replace OEM specifications.
        4. Scanned PDF OCR is not included.
        5. Uploaded videos are not analyzed by AI.
        6. SQLite storage is local and may not persist reliably on cloud hosting.
        7. User login, inspector permissions and report approval are not implemented.
        8. AI findings must be verified by a qualified inspector before repair decisions.

        ### Doctor Car

        Professional Vehicle Diagnostics  
        AI-Assisted Diagnostic Reports  
        Mobile Inspection Service Across UAE
        """
    )


# ==================================================
# END
# ==================================================
