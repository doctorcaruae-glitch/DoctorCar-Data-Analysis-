"""
Doctor Car - Evidence-Based AI Diagnostic Engine

Purpose:
- Combine DTCs, freeze-frame, scanner data and physical findings.
- Generate complaint-specific diagnostic questions.
- Separate confirmed faults from suspected causes.
- Avoid replacing parts based on DTCs alone.
- Support fuel delivery, fuel starvation and tank ventilation cases.
- Provide rule-based analysis when AI is unavailable.

Important:
AI findings are diagnostic guidance, not OEM repair instructions.
Vehicle-specific specifications and procedures must be verified.
"""

import os
import json
import re
from typing import Any, Dict, List

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

from csv_analyzer import get_csv_text_for_ai


# =========================================================
# 1. CONFIGURATION
# =========================================================

def get_api_key():

    key = os.getenv("OPENAI_API_KEY")

    if key:
        return key.strip()

    try:
        import streamlit as st

        key = st.secrets.get("OPENAI_API_KEY", "")

        if key:
            return str(key).strip()

    except Exception:
        pass

    return ""


def get_model():

    try:
        import streamlit as st

        model = st.secrets.get(
            "OPENAI_MODEL",
            "gpt-5.5"
        )

        if model:
            return str(model).strip()

    except Exception:
        pass

    return os.getenv(
        "OPENAI_MODEL",
        "gpt-5.5"
    )


def get_client():

    if OpenAI is None:
        return None

    api_key = get_api_key()

    if not api_key:
        return None

    try:
        return OpenAI(
            api_key=api_key,
            timeout=90.0,
            max_retries=2
        )

    except Exception:
        return None


# =========================================================
# 2. GENERAL HELPERS
# =========================================================

def safe_text(value):

    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    try:
        return str(value).strip()

    except Exception:
        return ""


def clean_json_text(text):

    text = safe_text(text)

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    return text.strip()


def normalize_evidence_status(status):

    allowed = {
        "Confirmed",
        "Strongly Suspected",
        "Possible",
        "Further Diagnosis Required",
        "Not Confirmed",
    }

    status = safe_text(status)

    if status in allowed:
        return status

    return "Further Diagnosis Required"


def format_input(value):

    if value is None:
        return "Not provided"

    if isinstance(value, (dict, list, tuple)):

        try:
            return json.dumps(
                value,
                indent=2,
                ensure_ascii=False,
                default=str
            )

        except Exception:
            return safe_text(value)

    return safe_text(value)


# =========================================================
# 3. COMPLAINT CLASSIFICATION
# =========================================================

DIAGNOSTIC_CATEGORIES = {

    "fuel_delivery": [
        "fuel pressure",
        "low fuel pressure",
        "fuel pump",
        "fuel delivery",
        "fuel starvation",
        "engine stall",
        "stalled while driving",
        "empty tank",
        "fuel tank",
        "fuel level",
        "fuel supply",
        "crank no start",
        "no start",
    ],

    "overheating": [
        "overheating",
        "engine temperature",
        "coolant temperature",
        "coolant loss",
        "engine hot",
        "temperature high",
    ],

    "misfire": [
        "misfire",
        "rough idle",
        "engine shaking",
        "cylinder misfire",
        "engine vibration",
    ],

    "battery_charging": [
        "battery",
        "alternator",
        "charging",
        "no start",
        "slow crank",
        "low voltage",
    ],

    "transmission": [
        "gearbox",
        "transmission",
        "gear slipping",
        "hard shifting",
        "delayed engagement",
    ],

    "air_conditioning": [
        "ac not cooling",
        "air conditioning",
        "compressor",
        "ac cooling",
    ],

    "emissions": [
        "catalyst",
        "catalytic converter",
        "oxygen sensor",
        "o2 sensor",
        "emissions",
    ],
}


def classify_complaint(complaint):

    text = safe_text(complaint).lower()

    matches = []

    for category, keywords in DIAGNOSTIC_CATEGORIES.items():

        if any(keyword in text for keyword in keywords):
            matches.append(category)

    return matches


