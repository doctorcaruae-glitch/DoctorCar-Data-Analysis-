
"""
Doctor Car - Evidence-Based Diagnostic Engine

Features:
1. Local diagnostic mode without OpenAI API
2. OpenAI API integration with error handling
3. Complaint-based diagnostic questions
4. Engine stall and fuel delivery guidance
5. CSV evidence integration
6. Physical test recommendations
7. Evidence-based diagnostic status
8. API failure must never crash the Streamlit application

Important:
Generic diagnostic guidance only.
Vehicle-specific OEM specifications and procedures must be verified.
"""

import os
import json
import re
import base64
from typing import Any


# =========================================================
# OPTIONAL IMPORTS
# =========================================================

try:
    from openai import OpenAI
    from openai import (
        RateLimitError,
        APIConnectionError,
        APITimeoutError,
        AuthenticationError,
        APIStatusError,
    )
except Exception:
    OpenAI = None
    RateLimitError = Exception
    APIConnectionError = Exception
    APITimeoutError = Exception
    AuthenticationError = Exception
    APIStatusError = Exception


try:
    from csv_analyzer import get_csv_text_for_ai
except Exception:
    get_csv_text_for_ai = None


# =========================================================
# SETTINGS
# =========================================================

DEFAULT_MODEL = "gpt-4.1-mini"


def get_api_key():
    """Read API key from Streamlit secrets or environment."""

    try:
        import streamlit as st

        key = st.secrets.get("OPENAI_API_KEY", None)

        if key:
            return str(key).strip()

    except Exception:
        pass

    return os.getenv("OPENAI_API_KEY", "").strip()


def get_model():
    """Read model name from configuration."""

    try:
        import streamlit as st

        model = st.secrets.get("OPENAI_MODEL", None)

        if model:
            return str(model).strip()

    except Exception:
        pass

    return os.getenv("OPENAI_MODEL", DEFAULT_MODEL).strip()


def get_client():
    """Create OpenAI client safely."""

    if OpenAI is None:
        return None

    api_key = get_api_key()

    if not api_key:
        return None

    try:
        return OpenAI(
            api_key=api_key,
            timeout=45.0,
            max_retries=1,
        )

    except Exception:
        return None


# =========================================================
# GENERAL HELPERS
# =========================================================

def safe_text(value, default="Not provided"):
    if value is None:
        return default

    try:
        text = str(value).strip()
    except Exception:
        return default

    if not text:
        return default

    return text


def format_input(value):
    """Convert values to safe readable text."""

    if value is None:
        return "Not provided"

    if isinstance(value, dict):
        return json.dumps(value, indent=2, ensure_ascii=False, default=str)

    if isinstance(value, (list, tuple)):
        return "\n".join(str(item) for item in value)

    return str(value)


def clean_json_text(text):
    """Remove Markdown code fences from JSON responses."""

    text = safe_text(text, "")

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(r"\s*```$", "", text)

    return text.strip()


def normalize_evidence_status(status):
    allowed = {
        "Confirmed",
        "Strongly Suspected",
        "Possible",
        "Further Diagnosis Required",
        "Not Evaluated",
    }

    status = safe_text(status, "Further Diagnosis Required")

    if status not in allowed:
        return "Further Diagnosis Required"

    return status


# =========================================================
# COMPLAINT CLASSIFICATION
# =========================================================

COMPLAINT_KEYWORDS = {
    "engine_stall": [
        "engine stall",
        "engine stalls",
        "engine shutting off",
        "engine shuts off",
        "engine stops",
        "car stalls",
        "stalling",
        "engine cuts off",
        "motor stops",
    ],

    "no_start": [
        "no start",
        "not starting",
        "engine won't start",
        "engine will not start",
        "crank no start",
        "cranks but won't start",
    ],

    "hard_start": [
        "hard start",
        "difficult starting",
        "long cranking",
        "takes long to start",
    ],

    "misfire": [
        "misfire",
        "engine shaking",
        "rough idle",
        "engine vibration",
        "cylinder misfire",
    ],

    "overheating": [
        "overheating",
        "engine hot",
        "temperature high",
        "coolant temperature high",
        "engine temperature",
    ],

    "low_power": [
        "low power",
        "loss of power",
        "poor acceleration",
        "lack of power",
        "engine weak",
    ],

    "fuel_delivery": [
        "fuel pressure",
        "fuel pump",
        "fuel starvation",
        "fuel supply",
        "fuel delivery",
    ],

    "fuel_level_error": [
        "fuel gauge",
        "fuel level",
        "wrong fuel level",
        "fuel sender",
        "fuel reading",
    ],

    "transmission": [
        "gear shifting",
        "transmission",
        "gearbox",
        "hard shifting",
        "slipping gear",
    ],

    "battery_charging": [
        "battery warning",
        "alternator",
        "charging problem",
        "battery not charging",
    ],

    "ac_power_loss": [
        "ac not cooling",
        "air conditioning",
        "ac problem",
        "ac cooling",
    ],
}


