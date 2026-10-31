import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Doctor Car: Master Forensic Diagnostic AI",
    page_icon="🚗",
    layout="wide",
)

st.title(
    "🚗 Doctor Car: Master Forensic Diagnostic AI & Complete Vehicle Inspector"
)
st.markdown(
    "Comprehensive multi-system live data analysis, parameter selection"
    " guides, physical photo inspection, interactive AI diagnostics, and 100%"
    " accurate professional reporting."
)

# 1. Vehicle & Inspection Basic Information
st.header("1. Vehicle & Inspection Basic Information")
col1, col2 = st.columns(2)
with col1:
  vehicle_brand = st.text_input(
      "Vehicle Brand",
      placeholder="e.g., Nissan, Land Rover, Toyota, Honda, Ford, etc.",
  )
  vehicle_model = st.text_input(
      "Model", placeholder="e.g., Pathfinder, Accord, Discovery, Wrangler, etc."
  )
  manufacture_year = st.number_input(
      "Manufacture Year", min_value=1990, max_value=2026, value=2020
  )
with col2:
  engine_spec = st.text_input(
      "Engine Specification & Fuel Type",
      placeholder="e.g., 2.0L Turbo / 3.5L V6 Petrol / Diesel",
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

# 2. Module Parameter Guides & File Uploaders
st.header(
    "2. Multi-Module Live Data Logs (CSV/PDF) & Mandatory Parameter Checklists"
)
st.markdown(
    "Ensure you select these exact parameters from your scanner (Autel /"
    " ThinkDiag) before exporting logs:"
)

# Module 1: ECM
with st.expander(
    "1. Engine ECU (ECM) - Mandatory & Optional Parameters Guide"
):
  st.markdown("""
    * **🔴 Mandatory Parameters:** `Engine RPM` (Idle: 650-800), `Coolant Temp (ECT)` (85-105°C), `STFT Bank 1/2` (-10% to +10%), `LTFT Bank 1/2` (-10% to +10%), `MAF Sensor (g/s)` or `MAP Sensor (kPa)`, `Barometric Pressure`.
    * **🟡 Optional Parameters:** `O2 Sensor Voltage`, `Ignition Timing Advance`, `Fuel Rail Pressure`, `Misfire Count`, `Engine Load (%)`.
    """)
ecm_file = st.file_uploader(
    "Upload Engine ECM Log (CSV / TXT / PDF)",
    type=["csv", "txt", "pdf"],
    key="ecm",
)

# Module 2: TCM
with st.expander(
    "2. Transmission ECU (TCM) - Mandatory & Optional Parameters Guide"
):
  st.markdown("""
    * **🔴 Mandatory Parameters:** `ATF Temperature` (70-95°C), `Current Gear`, `Commanded Gear`.
    * **🟡 Optional Parameters:** `Input/Output Shaft Speed`, `Torque Converter Slip (RPM)`, `Shift Solenoid Status`.
    """)
tcm_file = st.file_uploader(
    "Upload Transmission TCM Log (CSV / TXT / PDF)",
    type=["csv", "txt", "pdf"],
    key="tcm",
)

# Module 3: ABS & Brakes
with st.expander(
    "3. ABS & Braking System - Mandatory & Optional Parameters Guide"
):
  st.markdown("""
    * **🔴 Mandatory Parameters:** `Wheel Speed Sensors (FL, FR, RL, RR)` (Crucial for ABS/Traction faults), `Brake Pressure Sensor`.
    * **🟡 Optional Parameters:** `ABS Pump Motor Status`, `Yaw Rate / Lateral Acceleration Sensor`.
    """)
abs_file = st.file_uploader(
    "Upload ABS & Braking Log (CSV / TXT / PDF)",
    type=["csv", "txt", "pdf"],
    key="abs",
)

# Module 4: SRS
with st.expander(
    "4. SRS / Airbag Module - Mandatory Guide (Tampering & Resistor Detection)"
):
  st.markdown("""
    * **🔴 Mandatory Parameters:** `Airbag Deployment Status`, `Crash Event Memory Stored`, `Warning Lamp (SRS) Status`.
    * **🟡 Optional Parameters:** `Squib / Resistor Resistance Values` (Used to detect simulated resistors or diodes hiding deployed airbags).
    """)
srs_file = st.file_uploader(
    "Upload SRS / Airbag Log (CSV / TXT / PDF)",
    type=["csv", "txt", "pdf"],
    key="srs",
)

# Module 5: EPS & Suspension
with st.expander("5. Steering (EPS) & Suspension - Parameter Guide"):
  st.markdown(
      "* **🔴 Mandatory Parameters:** `Steering Angle Sensor`, `Steering Torque"
      " Sensor`, `EPS Motor Current`."
  )
eps_file = st.file_uploader(
    "Upload Steering EPS Log (CSV / TXT / PDF)",
    type=["csv", "txt", "pdf"],
    key="eps",
)

# Module 6: HVAC & AC
with st.expander("6. HVAC / AC System - Parameter Guide"):
  st.markdown("""
    * **🔴 Mandatory Parameters:** `Evaporator Temperature` (2-7°C), `AC Compressor Pressure / Command`, `Blower Speed`.
    * **🟡 Optional Parameters:** `Blend Door Position`, `Ambient Air Temperature`.
    """)
hvac_file = st.file_uploader(
    "Upload HVAC Log (CSV / TXT / PDF)", type=["csv", "txt", "pdf"], key="hvac"
)

# Module 7: 4WD / AWD
with st.expander("7. 4WD / AWD Drivetrain - Parameter Guide"):
  st.markdown(
      "* **🔴 Mandatory Parameters:** `Transfer Case Mode`, `Clutch Engagement"
      " Status (%)`, `Front/Rear Axle Speeds`."
  )
awd_file = st.file_uploader(
    "Upload 4WD / AWD Log (CSV / TXT / PDF)",
    type=["csv", "txt", "pdf"],
    key="awd",
)

# Module 8: BCM & Electrical
with st.expander("8. BCM & Electrical - Parameter Guide"):
  st.markdown(
      "* **🔴 Mandatory Parameters:** `Battery Voltage` (Running: 13.5-14.5V),"
      " `Ignition Switch Status`."
  )
bcm_file = st.file_uploader(
    "Upload BCM Log (CSV / TXT / PDF)", type=["csv", "txt", "pdf"], key="bcm"
)

# Module 9: ADAS
with st.expander("9. ADAS & Sensors - Parameter Guide"):
  st.markdown(
      "* **🔴 Mandatory Parameters:** `Radar & Camera Calibration Status`,"
      " `Obstacle Distance DTCs`."
  )
adas_file = st.file_uploader(
    "Upload ADAS Log (CSV / TXT / PDF)", type=["csv", "txt", "pdf"], key="adas"
)

# Module 10: Full Scan PDF
with st.expander("10. Full System Health Check Report - Upload"):
  st.markdown(
      "Upload full vehicle health scan PDF containing overall DTCs & Readiness"
      " monitors."
  )
full_scan_file = st.file_uploader(
    "Upload Full Scan Report (PDF / TXT / CSV)",
    type=["pdf", "txt", "csv"],
    key="full_scan",
)

# 11. Component Photo Upload
st.subheader(
    "📸 Upload Physical Component Photos (Visual Anomaly Verification)"
)
component_images = st.file_uploader(
    "Upload photos of physical damage, oil leaks, airbag tampering, or bulging"
    " components (JPG, PNG)",
    type=["jpg", "png", "jpeg"],
    accept_multiple_files=True,
    key="images",
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
        st.line