# =========================================================
# 4. DIAGNOSTIC QUESTIONS
# =========================================================

QUESTION_PROFILES = {

    "fuel_delivery": [
        "Did the engine stall while driving, or did it fail to start?",
        "Was the actual fuel quantity checked physically?",
        "Did the dashboard fuel level agree with the actual fuel quantity?",
        "Was fuel added before the vehicle restarted?",
        "Were low-pressure and high-pressure fuel readings recorded?",
        "Was actual fuel rail pressure compared with commanded pressure?",
        "Was the fuel pump command or current recorded?",
        "Was the fuel tank inspected for deformation or vacuum?",
        "Were the tank ventilation and EVAP systems checked?",
        "Were DTCs and freeze-frame data saved before clearing?",
    ],

    "overheating": [
        "When does the temperature increase: idle, traffic or driving?",
        "Was coolant level checked when the engine was cold?",
        "Was the cooling system pressure tested?",
        "Was radiator fan operation verified?",
        "Was thermostat operation verified?",
        "Was actual coolant temperature checked with scanner data?",
        "Was a combustion-gas test performed if indicated?",
    ],

    "misfire": [
        "Is the misfire present at idle, acceleration or under load?",
        "Which cylinder or cylinders are affected?",
        "Were misfire counters recorded?",
        "Were ignition coils and spark plugs physically inspected?",
        "Were fuel trims and injector operation checked?",
        "Was compression or leak-down testing performed if required?",
    ],

    "battery_charging": [
        "What is battery voltage with ignition OFF?",
        "What is battery voltage during cranking?",
        "What is charging voltage with engine running?",
        "Was alternator output tested under electrical load?",
        "Were battery terminals and grounds inspected?",
        "Was battery health tested?",
    ],

    "transmission": [
        "Does the symptom occur cold, hot or in both conditions?",
        "Which gear or shift event causes the symptom?",
        "Were transmission DTCs recorded?",
        "Were commanded and actual gear values checked?",
        "Was transmission fluid condition and level verified using the correct procedure?",
        "Were transmission temperature and adaptation data recorded?",
    ],

    "air_conditioning": [
        "Does the AC problem occur at idle, driving or both?",
        "Was compressor command checked?",
        "Was compressor operation verified?",
        "Were high-side and low-side pressures measured?",
        "Were condenser fan operation and airflow checked?",
        "Were refrigerant quantity and leak condition verified?",
    ],

    "emissions": [
        "Which exact DTCs are stored?",
        "Were freeze-frame conditions saved?",
        "Were upstream and downstream oxygen sensor readings recorded?",
        "Were short-term and long-term fuel trims checked?",
        "Were exhaust leaks checked?",
        "Were misfire and fuel-mixture problems ruled out before condemning the catalyst?",
    ],
}


def generate_diagnostic_questions(vehicle, complaint):

    categories = classify_complaint(complaint)

    questions = []

    for category in categories:

        questions.extend(
            QUESTION_PROFILES.get(category, [])
        )

    if not questions:

        questions = [
            "When did the problem first occur?",
            "Does the symptom happen continuously or intermittently?",
            "Under what operating conditions does it occur?",
            "Which DTCs are stored in all relevant modules?",
            "Is freeze-frame data available?",
            "What live-data readings were recorded?",
            "Which physical tests have been completed?",
            "Were any parts recently replaced or repairs performed?",
        ]

    vehicle_text = format_input(vehicle)

    return {
        "vehicle": vehicle_text,
        "categories": categories,
        "questions": questions,
    }


# =========================================================
# 5. FUEL DELIVERY RULE-BASED GUIDANCE
# =========================================================