def classify_complaint(complaint):
    """Return complaint categories based on keywords."""

    text = safe_text(complaint, "").lower()

    matched = []

    for category, keywords in COMPLAINT_KEYWORDS.items():

        if any(keyword in text for keyword in keywords):
            matched.append(category)

    return matched


# =========================================================
# LOCAL DIAGNOSTIC QUESTIONS
# =========================================================

LOCAL_QUESTIONS = {

    "engine_stall": [
        "Does the engine stall while idling, driving, accelerating, or braking?",
        "Does the engine restart immediately after stalling?",
        "Does the engine stall when the air conditioning is switched ON?",
        "Does the engine stall when the fuel level is low?",
        "Does the engine stall when the vehicle becomes hot?",
        "Are there any warning lights before or after the stall?",
        "Does engine RPM fluctuate before stalling?",
        "Does the engine lose electrical power when it stalls?",
    ],

    "no_start": [
        "Does the starter motor crank the engine normally?",
        "Is the immobilizer or security warning light flashing?",
        "Is the battery voltage adequate during cranking?",
        "Is fuel pressure available during cranking?",
        "Is engine RPM visible in live data while cranking?",
        "Is ignition spark available where applicable?",
        "Are injector commands present?",
    ],

    "hard_start": [
        "Does the problem occur during cold start or hot start?",
        "How long does the engine crank before starting?",
        "Does pressing the accelerator change the starting behavior?",
        "Is fuel pressure building correctly?",
        "Are there any stored or pending DTCs?",
    ],

    "misfire": [
        "Is the misfire present at idle, acceleration, or all conditions?",
        "Is the misfire isolated to one cylinder or multiple cylinders?",
        "Are there any cylinder-specific misfire DTCs?",
        "Does the misfire counter increase in live data?",
        "Have ignition coils, spark plugs, and injectors been inspected?",
    ],

    "overheating": [
        "Does overheating occur at idle, while driving, or both?",
        "Does the radiator cooling fan operate?",
        "Is coolant level stable?",
        "Is the radiator getting hot across its surface?",
        "Has the cooling system been pressure tested?",
        "Is there evidence of coolant loss or combustion gas in coolant?",
    ],

    "low_power": [
        "Does power loss occur during acceleration or at all times?",
        "Is the vehicle entering limp mode?",
        "Is boost pressure correct where applicable?",
        "Are fuel pressure and air intake readings normal?",
        "Is exhaust restriction suspected or tested?",
    ],

    "fuel_delivery": [
        "Does the engine lose power under load?",
        "What is the actual fuel pressure during the complaint?",
        "What is the commanded fuel pressure?",
        "Does fuel pressure drop when the engine stalls?",
        "Is fuel pump voltage and current available?",
        "Has fuel filter restriction been checked?",
    ],

    "fuel_level_error": [
        "Does the fuel gauge show an incorrect level?",
        "Does the reading change after restarting the vehicle?",
        "Are there separate fuel tank sender units?",
        "Has sender resistance been measured?",
        "Does the scan tool show the same level as the dashboard?",
    ],

    "transmission": [
        "Which gear or shift condition causes the complaint?",
        "Does the problem occur when cold, hot, or both?",
        "Are transmission DTCs present?",
        "What is the transmission fluid condition and level?",
        "Are commanded and actual gear values matching?",
    ],

    "battery_charging": [
        "Does the battery warning light remain ON?",
        "What is the battery voltage with engine OFF?",
        "What is the charging voltage with engine running?",
        "Does voltage change when electrical loads are switched ON?",
        "Have alternator connections and grounds been inspected?",
    ],

    "ac_power_loss": [
        "Does the AC stop cooling at idle or while driving?",
        "Does compressor command change when AC is switched ON?",
        "Is refrigerant pressure within vehicle-specific specifications?",
        "Does the cooling fan operate with AC request?",
        "Does the engine RPM change when AC is switched ON?",
    ],
}


