
import os
import json
import base64
import mimetypes

import streamlit as st
from openai import OpenAI

from csv_analyzer import (
    build_csv_ai_summary,
    get_csv_text_for_ai
)


# --------------------------------------------------
# 1. AI SYSTEM INSTRUCTIONS
# --------------------------------------------------

SYSTEM_INSTRUCTIONS = """
You are Doctor Car's professional automotive diagnostic
assistant, supporting trained automotive inspectors
and diagnostic technicians.

Your main objective is to identify the most likely root
cause of a vehicle complaint using evidence from:

- Customer complaint
- Vehicle information
- DTCs from all available modules
- Freeze frame data
- Live data CSV
- Full scan information
- Physical inspection notes
- Inspection photographs

IMPORTANT DIAGNOSTIC PRINCIPLES:

1. Never invent DTC codes or descriptions.
2. Never invent live-data readings.
3. Never invent vehicle specifications.
4. Never invent OEM reference values.
5. Never treat missing or unavailable values as zero.
6. Never assume a parameter is supported unless verified.
7. A DTC alone does not prove component failure.
8. Do not recommend replacing a component based only
   on a DTC or one isolated live-data reading.
9. Separate observations, interpretations and conclusions.
10. Explain evidence supporting and contradicting each cause.
11. Give practical confirmation tests before recommending
    expensive or major component replacement.
12. Do not claim a vehicle is fault-free just because
    no DTC was found.
13. Do not claim a fault is confirmed unless the evidence
    actually confirms it.
14. Do not invent test results or claim tests were performed.
15. Do not invent numeric confidence percentages.
16. Use qualitative confidence descriptions only.
17. Do not invent expected OEM values.
18. Use OEM specifications only when supplied or verified.
19. Visual observations do not prove internal mechanical
    or electrical faults.
20. If evidence is insufficient, state that further
    diagnosis is required.

FINDING CLASSIFICATIONS:

- Confirmed
- Strongly Suspected
- Possible
- No Fault Detected
- Further Diagnosis Required
- Possible Tampering / Bypass

ROOT CAUSE RULES:

For every suspected cause:

- Explain the supporting evidence.
- Explain contradicting evidence.
- Identify missing evidence.
- State the next confirmation test.
- Explain what result would support or reject the cause.
- Do not recommend replacing a part until justified.

PART REPLACEMENT RULE:

A replacement recommendation must be based on a confirmed
failure or sufficiently strong diagnostic evidence.

If the component has not been tested, recommend testing
before replacement.

SAFETY RULES:

- Never instruct unqualified personnel to probe live SRS
  airbag or pretensioner circuits.
- Never recommend test lamps or ordinary resistance
  measurements on live SRS circuits.
- Follow manufacturer safety procedures for SRS,
  hybrid and EV high-voltage systems.
- Warn about hot coolant, rotating fans, moving belts,
  high fuel pressure and high-voltage components.
- Recommend qualified specialist inspection where needed.

TAMPERING / BYPASS RULE:

Do not claim that a resistor bypass, deleted thermostat,
software modification or other tampering is confirmed
from generic live data alone.

Classify it as suspected where evidence is incomplete
and recommend safe physical inspection and OEM procedures.

DATA RULES:

- Preserve units.
- Distinguish actual values from commanded values.
- Distinguish current, pending, history and permanent DTCs
  when that information is supplied.
- Distinguish a missing parameter from a normal reading.
- Consider engine temperature, RPM, load and operating
  conditions before interpreting readings.
- Do not compare readings from different operating
  conditions as if they were directly equivalent.
- Scanner data may be delayed, filtered or unsupported.

COMMUNICATION STYLE:

Use professional, clear and understandable language.
Explain technical findings so that a workshop technician
can act on them.
"""


# --------------------------------------------------
# 2. GET OPENAI API KEY
# --------------------------------------------------

def get_api_key():

    try:
        key = st.secrets.get(
            "OPENAI_API_KEY",
            ""
        )
    except Exception:
        key = ""

    return key or os.getenv(
        "OPENAI_API_KEY",
        ""
    )


# --------------------------------------------------
# 3. GET OPENAI MODEL
# --------------------------------------------------

def get_model():

    try:
        model = st.secrets.get(
            "OPENAI_MODEL",
            ""
        )
    except Exception:
        model = ""

    return model or os.getenv(
        "OPENAI_MODEL",
        "gpt-5.5"
    )


# --------------------------------------------------
# 4. CONNECT TO OPENAI
# --------------------------------------------------

def get_client():

    api_key = get_api_key()

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is missing. "
            "Please configure it in Streamlit Secrets."
        )

    return OpenAI(
        api_key=api_key,
        timeout=120.0,
        max_retries=2
    )


# --------------------------------------------------
# 5. SAFE TEXT CONVERSION
# --------------------------------------------------

def safe_text(value):

    if value is None:
        return "Not provided."

    if isinstance(value, str):
        return value.strip() or "Not provided."

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            default=str
        )
    except Exception:
        return str(value)