def fuel_delivery_guidance(
    complaint,
    dtc_text,
    freeze_frame_text,
    scan_text,
    physical_notes
):

    combined = " ".join([
        safe_text(complaint),
        safe_text(dtc_text),
        safe_text(freeze_frame_text),
        safe_text(scan_text),
        safe_text(physical_notes),
    ]).lower()

    findings = []

    if not any(
        keyword in combined
        for keyword in [
            "fuel pressure",
            "fuel pump",
            "fuel starvation",
            "fuel level",
            "fuel tank",
        ]
    ):
        return findings

    findings.append({
        "finding": "Fuel delivery system requires evaluation.",
        "status": "Further Diagnosis Required",
        "reason": (
            "The complaint or supplied evidence contains "
            "fuel-delivery-related information. "
            "This does not establish a failed component."
        ),
    })

    starvation_indicators = [
        "empty tank",
        "low fuel",
        "fuel starvation",
        "ran out of fuel",
        "out of fuel",
        "fuel added",
        "after refueling",
    ]

    if any(
        indicator in combined
        for indicator in starvation_indicators
    ):

        findings.append({
            "finding": "Fuel starvation may have contributed to the symptom.",
            "status": "Possible",
            "reason": (
                "The supplied information contains a fuel shortage "
                "or refueling indicator. Verify actual fuel quantity "
                "and fuel pressure under the conditions of failure."
            ),
        })

    level_indicators = [
        "fuel level incorrect",
        "fuel gauge incorrect",
        "fuel gauge",
        "fuel level sensor",
        "fuel sender",
        "dashboard fuel",
    ]

    if any(
        indicator in combined
        for indicator in level_indicators
    ):

        findings.append({
            "finding": "Fuel level indication or sender circuit requires verification.",
            "status": "Possible",
            "reason": (
                "Compare the indicated fuel level with actual fuel "
                "quantity and inspect sender, wiring and instrument data."
            ),
        })

    tank_indicators = [
        "tank vacuum",
        "fuel tank vacuum",
        "tank deformation",
        "tank bulged",
        "tank collapsed",
        "tank deformed",
        "tank ventilation",
    ]

    if any(
        indicator in combined
        for indicator in tank_indicators
    ):

        findings.append({
            "finding": "Fuel tank ventilation or tank pressure condition requires investigation.",
            "status": "Possible",
            "reason": (
                "Inspect the tank ventilation and EVAP system using "
                "the vehicle manufacturer's procedure. Confirm the "
                "tank pressure condition before identifying a fault."
            ),
        })

    if (
        "low fuel pressure" in combined
        or "fuel pressure too low" in combined
    ):

        findings.append({
            "finding": "Low fuel pressure evidence is present in the supplied information.",
            "status": "Further Diagnosis Required",
            "reason": (
                "A low-pressure DTC or description does not identify "
                "the failed component. Compare actual pressure with "
                "the correct vehicle specification and operating "
                "conditions. Check supply, electrical control, "
                "restriction and pressure regulation."
            ),
        })

    return findings


# =========================================================
# 6. DIAGNOSTIC TEST RECOMMENDATIONS
# =========================================================