def generate_diagnostic_questions(vehicle, complaint):
    """
    Generate questions locally.
    This function does not require OpenAI API.
    """

    categories = classify_complaint(complaint)

    questions = []

    for category in categories:
        questions.extend(
            LOCAL_QUESTIONS.get(category, [])
        )

    if not questions:
        questions = [
            "When does the problem occur?",
            "Does the problem happen continuously or intermittently?",
            "Are any warning lights ON?",
            "Are any DTCs stored in the vehicle?",
            "What changes when the engine temperature increases?",
            "Has any repair or component replacement been performed recently?",
        ]

    # Remove duplicates while preserving order.
    questions = list(dict.fromkeys(questions))

    return {
        "vehicle": safe_text(vehicle),
        "categories": categories,
        "questions": questions[:15],
        "source": "Local Diagnostic Database",
        "ai_available": False,
    }


# =========================================================
# FUEL DELIVERY GUIDANCE
# =========================================================

def fuel_delivery_guidance(complaint):
    categories = classify_complaint(complaint)

    if not any(
        item in categories
        for item in [
            "engine_stall",
            "no_start",
            "hard_start",
            "fuel_delivery",
            "fuel_level_error",
        ]
    ):
        return []

    return [
        {
            "test": "Fuel pressure verification",
            "purpose": "Compare actual fuel pressure with vehicle-specific specifications.",
            "caution": "Do not condemn the fuel pump without pressure and electrical evidence.",
        },
        {
            "test": "Fuel pump power and ground test",
            "purpose": "Verify supply voltage, ground integrity, and pump current where applicable.",
            "caution": "Use the correct wiring diagram and safe fuel-system procedures.",
        },
        {
            "test": "Fuel pressure under operating conditions",
            "purpose": "Check whether pressure drops during the reported complaint.",
            "caution": "Follow OEM test procedures and fuel pressure safety precautions.",
        },
        {
            "test": "Fuel tank ventilation / EVAP inspection",
            "purpose": "Check for abnormal tank vacuum, vent restriction, or EVAP faults.",
            "caution": "A tank ventilation problem must be verified before any repair recommendation.",
        },
    ]


# =========================================================
# PHYSICAL TEST RECOMMENDATIONS
# =========================================================

def get_physical_test_recommendations(complaint):

    categories = classify_complaint(complaint)

    recommendations = []

    if "engine_stall" in categories:

        recommendations.extend([
            "Record engine RPM and relevant live data before and during the stall.",
            "Check battery voltage and main power/ground connections.",
            "Check fuel pressure during the complaint.",
            "Check crankshaft and camshaft signal stability where applicable.",
            "Check intake air leaks and throttle operation.",
        ])

    if "no_start" in categories:

        recommendations.extend([
            "Verify battery condition and cranking voltage.",
            "Check immobilizer authorization.",
            "Check engine RPM signal during cranking.",
            "Verify fuel delivery and ignition where applicable.",
        ])

    if "misfire" in categories:

        recommendations.extend([
            "Review cylinder-specific misfire counters.",
            "Inspect spark plugs and ignition components.",
            "Perform injector and compression tests when indicated.",
        ])

    if "overheating" in categories:

        recommendations.extend([
            "Perform cooling system pressure test.",
            "Verify radiator fan operation.",
            "Check thermostat and coolant circulation.",
            "Perform combustion gas test if evidence supports it.",
        ])

    if "fuel_delivery" in categories:

        recommendations.extend([
            "Measure fuel pressure under the reported operating condition.",
            "Check pump power, ground, and current.",
            "Inspect fuel filter and fuel supply restriction where applicable.",
        ])

    if "fuel_level_error" in categories:

        recommendations.extend([
            "Compare scan-tool fuel level with dashboard indication.",
            "Inspect fuel sender wiring and connector.",
            "Measure sender resistance using OEM procedures.",
        ])

    if "low_power" in categories:

        recommendations.extend([
            "Compare requested and actual engine load parameters.",
            "Check intake restriction and air leaks.",
            "Review fuel pressure and boost pressure where applicable.",
        ])

    if "transmission" in categories:

        recommendations.extend([
            "Scan the transmission control module.",
            "Review commanded and actual gear data.",
            "Check fluid level and condition using OEM procedure.",
        ])

    if "battery_charging" in categories:

        recommendations.extend([
            "Perform battery load test.",
            "Measure charging voltage under electrical load.",
            "Check alternator wiring and grounds.",
        ])

    if "ac_power_loss" in categories:

        recommendations.extend([
            "Check AC request and compressor command data.",
            "Verify refrigerant pressure using approved equipment.",
            "Check cooling fan operation.",
        ])

    if not recommendations:

        recommendations = [
            "Perform a complete vehicle scan.",
            "Record freeze-frame data for relevant DTCs.",
            "Reproduce the customer complaint.",
            "Collect relevant live data.",
            "Perform physical verification before recommending repairs.",
        ]

    return list(dict.fromkeys(recommendations))


