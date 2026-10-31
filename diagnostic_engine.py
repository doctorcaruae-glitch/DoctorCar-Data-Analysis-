import os
import json
import base64
from openai import OpenAI


def get_api_key():
    try:
        import streamlit as st
        return st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        return os.getenv("OPENAI_API_KEY", "")


def get_model():
    try:
        import streamlit as st
        return st.secrets.get(
            "OPENAI_MODEL",
            "gpt-5.5"
        )
    except Exception:
        return os.getenv("OPENAI_MODEL", "gpt-5.5")


def get_client():
    api_key = get_api_key()

    if not api_key:
        raise ValueError(
            "OpenAI API key is missing. Configure it in Streamlit Secrets."
        )

    return OpenAI(api_key=api_key)


SYSTEM_INSTRUCTIONS = """
You are Doctor Car AI, an automotive diagnostic assistant
supporting professional vehicle inspectors.

Your job is to analyze vehicle complaints using actual evidence.

STRICT RULES:

1. Never invent vehicle data, DTC codes, sensor readings or test results.
2. Never treat missing parameters as zero.
3. Never assume all vehicles support all OBD parameters.
4. Distinguish confirmed faults from suspected and possible faults.
5. A DTC alone does not prove that a component is defective.
6. Do not recommend replacing a component without supporting evidence.
7. If evidence is insufficient, say further diagnosis is required.
8. Explain why each next test is required.
9. Give expected readings only when vehicle-specific specifications
   are available. Otherwise clearly label them as general guidance.
10. Consider engine, transmission and other related modules together.
11. Check whether a complaint may be caused by another system.
12. Do not claim 100% diagnostic accuracy.
13. Identify safety-critical concerns clearly.
14. Never fabricate OEM specifications.
15. Missing data must be reported as unavailable, not normal.

Use these fault classifications:
- Confirmed
- Strongly Suspected
- Possible
- No Fault Detected
- Further Diagnosis Required

Provide practical instructions for the inspector.
"""


def generate_diagnostic_questions(vehicle, complaint):
    client = get_client()

    prompt = f"""
Create a diagnostic questionnaire for this vehicle complaint.

VEHICLE:
{json.dumps(vehicle, ensure_ascii=False)}

CUSTOMER COMPLAINT:
{complaint}

Return:
1. Questions to ask the customer.
2. Questions for the inspector.
3. Physical checks required.
4. Relevant modules to investigate.
5. Live data parameters required.
6. Why each parameter is required.

Classify every parameter:
Must Have / Optional / Vehicle Dependent.

Do not claim a parameter is supported unless verified.
Return a clear practical response.
"""

    response = client.responses.create(
        model=get_model(),
        instructions=SYSTEM_INSTRUCTIONS,
        input=prompt
    )

    return response.output_text


def analyze_vehicle(
    vehicle,
    complaint,
    answers,
    module_data,
    dtc_text,
    freeze_frame,
    scan_text,
    physical_notes,
    image_files=None
):
    client = get_client()

    input_content = []

    diagnostic_context = {
        "vehicle": vehicle,
        "customer_complaint": complaint,
        "questionnaire_answers": answers,
        "module_live_data": module_data,
        "dtc_codes_and_scan_findings": dtc_text,
        "freeze_frame": freeze_frame,
        "full_scan_report_text": scan_text,
        "physical_inspection_notes": physical_notes
    }

    input_content.append({
        "type": "input_text",
        "text": (
            "Analyze this vehicle using the available evidence.\n\n"
            + json.dumps(
                diagnostic_context,
                ensure_ascii=False,
                default=str
            )
            + """

Prepare a professional Doctor Car diagnostic report.

Include these sections:

1. Executive Summary
2. Vehicle and Complaint Overview
3. Data Availability and Missing Parameters
4. DTC Analysis
5. Engine Analysis
6. Transmission Analysis
7. Other Relevant Module Analysis
8. Photo Evidence Findings
9. Confirmed Faults
10. Strongly Suspected Faults
11. Possible Faults
12. No Fault Detected
13. Further Diagnosis Required
14. Most Likely Root Cause
15. Step-by-Step Next Diagnostic Tests
16. Expected Results and Interpretation
17. Repair Recommendations
18. Repair Priority
19. Verification Procedure
20. Diagnostic Confidence
21. Module Health Assessment
22. Important Safety Warnings

For every finding provide:
- Finding
- Classification
- Actual evidence
- Reasoning
- Confidence level
- Next test

Do not invent readings or vehicle specifications.

Do not assign a health score when evidence is insufficient.
Clearly separate data completeness from vehicle health.

Return the report in readable Markdown.
"""
        )
    })

    # Optional photo evidence.
    # Images are sent individually; videos are not interpreted as
    # complete videos by this version.
    for image_file in (image_files or [])[:8]:
        image_bytes = image_file.getvalue()
        encoded = base64.b64encode(image_bytes).decode("utf-8")

        mime = image_file.type or "image/jpeg"

        input_content.append({
            "type": "input_image",
            "image_url": f"data:{mime};base64,{encoded}"
        })

    response = client.responses.create(
        model=get_model(),
        instructions=SYSTEM_INSTRUCTIONS,
        input=[
            {
                "role": "user",
                "content": input_content
            }
        ]
    )

    return response.output_text