def get_physical_test_recommendations(
    complaint,
    categories
):

    recommendations = []

    if "fuel_delivery" in categories:

        recommendations.extend([
            "Verify actual fuel quantity independently of the dashboard gauge.",
            "Save all DTCs and freeze-frame data before clearing codes.",
            "Measure low-side fuel pressure using the manufacturer's test procedure.",
            "Compare commanded and actual rail pressure where supported.",
            "Check fuel pump command, supply voltage, ground and current where applicable.",
            "Inspect fuel filter, lines and restrictions where applicable.",
            "Check tank ventilation and EVAP operation using the OEM procedure.",
            "Repeat testing under the conditions in which the fault occurs, if safe.",
        ])

    if "overheating" in categories:

        recommendations.extend([
            "Perform a cooling-system pressure test.",
            "Verify radiator fan operation and control.",
            "Check thermostat operation using the correct procedure.",
            "Compare scanner coolant temperature with an independent measurement.",
            "Perform combustion-gas testing if evidence indicates possible cylinder leakage.",
        ])

    if "misfire" in categories:

        recommendations.extend([
            "Record cylinder-specific misfire counters.",
            "Inspect ignition components.",
            "Check injector operation and fuel delivery.",
            "Perform compression or leak-down testing where indicated.",
        ])

    if "battery_charging" in categories:

        recommendations.extend([
            "Perform a battery conductance or load test.",
            "Measure cranking voltage.",
            "Test charging output under electrical load.",
            "Inspect battery connections, grounds and charging cables.",
        ])

    if "transmission" in categories:

        recommendations.extend([
            "Scan the transmission control module.",
            "Record transmission temperature and relevant live data.",
            "Check fluid level and condition using the correct OEM procedure.",
            "Compare commanded and actual gear or pressure values where available.",
        ])

    if "air_conditioning" in categories:

        recommendations.extend([
            "Measure high-side and low-side refrigerant pressures.",
            "Verify compressor command and operation.",
            "Check condenser fan operation and airflow.",
            "Check refrigerant quantity and system leakage.",
        ])

    if "emissions" in categories:

        recommendations.extend([
            "Review freeze-frame data and readiness status.",
            "Compare upstream and downstream oxygen sensor data.",
            "Check fuel trims and misfire history.",
            "Inspect exhaust leaks before condemning the catalytic converter.",
        ])

    if not recommendations:

        recommendations = [
            "Confirm the reported symptom.",
            "Scan all relevant vehicle modules.",
            "Record freeze-frame data.",
            "Collect live data under the conditions of the complaint.",
            "Perform targeted physical tests before replacing components.",
        ]

    return recommendations


# =========================================================
# 7. BUILD EVIDENCE INPUT
# =========================================================

def build_evidence_context(
    vehicle,
    complaint,
    answers,
    module_data,
    dtc_text,
    freeze_frame_text,
    scan_text,
    physical_notes
):

    csv_sections = []

    if isinstance(module_data, dict):

        for module_name, module_result in module_data.items():

            csv_sections.append(
                f"\nMODULE: {module_name}\n"
            )

            if isinstance(module_result, dict):

                try:
                    csv_text = get_csv_text_for_ai(
                        module_result
                    )

                    csv_sections.append(csv_text)

                except Exception:
                    csv_sections.append(
                        format_input(module_result)
                    )

            else:
                csv_sections.append(
                    format_input(module_result)
                )

    elif module_data:

        csv_sections.append(
            format_input(module_data)
        )

    return {
        "vehicle": format_input(vehicle),
        "complaint": format_input(complaint),
        "answers": format_input(answers),
        "dtc": format_input(dtc_text),
        "freeze_frame": format_input(freeze_frame_text),
        "scan_data": format_input(scan_text),
        "csv_data": "\n".join(csv_sections),
        "physical_findings": format_input(physical_notes),
    }


# =========================================================
# 8. AI DIAGNOSTIC PROMPT
# =========================================================