# =========================================================
# EVIDENCE CONTEXT
# =========================================================

def build_evidence_context(
    dtcs=None,
    freeze_frame=None,
    live_data=None,
    csv_data=None,
    physical_notes=None,
    diagnostic_answers=None,
):
    """Build evidence text without treating missing data as normal."""

    sections = []

    if dtcs:
        sections.append(
            "DTC INFORMATION:\n" + format_input(dtcs)
        )

    if freeze_frame:
        sections.append(
            "FREEZE FRAME:\n" + format_input(freeze_frame)
        )

    if live_data:
        sections.append(
            "LIVE DATA:\n" + format_input(live_data)
        )

    if csv_data:

        for index, item in enumerate(csv_data, start=1):

            if isinstance(item, dict):

                summary = item.get("summary", "")

                if summary:
                    sections.append(
                        f"CSV FILE {index}:\n{format_input(summary)}"
                    )

                if get_csv_text_for_ai:

                    try:
                        csv_text = get_csv_text_for_ai(item)

                        if csv_text:
                            sections.append(
                                f"CSV DETAILS {index}:\n{csv_text}"
                            )

                    except Exception:
                        pass

    if physical_notes:
        sections.append(
            "PHYSICAL INSPECTION NOTES:\n" + format_input(physical_notes)
        )

    if diagnostic_answers:
        sections.append(
            "CUSTOMER / INSPECTOR ANSWERS:\n" + format_input(diagnostic_answers)
        )

    if not sections:
        return "No diagnostic evidence supplied."

    return "\n\n".join(sections)


# =========================================================
# DIAGNOSTIC PROMPT
# =========================================================

def build_diagnostic_prompt(
    vehicle,
    complaint,
    evidence_context,
    diagnostic_questions=None,
):
    return f"""
You are an automotive diagnostic assistant supporting Doctor Car.

VEHICLE:
{format_input(vehicle)}

CUSTOMER COMPLAINT:
{format_input(complaint)}

AVAILABLE EVIDENCE:
{format_input(evidence_context)}

DIAGNOSTIC QUESTIONS:
{format_input(diagnostic_questions)}

STRICT DIAGNOSTIC RULES:

1. Do not diagnose a failed component from a DTC alone.
2. Separate confirmed facts from possible causes.
3. Never invent live data or test results.
4. Missing parameters must be reported as unavailable, not normal.
5. Compare actual and commanded values only when both are available.
6. Do not invent OEM specifications.
7. Recommend physical tests to verify suspected causes.
8. Do not recommend replacing parts without supporting evidence.
9. Consider wiring, connectors, power, ground, mechanical and software causes.
10. Explain what evidence is still required.

Return a clear diagnostic report with these headings:

CUSTOMER COMPLAINT
EVIDENCE AVAILABLE
EVIDENCE NOT AVAILABLE
POSSIBLE CAUSES
MOST IMPORTANT NEXT TESTS
PHYSICAL CONFIRMATION PROCEDURE
REPAIR RECOMMENDATION
OVERALL STATUS

Use one of these overall statuses:

Confirmed
Strongly Suspected
Possible
Further Diagnosis Required

If evidence is insufficient, use Further Diagnosis Required.
Do not claim a diagnosis is confirmed without physical or strong supporting evidence.
"""


# =========================================================
# LOCAL ANALYSIS
# =========================================================