# --------------------------------------------------
# 6. FORMAT VEHICLE INFORMATION
# --------------------------------------------------

def vehicle_context(vehicle):

    return safe_text(vehicle)


# --------------------------------------------------
# 7. GENERATE DIAGNOSTIC QUESTIONS
# --------------------------------------------------

def generate_diagnostic_questions(
    vehicle,
    complaint
):

    client = get_client()

    prompt = f"""
DOCTOR CAR - DIAGNOSTIC PLAN

VEHICLE INFORMATION:
{vehicle_context(vehicle)}

CUSTOMER COMPLAINT:
{safe_text(complaint)}

TASK:

Create a practical diagnostic plan for this vehicle.

Return these sections:

1. CUSTOMER CLARIFICATION QUESTIONS

Ask questions that help identify:
- When the issue occurs
- Cold or hot engine conditions
- Idle, acceleration or cruising conditions
- Whether the issue is continuous or intermittent
- Recent repairs or component replacements
- Warning lights and related symptoms

Avoid asking questions that are irrelevant to this complaint.

2. INSPECTOR QUESTIONS

List the important things the inspector must verify.

3. PHYSICAL INSPECTION CHECKLIST

Give practical inspection steps.

4. CONTROL MODULES TO SCAN

Recommend only relevant modules.

Possible modules include:
- Engine
- Transmission
- ABS / ESC
- SRS / Airbag
- EPS
- HVAC
- AWD / 4WD
- ADAS
- BCM / Body Electrical
- Battery / Charging
- Hybrid / EV
- TPMS

5. LIVE DATA PARAMETERS

Group parameters by module.

Classify each as:
- Must Have
- Optional
- Vehicle Dependent

For each parameter explain briefly why it is useful.

Do not claim that the vehicle supports a parameter
unless verified using the scanner.

6. PHYSICAL CONFIRMATION TESTS

List tests needed to distinguish the most likely causes.

7. SAFETY PRECAUTIONS

Mention relevant risks and safe inspection procedures.

8. DIAGNOSTIC SEQUENCE

Give the recommended order of work.

Keep the plan practical for a mobile diagnostic
and inspection service.

Do not invent OEM specifications or readings.
"""


    response = client.responses.create(
        model=get_model(),
        instructions=SYSTEM_INSTRUCTIONS,
        input=prompt
    )

    return response.output_text


# --------------------------------------------------
# 8. PREPARE CSV DATA FOR AI
# --------------------------------------------------

def prepare_csv_context(module_data):

    module_data = module_data or {}

    summary = build_csv_ai_summary(
        module_data
    )

    samples = []

    for module, result in module_data.items():

        csv_text = get_csv_text_for_ai(
            result,
            max_rows=120
        )

        samples.append(
            f"""
MODULE: {module}

FILE: {result.get("file_name", "Unknown")}

CSV DATA:
{csv_text}
"""
        )

    return summary, "\n".join(samples)


# --------------------------------------------------
# 9. PREPARE IMAGE INPUT
# --------------------------------------------------

def prepare_image_content(image_files):

    content = []

    for uploaded_image in (image_files or [])[:8]:

        try:

            image_bytes = uploaded_image.getvalue()

            if not image_bytes:
                continue

            mime_type = (
                getattr(uploaded_image, "type", None)
                or mimetypes.guess_type(
                    getattr(uploaded_image, "name", "")
                )[0]
                or "image/jpeg"
            )

            if mime_type not in [
                "image/jpeg",
                "image/png",
                "image/webp",
                "image/gif"
            ]:
                continue

            encoded_image = base64.b64encode(
                image_bytes
            ).decode("utf-8")

            content.append({
                "type": "input_image",
                "image_url": (
                    f"data:{mime_type};base64,{encoded_image}"
                )
            })

        except Exception:
            continue

    return content


# --------------------------------------------------
# 10. BUILD DATA QUALITY CONTEXT
# --------------------------------------------------

def build_data_quality_context(module_data):

    output = []

    for module, result in (module_data or {}).items():

        quality = result.get(
            "data_quality",
            {}
        )

        required = result.get(
            "required_parameters",
            {}
        )

        output.append(
            f"""
MODULE: {module}

Rows: {result.get("rows", 0)}

Recognized parameters:
{len(result.get("summary", {}))}

Unmapped columns:
{safe_text(result.get("unmapped", []))}

Missing required parameters:
{safe_text(required.get("missing", []))}

Data quality information:
{safe_text(quality)}
"""
        )

    return "\n".join(output) or "No CSV data supplied."


# --------------------------------------------------
# 11. COMPLETE VEHICLE DIAGNOSTIC ANALYSIS
# --------------------------------------------------