def build_diagnostic_prompt(evidence, categories):

    return f"""
You are Doctor Car's automotive diagnostic analysis assistant.

Your task is to reason from evidence, not guess parts.

VEHICLE INFORMATION:
{evidence["vehicle"]}

CUSTOMER COMPLAINT:
{evidence["complaint"]}

CUSTOMER / INSPECTOR ANSWERS:
{evidence["answers"]}

DTC INFORMATION:
{evidence["dtc"]}

FREEZE FRAME:
{evidence["freeze_frame"]}

SCANNER DATA:
{evidence["scan_data"]}

CSV LIVE DATA ANALYSIS:
{evidence["csv_data"]}

PHYSICAL INSPECTION FINDINGS:
{evidence["physical_findings"]}

DETECTED DIAGNOSTIC CATEGORIES:
{", ".join(categories) if categories else "Not classified"}

MANDATORY DIAGNOSTIC RULES:

1. Do not diagnose a failed component from a DTC alone.
2. Distinguish root cause, contributing condition and secondary DTC.
3. A DTC recorded during an abnormal event may be consequential.
4. Do not assume a missing parameter is zero or normal.
5. Do not invent sensor values, OEM specifications or test results.
6. Do not compare readings with generic limits when vehicle-specific
   specifications are required.
7. Compare commanded and actual values only when the parameter,
   unit and operating condition are understood.
8. A normal reading at idle does not rule out an intermittent or
   load-related fault.
9. Distinguish confirmed findings from suspected causes.
10. State what evidence is missing.
11. Give practical next tests in a logical order.
12. Do not recommend replacing a part until the evidence supports it.
13. Do not claim that an image or video was analyzed unless actual
    image analysis was performed.
14. Do not recommend opening high-pressure fuel lines casually.
15. Preserve DTC and freeze-frame evidence before clearing codes.

FUEL DELIVERY SPECIAL RULES:

If fuel pressure DTCs are present, do not automatically conclude
that the fuel pump has failed.

Consider:
- Actual fuel quantity
- Fuel level sender accuracy
- Low-side pressure
- High-side / rail pressure
- Commanded versus actual rail pressure
- Pump command and electrical supply
- Fuel restriction
- Tank ventilation and EVAP
- Conditions when the DTC was recorded

If the engine stalled because of fuel starvation and restarted
after refueling, consider starvation as a possible cause of the
pressure DTC. This does not automatically rule out a pump fault.

If a tank is deformed or vacuum is suspected, recommend appropriate
tank ventilation checks. Do not conclude that the tank must be
replaced without confirming the cause and condition.

OUTPUT FORMAT:

Return a clear professional report using these headings:

1. Executive Diagnostic Summary
2. Confirmed Findings
3. Strongly Suspected Causes
4. Possible Causes
5. DTC Interpretation
6. Live Data Interpretation
7. Root Cause Assessment
8. Further Tests Required
9. Recommended Diagnostic Sequence
10. Parts Replacement Recommendation
11. Diagnostic Limitations

For each important finding state:
- Evidence
- Status
- Reasoning
- What would confirm or reject it

Use these evidence statuses exactly:
Confirmed
Strongly Suspected
Possible
Further Diagnosis Required
Not Confirmed

Never manufacture a confidence percentage.

If the available evidence is insufficient, clearly say:
"Root cause not confirmed - further diagnosis required."

Use concise, professional automotive terminology.
"""


# =========================================================
# 9. LOCAL RULE-BASED ANALYSIS
# =========================================================

def generate_local_analysis(
    vehicle,
    complaint,
    evidence,
    categories
):

    fuel_findings = fuel_delivery_guidance(
        complaint,
        evidence["dtc"],
        evidence["freeze_frame"],
        evidence["scan_data"],
        evidence["physical_findings"]
    )

    physical_tests = get_physical_test_recommendations(
        complaint,
        categories
    )

    lines = []

    lines.append("# Doctor Car - Diagnostic Assessment")
    lines.append("")
    lines.append("## 1. Executive Diagnostic Summary")
    lines.append(
        "The available information requires evidence-based "
        "diagnostic verification."
    )

    lines.append("")
    lines.append("## 2. Initial Findings")

    if fuel_findings:

        for finding in fuel_findings:

            lines.append(
                f"\n### {finding['finding']}"
            )

            lines.append(
                f"**Status:** {finding['status']}"
            )

            lines.append(
                f"**Reason:** {finding['reason']}"
            )

    else:

        lines.append(
            "No specific component failure can be confirmed "
            "from the supplied information alone."
        )

    lines.append("")
    lines.append("## 3. Further Tests Required")

    for index, test in enumerate(
        physical_tests,
        start=1
    ):

        lines.append(f"{index}. {test}")

    lines.append("")
    lines.append("## 4. Diagnostic Limitations")

    lines.append(
        "- Vehicle-specific OEM specifications were not independently verified."
    )

    lines.append(
        "- Missing live-data values cannot be treated as normal."
    )

    lines.append(
        "- DTCs alone do not prove component failure."
    )

    lines.append(
        "- Physical confirmation may be required before repair recommendations."
    )

    lines.append("")
    lines.append(
        "**Overall Status: Further Diagnosis Required**"
    )

    return "\n".join(lines)


