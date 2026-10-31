import streamlit as strlit
import openai
import pandas as pd

# Page Config
strlit.set_page_config(page_title="Doctor Car - Pro Inspection AI", page_icon="🚗", layout="wide")

strlit.title("🚗 Doctor Car: Advanced Multi-System Live Data Diagnostic AI")
strlit.markdown("വണ്ടിയുടെ ലൈവ് ഡാറ്റ ലോഗുകൾ വിശകലനം ചെയ്ത് പ്രൊഫഷണൽ മെക്കാനിക് റിപ്പോർട്ട് തയ്യാറാക്കുന്ന ടൂൾ.")

# --- 1. OPENAI API KEY SETUP ---
with strlit.sidebar:
    strlit.header("⚙️ Configuration")
    api_key = strlit.text_input("Enter OpenAI API Key", type="password")
    strlit.markdown("---")
    strlit.info("ഇവിടെ നിങ്ങളുടെ OpenAI API Key നൽകിയാൽ ആപ്പ് കൃത്യമായി പ്രവർത്തിക്കും.")

# --- 2. VEHICLE DETAILS ---
strlit.header("1. Vehicle Information")
col1, col2, col3 = strlit.columns(3)

with col1:
    brand = strlit.selectbox("Vehicle Brand", ["Nissan", "Toyota", "Lexus", "Jeep", "BMW", "Mercedes", "Ford", "Other"])
    model = strlit.text_input("Model (e.g., Sunny / Pathfinder / Wrangler)")
with col2:
    year = strlit.number_input("Manufacture Year", min_value=1995, max_value=2026, value=2018)
    engine_type = strlit.text_input("Engine Specification (e.g., 1.5L Petrol / 3.5L V6)")
with col3:
    odometer = strlit.number_input("Odometer (KM)", min_value=0, value=120000, step=1000)
    vin = strlit.text_input("VIN / Chassis Number (Optional)", value="")

strlit.markdown("---")

# --- 3. CATEGORY-WISE CSV FILE UPLOADS ---
strlit.header("2. Upload System-Wise Live Data Logs (CSV)")
strlit.markdown("നിങ്ങൾക്ക് ആവശ്യമുള്ള സിസ്റ്റങ്ങളുടെ ലോഗ് ഫയലുകൾ മാത്രം താഴെ അപ്‌ലോഡ് ചെയ്യുക (ഒന്നോ അതിലധികമോ ചെയ്യാം):")

col_a, col_b = strlit.columns(2)

with col_a:
    engine_file = strlit.file_uploader("🔴 Engine Control Module (ECM) CSV", type=["csv", "txt"])
    trans_file = strlit.file_uploader("🔵 Transmission Control (TCM) CSV", type=["csv", "txt"])
    abs_file = strlit.file_uploader("🟠 ABS & Braking System CSV", type=["csv", "txt"])

with col_b:
    steering_file = strlit.file_uploader("🟡 Steering System CSV", type=["csv", "txt"])
    elec_file = strlit.file_uploader("🟣 Electrical & Charging (BCM) CSV", type=["csv", "txt"])
    susp_file = strlit.file_uploader("🟢 Suspension System CSV", type=["csv", "txt"])

strlit.markdown("---")

# --- 4. ANALYSIS & AI PROCESSING ---
if strlit.button("🚀 Analyze Vehicle Health & Generate Report", type="primary", use_container_width=True):
    if not api_key:
        strlit.error("⚠️ ദയവായി സൈഡ് ബാറിൽ നിങ്ങളുടെ OpenAI API Key നൽകുക!")
    elif not any([engine_file, trans_file, abs_file, steering_file, elec_file, susp_file]):
        strlit.warning("⚠️ കുറഞ്ഞത് ഏതെങ്കിലും ഒരു സിസ്റ്റത്തിന്റെ ലോഗ് ഫയൽ എങ്കിലും അപ്‌ലോഡ് ചെയ്യുക!")
    else:
        openai.api_key = api_key
        
        # Reading uploaded files data descriptions
        uploaded_data_summary = ""
        
        if engine_file:
            df_eng = pd.read_csv(engine_file)
            uploaded_data_summary += f"\n- Engine Data Preview: {df_eng.head(3).to_string()}"
        if trans_file:
            df_trans = pd.read_csv(trans_file)
            uploaded_data_summary += f"\n- Transmission Data Preview: {df_trans.head(3).to_string()}"
        if abs_file:
            df_abs = pd.read_csv(abs_file)
            uploaded_data_summary += f"\n- ABS Data Preview: {df_abs.head(3).to_string()}"
        if elec_file:
            df_elec = pd.read_csv(elec_file)
            uploaded_data_summary += f"\n- Electrical Data Preview: {df_elec.head(3).to_string()}"

        with strlit.spinner("🤖 AI എഞ്ചിൻ ഡാറ്റ വിശകലനം ചെയ്യുന്നു... ദയവായി കാത്തിരിക്കുക..."):
            
            prompt = f"""
            You are an expert Automotive Diagnostic Engineer assisting a professional pre-purchase vehicle inspector in Dubai.
            Vehicle Details: Brand: {brand}, Model: {model}, Year: {year}, Engine: {engine_type}, Odometer: {odometer} KM.
            
            Analyze the provided CSV log previews below and give a professional diagnostic report for each uploaded system. 
            For each system, provide:
            1. Health Score (out of 100%).
            2. Key Findings from the live data (mention specific PID values like MAP, Fuel Trims, TCC slip, Voltage, etc.).
            3. Root Cause of any drops in health (e.g., Vacuum leak, minor clutch wear, low voltage).
            4. Step-by-step physical inspection / repair recommendations for the mechanic.
            
            Data logs:
            {uploaded_data_summary}
            
            Format the output cleanly with appropriate headings and bullet points in Malayalam or professional English as requested.
            """
            
            try:
                client = openai.OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                report_output = response.choices[0].message.content
                
                strlit.success("✅ വിശകലനം വിജയകരമായി പൂർത്തിയായി!")
                strlit.header("📊 Doctor Car Professional Inspection Report")
                strlit.markdown(report_output)
                
            except Exception as e:
                strlit.error(f"പിഴവ് സംഭവിച്ചു: {e}")
