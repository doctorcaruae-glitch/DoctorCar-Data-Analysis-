import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Doctor Car: Advanced Diagnostic AI", page_icon="🚗", layout="wide"
)

st.title("🚗 Doctor Car: Advanced Multi-System Live Data Diagnostic AI")
st.markdown(
    "Analyze professional multi-system live data logs, detect exact fault"
    " locations, physical deformations, and lookup DTCs."
)

st.header("1. Vehicle Basic Information")

# Global vehicle brand and model inputs
vehicle_brand = st.text_input(
    "Vehicle Brand",
    placeholder="e.g., Land Rover, Nissan, Changan, Toyota, Ford, etc.",
)
vehicle_model = st.text_input(
    "Model", placeholder="e.g., Discovery Sport, Pathfinder, Sunny, CS95, etc."
)
manufacture_year = st.number_input(
    "Manufacture Year", min_value=1990, max_value=2026, value=2020
)
engine_spec = st.text_input(
    "Engine Specification & Fuel Type",
    placeholder="e.g., 2.0L Turbo Petrol / 3.5L V6",
)
spec_region = st.selectbox(
    "Vehicle Specification Region",
    ["GCC Spec", "American Spec", "Japanese Spec", "European Spec", "Other"],
)

# Drive Duration / Cold Start Selection
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
    "2. Upload System-Wise Live Data Logs & Module Status (CSV / Text)"
)
st.markdown(
    "Upload the required system logs and diagnostic scan exports to enable"
    " deep AI inspection:"
)

# ECM Section
st.subheader("1. Engine ECU (ECM) - Live Data & DTCs")
st.markdown(
    """
* **Mandatory Live Data:** `Engine RPM`, `Coolant Temp (ECT)`, `Short Term Fuel Trim (STFT)`, `Long Term Fuel Trim (LTFT)`, `MAF/MAP Sensor`, `Barometric Pressure`.
* **Optional / Advanced:** `O2 Sensor Voltage`, `Fuel Level Input`, `Ignition Timing`, `Misfire Count`[span_0](start_span)[span_0](end_span)[span_1](start_span)[span_1](end_span)[span_2](start_span)[span_2](end_span).
"""
)
ecm_file = st.file_uploader(
    "Upload Engine ECM CSV/TXT", type=["csv", "txt"], key="ecm"
)

# TCM Section
st.subheader("2. Transmission ECU (TCM)")
st.markdown(
    """
* **Mandatory Data:** `Transmission Fluid Temperature (ATF)`, `Current Gear`, `Commanded Gear`.
* **Optional:** `Input/Output Shaft Speed`, `Torque Converter Slip`[span_3](start_span)[span_3](end_span).
"""
)
tcm_file = st.file_uploader(
    "Upload Transmission TCM CSV/TXT", type=["csv", "txt"], key="tcm"
)

# ECU Diagnostic Info & Readiness
st.subheader("3. ECU Diagnostic Info & OBD Readiness")
st.markdown(
    """
* **Check Includes:** Confirmed/Pending/Permanent DTCs, Freeze Frame Data, MIL Status[span_4](start_span)[span_4](end_span).
* **Readiness Monitors:** Misfire, Fuel System, Catalyst, Oxygen Sensor, EVAP monitors[span_5](start_span)[span_5](end_span).
"""
)
dtc_file = st.file_uploader(
    "Upload DTC & Readiness Report (TXT/CSV)", type=["txt", "csv"], key="dtc"
)

# Safety & Other Modules (SRS, ABS, BCM, TPMS)
st.subheader("4. Safety & Other Modules (SRS, ABS, BCM, TPMS)")
st.markdown(
    """
* **SRS / Airbags Check:** Airbag DTCs, deployment status, and warning light check (detects simulated resistors/diodes hiding crash history)[span_6](start_span)[span_6](end_span).
* **ABS & Braking:** Wheel speed sensors, hydraulic pressure[span_7](start_span)[span_7](end_span).
* **Other Systems:** EPS (Steering), BCM, TPMS, HVAC[span_8](start_span)[span_8](end_span).
"""
)
safety_file = st.file_uploader(
    "Upload Full System Scan / Safety Modules Report (TXT/CSV)",
    type=["txt", "csv"],
    key="safety",
)

# Ask AI / Specific DTC Lookup & Complex Symptom Description
st.header("3. Ask AI: Specific DTC Code or Complex Vehicle Symptom")
st.markdown(
    "Describe complex symptoms (e.g., fuel gauge showing wrong percentage due to"
    " tank deformation/bulging, floating issues, or specific OBD codes like"
    " P0171):"
)
custom_dtc_input = st.text_input(
    "Enter Trouble Codes, Fuel Gauge Errors, or Physical Symptoms",
    placeholder=(
        "e.g., Discovery Sport fuel gauge stuck at 45% due to deformed/bulged"
        " tank or sensor jam"
    ),
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
        "AI Master Diagnostic Engineer is analyzing multi-system logs, physical"
        " tank/sensor anomalies, and root causes... Please wait."
    ):
      ai_prompt = f"""
            You are an expert master automotive diagnostic engineer and AI forensic vehicle inspector.
            Perform a comprehensive health analysis of the vehicle based on the following details and logs:
            
            - Brand: {vehicle_brand}
            - Model: {vehicle_model}
            - Year: {manufacture_year}
            - Engine & Fuel: {engine_spec}
            - Region Spec: {spec_region}
            - Drive Condition: {drive_duration}
            - Specific User Query / Complex Symptom: {custom_dtc_input}
            
            Special Diagnostic Guidelines to Follow:
            1. Physical & Mechanical Anomalies: Consider hidden structural issues such as fuel tank bulging/deformation causing physical binding of the fuel level sender float (e.g., false fuel percentage readings like showing 45% when empty, or inverse readings when adding fuel).
            2. Sensor vs Physical Mismatch: Analyze discrepancies between live data fuel level inputs and actual physical tank conditions.
            3. Pinpoint exact fault locations: Differentiate between electrical sensor failures, wiring issues, fuel pump assembly problems, and physical tank/mounting misalignments.
            4. Engine ECM & Fuel Trims: Evaluate STFT/LTFT, MAF/MAP, barometric pressure, misfires[span_9](start_span)[span_9](end_span)[span_10](start_span)[span_10](end_span)[span_11](start_span)[span_11](end_span).
            5. ECU Readiness & DTC Clearing: Check if codes were recently cleared to hide active problems[span_12](start_span)[span_12](end_span)[span_13](start_span)[span_13](end_span).
            6. SRS / Airbag Tampering Check: Inspect for resistor/diode bypass methods hiding deployed airbags[span_14](start_span)[span_14](end_span).
            7. Other Module Statuses (ABS, BCM, EPS, AWD)[span_15](start_span)[span_15](end_span).
            
            Provide a strict, professional, fault-free diagnostic report structured like an official pre-purchase inspection report, covering both electronic data and physical/mechanical mechanical failure modes.
            """
      st.success(
          "Diagnostic & Forensic Health Analysis Completed Successfully!"
      )