# =========================================================
# 10. OPTIONAL IMAGE INPUT
# =========================================================

def build_image_content(image_files):

    """
    Prepare supported image files for OpenAI vision input.

    This function does not analyze videos.
    """

    content = []

    if not image_files:
        return content

    for uploaded_image in image_files:

        try:

            image_bytes = uploaded_image.getvalue()

            if not image_bytes:
                continue

            import base64

            encoded = base64.b64encode(
                image_bytes
            ).decode("utf-8")

            mime_type = getattr(
                uploaded_image,
                "type",
                "image/jpeg"
            )

            if not mime_type.startswith("image/"):
                continue

            data_url = (
                f"data:{mime_type};base64,{encoded}"
            )

            content.append({
                "type": "image_url",
                "image_url": {
                    "url": data_url,
                    "detail": "high",
                },
            })

        except Exception:
            continue

    return content


# =========================================================
# 11. OPENAI ANALYSIS
# =========================================================

def run_ai_analysis(
    prompt,
    image_files=None
):

    client = get_client()

    if client is None:

        return {
            "success": False,
            "analysis": None,
            "error": (
                "OpenAI client is unavailable. "
                "Check API configuration and package installation."
            ),
        }

    try:

        user_content = [
            {
                "type": "text",
                "text": prompt,
            }
        ]

        image_content = build_image_content(
            image_files
        )

        user_content.extend(image_content)

        response = client.chat.completions.create(
            model=get_model(),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Doctor Car's evidence-based "
                        "automotive diagnostic assistant. "
                        "Never invent evidence or OEM specifications."
                    ),
                },
                {
                    "role": "user",
                    "content": user_content,
                },
            ],
            temperature=0.2,
        )

        result = response.choices[0].message.content

        if not result:
            raise ValueError(
                "AI returned an empty diagnostic response."
            )

        return {
            "success": True,
            "analysis": result,
            "error": None,
        }

    except Exception as error:

        return {
            "success": False,
            "analysis": None,
            "error": str(error),
        }


# =========================================================
# 12. MAIN DIAGNOSTIC FUNCTION
# =========================================================

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

    categories = classify_complaint(
        complaint
    )

    evidence = build_evidence_context(
        vehicle=vehicle,
        complaint=complaint,
        answers=answers,
        module_data=module_data,
        dtc_text=dtc_text,
        freeze_frame_text=freeze_frame_text,
        scan_text=scan_text,
        physical_notes=physical_notes,
    )

    local_analysis = generate_local_analysis(
        vehicle,
        complaint,
        evidence,
        categories
    )

    prompt = build_diagnostic_prompt(
        evidence,
        categories
    )

    ai_result = run_ai_analysis(
        prompt,
        image_files=image_files
    )

    if ai_result["success"]:

        final_analysis = ai_result["analysis"]

        analysis_mode = "AI + Rule-Based"

    else:

        final_analysis = local_analysis

        analysis_mode = "Rule-Based Only"

    return {
        "success": True,
        "diagnosis": final_analysis,
        "local_analysis": local_analysis,
        "ai_analysis": ai_result["analysis"],
        "ai_available": ai_result["success"],
        "ai_error": ai_result["error"],
        "analysis_mode": analysis_mode,
        "categories": categories,
        "evidence": evidence,
        "physical_test_recommendations": (
            get_physical_test_recommendations(
                complaint,
                categories
            )
        ),
        "overall_status": "Further Diagnosis Required",
    }


# =========================================================
# 13. SELF TEST
# =========================================================

def run_diagnostic_engine_self_test():

    complaint = (
        "Engine stalled while driving. "
        "Low fuel pressure DTC. "
        "Fuel was added and engine restarted."
    )

    categories = classify_complaint(
        complaint
    )

    findings = fuel_delivery_guidance(
        complaint,
        "Low fuel pressure",
        "Not provided",
        "Not provided",
        "Not provided"
    )

    return {
        "success": True,
        "categories": categories,
        "fuel_findings": findings,
        "api_configured": bool(get_api_key()),
        "model": get_model(),
    }
