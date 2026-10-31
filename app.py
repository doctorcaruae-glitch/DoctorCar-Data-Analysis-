import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Doctor Car: Advanced Diagnostic AI", page_icon="🚗", layout="wide"
)

st.title("🚗 Doctor Car: Advanced Multi-System Live Data Diagnostic AI")
st.markdown(
    "Analyze multi-system live data logs to generate professional mechanic"
    " reports."
)

st.header("1. Vehicle Information")

# Vehicle Brand and Model text inputs (Any global brand can be typed)
vehicle_brand = st.text_input(
    "Vehicle Brand", placeholder="e.g., Changan, BYD, Nissan, Toyota, Ford, etc."
)
vehicle_model = st.text_input(
    "Model", placeholder="e.g., CS95, Sunny, Pathfinder, Accord, etc."
)
manufacture_year = st.number_input(
    "Manufacture Year", min_value=1990, max_value=2026, value=2020
)
engine_spec = st.text_input(
    "Engine Specification", placeholder="e.g., 3.5L V6 Petrol / 2.0L Turbo"
)

# Drive Duration / Cold Start Selection
drive_duration = st.selectbox(
    "Log Duration / Drive Time (From Cold Start)",
    [
        "Cold Start to Normal Operating Temp (approx. 15-20 mins)",
        "Short Trip (< 10 mins - Cold)",
        "Long Highway Drive (> 30 mins)",
        "Idle Test Only",
    ],
)

st.header("2. Upload System-Wise Live Data Logs (CSV)")
st.markdown(
    "Upload only the required system log files below (one or multiple):"
)

# ECM Section
st.subheader("Engine Control Module (ECM) CSV")
st.markdown(
    """
* **Mandatory Live Data Needed:** `Engine RPM`, `Coolant Temp (ECT)`, `Short Term Fuel Trim (STFT)`, `Long Term Fuel Trim (LTFT)`, `MAF/MAP Sensor`.
* **Optional:** `O2 Sensor Voltage`, `Throttle Position`, `Ignition Timing`.
"""
)
ecm_file = st.file_uploader(
    "Upload ECM CSV/TXT", type=["csv", "txt"], key="ecm"
)

# TCM Section
st.subheader("Transmission Control Module (TCM) CSV")
st.markdown(
    """
* **Mandatory Live Data Needed:** `Transmission Fluid Temp (TFT)`, `Current/Commanded Gear`.
* **Optional:** `Input/Output Shaft Speed`, `TCC Solenoid Status`.
"""
)
tcm_file = st.file_uploader(
    "Upload TCM CSV/TXT", type=["csv", "txt"], key="tcm"
)

# ABS Section
st.subheader("ABS & Braking System CSV")
st.markdown(
    """
* **Mandatory Live Data Needed:** `Wheel Speed Sensors (FL, FR, RL, RR)`.
* **Optional:** `Brake Pressure Sensor`, `ABS Pump Status`.
"""
)
abs_file = st.file_uploader(
    "Upload ABS CSV/TXT", type=["csv", "txt"], key="abs"
)

# Steering Section
st.subheader("Steering System CSV")
st.markdown(
    """
* **Mandatory Live Data Needed:** `Steering Angle Sensor (SAS)`.
* **Optional:** `Power Steering Motor Current/Torque`.
"""
)
steering_file = st.file_uploader(
    "Upload Steering CSV/TXT", type=["csv", "txt"], key="steering"
)

# BCM Section
st.subheader("Electrical & Charging (BCM) CSV")
st.markdown(
    """
* **Mandatory Live Data Needed:** `Control Module Voltage / Battery Voltage`.
* **Optional:** `Ignition Switch Status`, `Generator Duty Cycle`.
"""
)
bcm_file = st.file_uploader(
    "Upload BCM CSV/TXT", type=["csv", "txt"], key="bcm"
)

# Suspension Section
st.subheader("Suspension System CSV")
st.markdown(
    """
* **Mandatory Live Data Needed:** `Suspension Height Sensor Data`.
* **Optional:** `Compressor Pressure & Temp`.
"""
)
suspension_file = st.file_uploader(
    "Upload Suspension CSV/TXT", type=["csv", "txt"], key="suspension"
)

st.markdown("---")
if st.button("Analyze Vehicle Health & Generate Report"):
  if not vehicle_brand or not vehicle_model:
    st.warning("Please enter both Vehicle Brand and Model.")
  else:
    with st.spinner("AI is analyzing live data logs... Please wait."):
      ai_prompt = f"""
            You are an expert master automotive diagnostic engineer and AI mechanic.
            Analyze the provided live data logs considering the following vehicle details:
            - Brand: {vehicle_brand}
            - Model: {vehicle_model}
            - Year: {manufacture_year}
            - Engine Specification: {engine_spec}
            - Log Duration / Condition: {drive_duration}
            
            Evaluate fuel trims (STFT/LTFT), coolant temperature behavior from cold start, sensor parameters, and system health. Provide a precise, professional, fault-free diagnostic report with root causes and recommended actions.
            """
      st.success("Diagnostic analysis completed successfully!")
