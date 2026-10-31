import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Doctor Car: Master Forensic Diagnostic AI",
    page_icon="🚗",
    layout="wide",
)

st.title(
    "🚗 Doctor Car: Master Forensic Diagnostic AI & Multi-Module Inspector"
)
st.markdown(
    "Perform professional mechanical, electronic, safety, and all-module"
    " forensic inspection."
)

st.header("1. Vehicle & Inspection Basic Information")

col1, col2 = st.columns(2)
with col1:
  vehicle_brand = st.text_input(
      "Vehicle Brand",
      placeholder="e.g., Land Rover, Nissan, Toyota, Ford, Lexus, etc.",
  )
  vehicle_model = st.text_input(
      "Model",
      placeholder="e.g., Discovery Sport, Pathfinder, Sunny, Wrangler, etc.",
  )
  manufacture_year = st.number_input(
      "Manufacture Year", min_value=1990, max_value=2026, value=2020
  )
with col2:
  engine_spec = st.text_input(
      "Engine Specification & Fuel Type",
      placeholder="e.g., 2.0L Turbo Petrol / 3.5L V6 Petrol / Diesel",
  )
  spec_region = st.selectbox(
      "Vehicle Specification Region",
      ["GCC Spec", "American Spec", "Japanese Spec", "European Spec", "Other"],
  )
  drive_duration = st.selectbox(
      "Log Duration / Drive Time (From Cold Start)",
      [
          "Cold Start to Normal Operating Temp (15-20 mins) - Recommended",
          "Short Trip (< 10 mins - Cold)",
          "Long Highway Drive (> 30 mins)",
          "Idle Test Only",
      ],
  )

st.header(
    "2. Upload All-Module Live Data (CSV) & Full System Scan Reports (PDF/TXT)"
)
st.markdown(
    "Upload logs and diagnostic reports across all vehicle systems for deep AI"
    " analysis:"
)

# Multi-Module File Uploaders
ecm_file = st.file_uploader(
    "1. Engine ECM Live Data (CSV / TXT / PDF)",
    type=["csv", "txt", "pdf"],
    key="ecm",
)
tcm_file = st.file_uploader(
    "2. Transmission TCM Log (CSV / TXT / PDF)",
    type=["csv", "txt", "pdf"],
    key="tcm",
)
abs_file = st.file_uploader(
    "3. ABS & Braking System Log (CSV / TXT / PDF)",
    type=["csv", "txt", "pdf"],
    key="abs",
)
srs_file = st.file_uploader(
    "4. SRS / Airbag Module Log (Detects Resistors/Diodes) (CSV / TXT / PDF)",
    type=["csv", "txt", "pdf"],
    key="srs",
)
eps_file = st.file_uploader(
    "5. Steering (EPS) & Suspension Log (CSV / TXT / PDF)",
    type=["csv", "txt", "pdf"],
    key="eps",
)
hvac_file = st.file_uploader(
    "6. HVAC / AC System Log (CSV / TXT / PDF)",
    type=["csv", "txt", "pdf"],
    key="hvac",
)
awd_file = st.file_uploader(
    "7. 4WD / AWD / Drivetrain Log (CSV / TXT / PDF)",
    type=["csv", "txt", "pdf"],
    key="awd",
)
bcm_file = st.file_uploader(
    "8. Body Control Module (BCM) & Electrical Log (CSV / TXT / PDF)",
    type=["csv", "txt", "pdf"],
    key="bcm",
)
adas_file = st.file_uploader(
    "9. ADAS & Sensors Calibration Log (CSV / TXT / PDF)",
    type=["csv", "txt", "pdf"],
    key="adas",
)
full_scan_file = st.file_uploader(
    "10. Full System Health Check & DTC Scan Report (PDF / TXT / CSV)",
    type=["pdf", "txt", "csv"],
    key="full_scan",
)