def generate_local_analysis(
    vehicle,
    complaint,
    evidence_context="",
    diagnostic_answers=None,
):
    """
    Basic offline analysis.
    It identifies complaint categories and suggests verification steps.
    It does not claim a confirmed component failure.
    """

    categories = classify_complaint(complaint)

    questions = generate_diagnostic_questions(
        vehicle,
        complaint,
    )

    tests = get_physical_test_recommendations(complaint)

    fuel_tests = fuel_delivery_guidance(complaint)

    lines = []

    lines.append("CUSTOMER COMPLAINT")
    lines.append(safe_text(complaint))

    lines.append("\nVEHICLE")
    lines.append(safe_text(vehicle))

    lines.append("\nMATCHED DIAGNOSTIC CATEGORIES")

    if categories:
        for category in categories:
            lines.append("- " + category.replace("_", " ").title())
    else:
        lines.append("- No specific complaint profile matched.")

    lines.append("\nEVIDENCE AVAILABLE")
    lines.append(format_input(evidence_context))

    lines.append("\nPOSSIBLE CAUSES")

    if "engine_stall" in categories:

        lines.extend([
            "- Fuel delivery interruption.",
            "- Crankshaft or camshaft signal interruption.",
            "- Ignition or injector control issue.",
            "- Air intake or throttle control issue.",
            "- Electrical power or ground interruption.",
            "- Engine control system issue.",
        ])

    elif "no_start" in categories:

        lines.extend([
            "- Battery or cranking system issue.",
            "- Immobilizer authorization issue.",
            "- Fuel delivery issue.",
            "- Ignition or injector control issue.",
            "- Engine speed signal issue.",
            "- Mechanical engine condition issue.",
        ])

    elif "overheating" in categories:

        lines.extend([
            "- Cooling fan or fan control issue.",
            "- Thermostat or coolant circulation issue.",
            "- Radiator restriction.",
            "- Coolant leakage.",
            "- Combustion gas entering cooling system.",
        ])

    elif "misfire" in categories:

        lines.extend([
            "- Ignition system issue.",
            "- Injector or fuel delivery issue.",
            "- Air leak.",
            "- Compression or mechanical issue.",
        ])

    else:

        lines.append(
            "- Additional vehicle-specific evidence is required."
        )

    lines.append("\nMOST IMPORTANT NEXT TESTS")

    for test in tests:
        lines.append("- " + test)

    if fuel_tests:

        lines.append("\nFUEL SYSTEM VERIFICATION")

        for item in fuel_tests:
            lines.append(
                "- " + item["test"] + ": " + item["purpose"]
            )

    lines.append("\nDIAGNOSTIC QUESTIONS")

    for question in questions["questions"]:
        lines.append("- " + question)

    lines.append("\nREPAIR RECOMMENDATION")
    lines.append(
        "Do not replace any component until the relevant test "
        "confirms the failure."
    )

    lines.append("\nOVERALL STATUS")
    lines.append("Further Diagnosis Required")

    return "\n".join(lines)


# =========================================================
# IMAGE CONTENT
# =========================================================

def build_image_content(image_files):
    """Convert supported uploaded images into Responses API content."""

    content = []

    if not image_files:
        return content

    for uploaded_image in image_files:

        try:

            image_bytes = uploaded_image.getvalue()

            if not image_bytes:
                continue

            mime_type = getattr(
                uploaded_image,
                "type",
                "image/jpeg",
            )

            if not str(mime_type).startswith("image/"):
                continue

            encoded = base64.b64encode(
                image_bytes
            ).decode("utf-8")

            data_url = (
                f"data:{mime_type};base64,{encoded}"
            )

            content.append({
                "type": "input_image",
                "image_url": data_url,
                "detail": "high",
            })

        except Exception:
            continue

    return content


# =========================================================
# OPENAI ERROR HANDLING
# =========================================================

def get_api_error_message(error):
    """Return a safe, user-readable API error."""

    message = str(error).lower()

    if "insufficient_quota" in message or "no credits remaining" in message:

        return (
            "OpenAI API credits are exhausted. "
            "Add API credits to enable AI analysis. "
            "Local Diagnostic Mode is still available."
        )

    if "rate_limit_exceeded" in message:

        return (
            "OpenAI API request limit reached. "
            "Please wait and try again. "
            "Local Diagnostic Mode is still available."
        )

    if "invalid_api_key" in message or "authentication" in message:

        return (
            "OpenAI API authentication failed. "
            "Check the API key in Streamlit Secrets."
        )

    if "model_not_found" in message or "does not exist" in message:

        return (
            "The configured OpenAI model is unavailable. "
            "Check OPENAI_MODEL in Streamlit Secrets."
        )

    if "timeout" in message:

        return (
            "OpenAI API request timed out. "
            "Please try again later."
        )

    return (
        "OpenAI AI analysis is currently unavailable. "
        "Local Diagnostic Mode can still be used."
    )