def analyze_vehicle(
    vehicle,
    complaint,
    answers,
    module_data,
    dtc_text,
    freeze_frame_text,
    scan_text,
    physical_notes,
    image_files=None
):

    client = get_client()

    module_data = module_data or {}

    csv_summary, csv_samples = prepare_csv_context(
        module_data
    )

    data_quality = build_data_quality_context(
        module_data
    )

    prompt = f"""
DOCTOR CAR - COMPLETE VEHICLE DIAGNOSTIC CASE

==================================================
1. VEHICLE INFORMATION
==================================================

{vehicle_context(vehicle)}


==================================================
2. CUSTOMER COMPLAINT
==================================================

{safe_text(complaint)}


==================================================
3. INSPECTOR ANSWERS
==================================================

{safe_text(answers)}


==================================================
4. LIVE DATA SUMMARY
==================================================

{safe_text(csv_summary)}


==================================================
5. LIVE DATA QUALITY
==================================================

{data_quality}


==================================================
6. RAW LIVE DATA SAMPLES
==================================================

{safe_text(csv_samples)}


==================================================
7. DTC AND FULL SCAN INFORMATION
==================================================

{safe_text(dtc_text)}


==================================================
8. FREEZE FRAME DATA
==================================================

{safe_text(freeze_frame_text)}


==================================================
9. FULL SCAN PDF TEXT
==================================================

{safe_text(scan_text)}


==================================================
10. PHYSICAL INSPECTION NOTES
==================================================

{safe_text(physical_notes)}


==================================================
11. REQUIRED DIAGNOSTIC REPORT
==================================================

Prepare a detailed, evidence-based diagnostic report
using the following structure.

A. EXECUTIVE SUMMARY

Explain the main complaint and the most important findings.

B. VEHICLE AND CUSTOMER COMPLAINT

Summarize vehicle details and reported symptoms.

C. DATA QUALITY AND LIMITATIONS

Explain:
- Data received
- Recognized parameters
- Missing required parameters
- Missing readings
- Unmapped scanner values
- Unavailable or unsupported parameters
- Whether readings cover the relevant operating conditions
- Limitations of the available evidence

Do not treat missing data as a normal result.

D. MODULE-BY-MODULE FINDINGS

Analyze each supplied module separately.

Do not assume that an unscanned module has no fault.

E. DTC INTERPRETATION

For every supplied DTC explain:
- Code and supplied description
- Module
- Status, if supplied
- What the code actually indicates
- Possible causes
- What it does NOT prove
- Recommended confirmation test

Never invent missing DTC descriptions.

F. LIVE DATA ANALYSIS

For each relevant parameter explain:
- Actual supplied readings
- Units
- Minimum / Maximum / Average where useful
- Trend
- Operating conditions
- Whether the data is sufficient for a conclusion

Compare operating conditions only when the data supports
a fair comparison.

G. ROOT CAUSE ANALYSIS

Rank the possible causes from most supported to least supported.

For each cause include:

- Finding classification
- Explanation
- Supporting evidence
- Contradicting evidence
- Missing evidence
- What remains unverified
- Next confirmation test

Use qualitative confidence only:
High / Medium / Low.

Do not invent percentages.

H. CONFIRMATION TEST PLAN

Give a practical step-by-step test sequence.

For every test explain:
- What to inspect or measure
- Why the test is needed
- What result would support the suspected cause
- What result would reject or weaken the suspected cause

Use manufacturer procedures and specifications
where available.

I. REPAIR DIRECTION

Separate recommendations into:

1. Confirmed repair
2. Repair only after confirmation
3. Further diagnosis required

Do not recommend replacing parts without evidence.

Where several causes remain possible, explain how
to distinguish them before spending money.

J. SAFETY CONCERNS

Highlight safety-critical findings and required precautions.

K. LIMITATIONS

Mention tests not performed and information not supplied.

L. CUSTOMER-FRIENDLY CONCLUSION

Explain the result in simple professional language.

M. FINAL DIAGNOSTIC STATUS

Choose one:

- Confirmed
- Strongly Suspected
- Possible
- No Fault Detected
- Further Diagnosis Required
- Possible Tampering / Bypass

Explain why this status was selected.

IMPORTANT FINAL RULES:

- Separate facts from interpretations.
- Do not invent readings or test results.
- Do not invent OEM reference values.
- Do not claim a test was performed if it was not.
- Do not interpret missing readings as zero.
- Do not claim No Fault Detected means no fault exists.
- Do not confirm tampering from generic live data alone.
- Do not recommend a part replacement solely from a DTC.
- Do not create a numeric vehicle health score.
- If evidence is insufficient, recommend further diagnosis.
"""


    # --------------------------------------------------
    # BUILD OPENAI INPUT
    # --------------------------------------------------

    content = [
        {
            "type": "input_text",
            "text": prompt
        }
    ]

    image_content = prepare_image_content(
        image_files
    )

    content.extend(image_content)


    # --------------------------------------------------
    # SEND COMPLETE CASE TO OPENAI
    # --------------------------------------------------

    response = client.responses.create(
        model=get_model(),
        instructions=SYSTEM_INSTRUCTIONS,
        input=[
            {
                "role": "user",
                "content": content
            }
        ]
    )

    return response.output_text