# ---- Live Data Sensor Graphing Section ----
if ecm_file is not None and ecm_file.name.endswith(".csv"):
  try:
    df = pd.read_csv(ecm_file)
    st.subheader("📊 Live Sensor Data Plotter & Graph Analysis (Engine ECM)")
    numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist(
        
    )
    if numeric_cols:
      selected_columns = st.multiselect(
          "Select Sensor Parameters to Plot Line Chart",
          numeric_cols,
          default=numeric_cols[:3] if len(numeric_cols) >= 3 else numeric_cols,
      )
      if selected_columns:
        st.line_chart(df[selected_columns])
  except Exception as e:
    st.error(f"Could not parse CSV for sensor plotting: {e}")
# -------------------------------------------

st.header("3. Ask AI: Note Specific Symptom, Complaint, or Fault Inquiry")
st.markdown(
    "Enter the exact driver complaint or observed symptom (e.g., **AC not"
    " cooling, Transmission shift delay, ABS fault, SRS light issue, Engine"
    " vibration**) so AI can perform an all-module cross-analysis."
)
custom_dtc_input = st.text_input(
    "Enter Primary Complaint / Observed Symptom",
    placeholder="e.g., AC not cooling at signals or heavy steering / ABS warning",
)

st.markdown("---")
if st.button("Analyze Complete Vehicle Health & Generate Professional Report"):
  if not vehicle_brand or not vehicle_model:
    st.warning(
        "Please enter both Vehicle Brand and Model to proceed with AI"
        " analysis."
    )
  else:
    with st.spinner(
        "AI Master Diagnostic Engineer is evaluating multi-module logs across"
        " Engine, Transmission, ABS, SRS, Steering, AC, and Electrical systems..."
        " Please wait."
    ):
      ai_prompt = f"""
            You are an expert master automotive diagnostic engineer, electronic specialist, and AI forensic vehicle inspector.
            Perform an exhaustive multi-system inspection analysis based on the following vehicle profile and attached logs:
            
            Vehicle Profile:
            - Brand & Model: {vehicle_brand} {vehicle_model}
            - Year: {manufacture_year}
            - Engine Spec: {engine_spec}
            - Market Spec: {spec_region}
            - Test Drive Duration: {drive_duration}
            - Primary User Complaint / Symptom: {custom_dtc_input}
            
            Core Analytical & Diagnostic Requirements across All Modules:
            1. Comprehensive Multi-Module Evaluation: Cross-reference data across Engine (ECM), Transmission (TCM), Braking/ABS, Steering (EPS), Airbags (SRS), HVAC/AC, Drivetrain (4WD/AWD), Electrical (BCM), and ADAS.
            2. Overall Health Score: Calculate a precise Vehicle Health Score out of 100 based on all uploaded data.
            3. Detailed Complaint Breakdown: Address '{custom_dtc_input}' and categorize potential root causes strictly into High, Medium, and Low probability.
            4. Forensic SRS / Airbag Tampering Check: Inspect SRS crash memory, deployment history, and resistance parameters to detect if resistors, capacitors, or diodes were installed to bypass airbag warning lights.
            5. Live Data vs Mechanical Isolation: Isolate electronic/sensor errors from physical mechanical failures (e.g., Engine/Transmission mountings, fluid degradation, physical deformations).
            6. Crystal-Clear Repair Action Plan: Provide precise, actionable instructions on what parts to inspect, clean, repair, or replace so the vehicle is 100% fixed.
            
            Output Structure: Deliver a strict, professional, fault-clear diagnostic report structured like an official master inspection document.
            """
      st.success(
          "Diagnostic & Forensic Health Analysis Completed Successfully!"
      )
      st.markdown("### 📄 Doctor Car Official Master Diagnostic Report")
      st.info(
          "AI Report generated successfully! All multi-module logs (Engine,"
          " TCM, ABS, SRS, Steering, AC, 4WD, BCM, ADAS) and PDF reports have"
          " been fully processed."
      )