def run_ai_analysis(
    vehicle,
    complaint,
    evidence_context,
    diagnostic_questions=None,
    image_files=None,
):
    """
    Run OpenAI Responses API.
    All API errors are caught and returned safely.
    """

    client = get_client()

    if client is None:

        if not get_api_key():

            return {
                "success": False,
                "analysis": "",
                "error": "OpenAI API key is missing.",
            }

        return {
            "success": False,
            "analysis": "",
            "error": "OpenAI client could not be initialized.",
        }

    prompt = build_diagnostic_prompt(
        vehicle,
        complaint,
        evidence_context,
        diagnostic_questions,
    )

    content = [
        {
            "type": "input_text",
            "text": prompt,
        }
    ]

    image_content = build_image_content(image_files)

    content.extend(image_content)

    try:

        response = client.responses.create(
            model=get_model(),
            input=[
                {
                    "role": "user",
                    "content": content,
                }
            ],
        )

        result = safe_text(
            getattr(response, "output_text", ""),
            "",
        )

        if not result:

            return {
                "success": False,
                "analysis": "",
                "error": "OpenAI returned an empty response.",
            }

        return {
            "success": True,
            "analysis": result,
            "error": "",
        }

    except Exception as error:

        return {
            "success": False,
            "analysis": "",
            "error": get_api_error_message(error),
        }


# =========================================================
# MAIN DIAGNOSTIC FUNCTION
# =========================================================

def analyze_vehicle(
    vehicle,
    complaint,
    dtcs=None,
    freeze_frame=None,
    live_data=None,
    csv_data=None,
    physical_notes=None,
    diagnostic_answers=None,
    image_files=None,
    **kwargs,
):
    """
    Main diagnostic function.

    Returns a dictionary compatible with the Doctor Car app.
    Local analysis is always generated first.
    AI analysis is optional.
    """

    evidence_context = build_evidence_context(
        dtcs=dtcs,
        freeze_frame=freeze_frame,
        live_data=live_data,
        csv_data=csv_data,
        physical_notes=physical_notes,
        diagnostic_answers=diagnostic_answers,
    )

    categories = classify_complaint(complaint)

    question_data = generate_diagnostic_questions(
        vehicle,
        complaint,
    )

    local_analysis = generate_local_analysis(
        vehicle,
        complaint,
        evidence_context,
        diagnostic_answers,
    )

    physical_tests = get_physical_test_recommendations(
        complaint
    )

    ai_result = run_ai_analysis(
        vehicle=vehicle,
        complaint=complaint,
        evidence_context=evidence_context,
        diagnostic_questions=question_data["questions"],
        image_files=image_files,
    )

    if ai_result["success"]:

        diagnosis = ai_result["analysis"]

        analysis_mode = "AI-Assisted Analysis"

        ai_available = True

        ai_error = ""

    else:

        diagnosis = local_analysis

        analysis_mode = "Local Diagnostic Mode"

        ai_available = False

        ai_error = ai_result["error"]

    return {
        "diagnosis": diagnosis,
        "local_analysis": local_analysis,
        "ai_analysis": ai_result["analysis"],
        "ai_available": ai_available,
        "ai_error": ai_error,
        "analysis_mode": analysis_mode,
        "categories": categories,
        "evidence": evidence_context,
        "physical_test_recommendations": physical_tests,
        "overall_status": "Further Diagnosis Required",
        "question_data": question_data,
    }


# =========================================================
# SELF TEST
# =========================================================

def run_diagnostic_engine_self_test():

    test_results = []

    # Test 1: Engine stall classification.
    categories = classify_complaint("Engine stall")

    test_results.append({
        "test": "Engine stall classification",
        "passed": "engine_stall" in categories,
    })

    # Test 2: Local questions.
    questions = generate_diagnostic_questions(
        "2017 Audi A4 2.0 Petrol",
        "Engine stall",
    )

    test_results.append({
        "test": "Engine stall local questions",
        "passed": len(questions["questions"]) > 0,
    })

    # Test 3: Physical test recommendations.
    tests = get_physical_test_recommendations(
        "Engine stall"
    )

    test_results.append({
        "test": "Engine stall physical tests",
        "passed": len(tests) > 0,
    })

    # Test 4: Local analysis.
    local = generate_local_analysis(
        "2017 Audi A4 2.0 Petrol",
        "Engine stall",
    )

    test_results.append({
        "test": "Local analysis generation",
        "passed": "Further Diagnosis Required" in local,
    })

    # Test 5: Fuel delivery guidance.
    fuel_tests = fuel_delivery_guidance(
        "Engine stall"
    )

    test_results.append({
        "test": "Fuel delivery guidance",
        "passed": len(fuel_tests) > 0,
    })

    return {
        "passed": all(
            item["passed"] for item in test_results
        ),
        "total": len(test_results),
        "results": test_results,
    }
