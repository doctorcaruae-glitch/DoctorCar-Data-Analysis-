
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
You are Doctor Car's professional automotive diagnostic assistant.

Your role is to support trained vehicle inspectors
during pre-purchase vehicle inspections.

STRICT DIAGNOSTIC RULES:

1. Never invent DTC codes or descriptions.
2. Never invent live-data readings.
3. Never invent vehicle specifications.
4. Never invent OEM reference values.
5. Missing values must NEVER be treated as zero.
6. Unsupported parameters must be identified as unsupported
   or unavailable, not as a fault.
7. A DTC alone does not prove that a component has failed.
8. Never recommend replacing a component based only on a DTC.
9. Separate confirmed facts from possible explanations.
10. Explain evidence supporting and contradicting each finding.
11. Give practical next diagnostic tests in the correct sequence.
12. Do not claim that a vehicle is fault-free simply because
    no DTC was found.
13. Clearly mention limitations and unavailable data.
14. Safety-critical faults must be highlighted.
15. Do not invent vehicle-specific expected readings.
16. Only use OEM specifications when a verified source
    is provided.
17. Visual observations from photos are not proof of
    internal mechanical or electrical faults.
18. Do not invent a numeric vehicle health score.
19. If evidence is insufficient, state that further
    diagnosis is required.

FINDING CLASSIFICATIONS:

- Confirmed
- Strongly Suspected
- Possible
- No Fault Detected
- Further Diagnosis Required

Use professional but understandable language.
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
        api_key=api_key
    )


# --------------------------------------------------
# 5. FORMAT VEHICLE INFORMATION
# --------------------------------------------------

def vehicle_context(vehicle):

    return json.dumps(
        vehicle or {},
        ensure_ascii=False,
        indent=2,
        default=str
    )


# --------------------------------------------------
# 6. GENERATE DIAGNOSTIC QUESTIONS
# --------------------------------------------------

def generate_diagnostic_questions(
    vehicle,
    complaint
):

    client = get_client()

    prompt = f"""
VEHICLE INFORMATION:

{vehicle_context(vehicle)}

CUSTOMER COMPLAINT:

{complaint}

TASK:

Prepare a practical diagnostic and inspection plan
for this vehicle and complaint.

Return the following sections:

1. CUSTOMER CLARIFICATION QUESTIONS

Questions that help understand the complaint.

2. INSPECTOR QUESTIONS

Questions the inspector should ask or verify.

3. PHYSICAL INSPECTION CHECKLIST

Practical checks to perform on the vehicle.

4. CONTROL MODULES TO SCAN

Identify relevant modules such as:

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
- Other available OEM modules

Only recommend modules relevant to the vehicle
and complaint.

5. LIVE DATA PARAMETERS

Group parameters by module.

Classify each parameter as:

- Must Have
- Optional
- Vehicle Dependent

IMPORTANT:

Do not claim that a parameter is supported by the vehicle
unless verified.

Label generic suggestions as scanner/vehicle dependent.

6. SAFETY PRECAUTIONS

Mention any safety precautions relevant to the inspection.

Keep the plan practical for a mobile pre-purchase
vehicle inspection.
"""

    response = client.responses.create(

        model=get_model(),

        instructions=SYSTEM_INSTRUCTIONS,

        input=prompt

    )

    return response.output_text


# --------------------------------------------------
# 7. PREPARE CSV DATA FOR AI
# --------------------------------------------------

def prepare_csv_context(module_data):

    summary = build_csv_ai_summary(
        module_data or {}
    )

    samples = []

    for module, result in (
        module_data or {}
    ).items():

        csv_text = get_csv_text_for_ai(
            result,
            max_rows=120
        )

        samples.append(
            f"""
MODULE: {module}

CSV DATA:

{csv_text}
"""
        )

    return summary, "\n".join(samples)


# --------------------------------------------------
# 8. PREPARE IMAGE INPUT
# --------------------------------------------------

def prepare_image_content(image_files):

    content = []

    for uploaded_image in (
        image_files or []
    )[:8]:

        try:

            image_bytes = uploaded_image.getvalue()

            mime_type = (
                getattr(
                    uploaded_image,
                    "type",
                    None
                )
                or mimetypes.guess_type(
                    getattr(
                        uploaded_image,
                        "name",
                        ""
                    )
                )[0]
                or "image/jpeg"
            )

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
# 9. COMPLETE VEHICLE DIAGNOSTIC ANALYSIS
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

    csv_summary, csv_samples = prepare_csv_context(
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

{complaint}


==================================================
3. INSPECTOR ANSWERS
==================================================

{answers}


==================================================
4. LIVE DATA SUMMARY
==================================================

{csv_summary}


==================================================
5. RAW LIVE DATA SAMPLES
==================================================

{csv_samples}


==================================================
6. DTC AND FULL SCAN INFORMATION
==================================================

{dtc_text}


==================================================
7. FREEZE FRAME DATA
==================================================

{freeze_frame_text}


==================================================
8. FULL SCAN PDF TEXT
==================================================

{scan_text}


==================================================
9. PHYSICAL INSPECTION NOTES
==================================================

{physical_notes}


==================================================
10. REQUIRED DIAGNOSTIC REPORT
==================================================

Prepare a professional evidence-based report
with the following sections:

A. EXECUTIVE SUMMARY

Explain the overall inspection findings.

B. VEHICLE AND CUSTOMER COMPLAINT

Summarize the vehicle and reported problem.

C. DATA QUALITY

Explain:

- Data received
- Parameters identified
- Missing readings
- Unavailable parameters
- Unsupported parameters
- Unmapped scanner values
- Limitations of the available data

D. MODULE-BY-MODULE FINDINGS

Analyze each available module separately.

E. DTC INTERPRETATION

Explain the available trouble codes.

Do not assume a DTC proves component failure.

F. ROOT CAUSE POSSIBILITIES

Rank possible causes according to evidence.

For every cause provide:

- Finding classification
- Supporting evidence
- Contradicting evidence
- Confidence level
- What remains unverified

G. NEXT DIAGNOSTIC TESTS

Give the exact practical test sequence.

Explain what each test is intended to confirm.

H. REPAIR DIRECTION

Recommend repair direction only when evidence supports it.

Do not guess parts.

I. SAFETY CONCERNS

Highlight safety-critical findings.

J. LIMITATIONS

Clearly mention tests not performed
and information not available.

K. CUSTOMER-FRIENDLY CONCLUSION

Explain the findings in simple professional language.

IMPORTANT:

Do not invent expected OEM readings.

Do not calculate a numeric vehicle health score.

Do not interpret missing readings as zero.

Do not claim No Fault Detected means
that no fault exists.

Use these finding classifications:

- Confirmed
- Strongly Suspected
- Possible
- No Fault Detected
- Further Diagnosis Required

Separate observations from interpretations.

If evidence is insufficient, recommend further diagnosis.
"""


    # Main AI text input

    content = [
        {
            "type": "input_text",
            "text": prompt
        }
    ]


    # Add inspection photographs

    image_content = prepare_image_content(
        image_files
    )

    content.extend(
        image_content
    )


    # Send complete case to OpenAI

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
