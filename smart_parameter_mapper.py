
"""
Doctor Car - Smart Automotive Parameter Mapper

Features:
- Maps scanner parameter names to canonical database parameters.
- Uses exact aliases before considering fuzzy suggestions.
- Never auto-confirms fuzzy matches.
- Checks module and unit compatibility.
- Stores manually confirmed mappings in SQLite.
- Keeps the existing parameter_database.py as the source of truth.

Important:
A suggested mapping is not proof that two parameters are equivalent.
Always verify scanner units, module and vehicle-specific meaning.
"""

import os
import re
import sqlite3
from difflib import SequenceMatcher

from parameter_database import PARAMETERS, identify_parameter


# =========================================================
# 1. DATABASE SETTINGS
# =========================================================

DB_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "doctor_car_history.db"
)

TABLE_NAME = "parameter_mappings_v2"


# =========================================================
# 2. TEXT AND UNIT NORMALIZATION
# =========================================================

def normalize_name(value):
    value = str(value or "").strip().lower()
    value = value.replace("%", " percent ")
    value = re.sub(r"[_\-/]+", " ", value)
    value = re.sub(r"[^a-z0-9°]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_unit(unit):
    unit = str(unit or "").strip().lower()
    unit = unit.replace(" ", "")
    unit = unit.replace("°", "deg")

    replacements = {
        "volts": "v",
        "volt": "v",
        "amperes": "a",
        "amp": "a",
        "amps": "a",
        "degrees": "degree",
        "deg": "degree",
        "celsius": "degc",
        "°c": "degc",
        "percent": "%",
        "percentage": "%",
        "kmh": "km/h",
        "kph": "km/h",
        "grams/sec": "g/s",
        "g/sec": "g/s",
        "kilopascal": "kpa",
        "kilopascals": "kpa",
        "newtonmeter": "nm",
        "newtonmeters": "nm",
    }

    return replacements.get(unit, unit)


def unit_is_compatible(source_unit, target_unit):
    """
    Empty source unit means unknown, not automatically incompatible.
    Non-empty different units are not accepted as confirmed matches.
    """
    source = normalize_unit(source_unit)
    target = normalize_unit(target_unit)

    if not source or not target:
        return True

    return source == target


# =========================================================
# 3. SQLITE STORAGE
# =========================================================

def get_connection():
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_name TEXT NOT NULL,
                normalized_name TEXT NOT NULL,
                standard_name TEXT NOT NULL,
                module TEXT DEFAULT '',
                unit TEXT DEFAULT '',
                confirmed INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(normalized_name, module, unit)
            )
            """
        )


initialize_database()


# =========================================================
# 4. MODULE COMPATIBILITY
# =========================================================

def module_is_compatible(source_module, target_module):
    source = normalize_name(source_module)
    target = normalize_name(target_module)

    if not source or not target:
        return True

    if source == target:
        return True

    # Common scanner naming variations.
    aliases = {
        "ecm": "engine",
        "pcm": "engine",
        "powertrain": "engine",
        "tcm": "transmission",
        "at": "transmission",
        "abs": "abs esc",
        "esc": "abs esc",
        "srs airbag": "srs",
        "airbag": "srs",
        "eps": "eps",
        "ac": "hvac",
        "charging": "battery charging",
        "battery": "battery charging",
    }

    source = aliases.get(source, source)
    target = aliases.get(target, target)

    return source == target


# =========================================================
# 5. SAVED MAPPING LOOKUP
# =========================================================

def get_saved_mapping(raw_name, module=None, unit=None):
    normalized = normalize_name(raw_name)

    if not normalized:
        return None

    module_value = str(module or "").strip()
    unit_value = normalize_unit(unit)

    initialize_database()

    with get_connection() as connection:

        # Prefer an exact module and unit match.
        row = connection.execute(
            f"""
            SELECT * FROM {TABLE_NAME}
            WHERE normalized_name = ?
              AND lower(module) = lower(?)
              AND unit = ?
              AND confirmed = 1
            ORDER BY id DESC
            LIMIT 1
            """,
            (normalized, module_value, unit_value)
        ).fetchone()

        if row:
            return dict(row)

        # Generic confirmed mapping is used only when the saved
        # mapping has no module and no unit.
        row = connection.execute(
            f"""
            SELECT * FROM {TABLE_NAME}
            WHERE normalized_name = ?
              AND module = ''
              AND unit = ''
              AND confirmed = 1
            ORDER BY id DESC
            LIMIT 1
            """,
            (normalized,)
        ).fetchone()

        if row:
            return dict(row)

    return None


# =========================================================
# 6. SAVE CONFIRMED MAPPING
# =========================================================

def save_confirmed_mapping(
    raw_name,
    standard_name,
    module=None,
    unit=None
):
    normalized = normalize_name(raw_name)

    if not normalized:
        return False

    if standard_name not in PARAMETERS:
        return False

    metadata = PARAMETERS[standard_name]

    target_module = metadata.get("module", "")
    target_unit = metadata.get("unit", "")

    if module and not module_is_compatible(module, target_module):
        return False

    if unit and not unit_is_compatible(unit, target_unit):
        return False

    module_value = str(module or "").strip()
    unit_value = normalize_unit(unit)

    initialize_database()

    try:
        with get_connection() as connection:
            connection.execute(
                f"""
                INSERT INTO {TABLE_NAME} (
                    raw_name,
                    normalized_name,
                    standard_name,
                    module,
                    unit,
                    confirmed
                )
                VALUES (?, ?, ?, ?, ?, 1)
                ON CONFLICT(normalized_name, module, unit)
                DO UPDATE SET
                    raw_name = excluded.raw_name,
                    standard_name = excluded.standard_name,
                    confirmed = 1
                """,
                (
                    str(raw_name).strip(),
                    normalized,
                    standard_name,
                    module_value,
                    unit_value
                )
            )

        return True

    except sqlite3.Error:
        return False


# =========================================================
# 7. EXACT ALIAS MATCHING
# =========================================================

def find_exact_parameter(raw_name):
    normalized = normalize_name(raw_name)

    if not normalized:
        return None

    # First use the original database identification function.
    result = identify_parameter(raw_name)

    if result in PARAMETERS:
        return result

    # Then check all canonical names and aliases.
    for key, metadata in PARAMETERS.items():

        candidates = [
            key.replace("_", " "),
            metadata.get("label", "")
        ] + metadata.get("aliases", [])

        for candidate in candidates:
            if normalized == normalize_name(candidate):
                return key

    return None


# =========================================================
# 8. FUZZY SUGGESTION
# =========================================================

def find_fuzzy_suggestions(raw_name, limit=3):
    normalized = normalize_name(raw_name)

    if len(normalized) < 5:
        return []

    scores = []

    for key, metadata in PARAMETERS.items():

        candidates = [
            key.replace("_", " "),
            metadata.get("label", "")
        ] + metadata.get("aliases", [])

        best_score = 0.0

        for candidate in candidates:
            candidate_name = normalize_name(candidate)

            if not candidate_name:
                continue

            score = SequenceMatcher(
                None,
                normalized,
                candidate_name
            ).ratio()

            best_score = max(best_score, score)

        if best_score >= 0.72:
            scores.append({
                "standard_name": key,
                "label": metadata["label"],
                "module": metadata["module"],
                "unit": metadata["unit"],
                "similarity": round(best_score, 3)
            })

    scores.sort(
        key=lambda item: item["similarity"],
        reverse=True
    )

    return scores[:limit]


# =========================================================
# 9. MAIN PARAMETER MAPPER
# =========================================================

def map_parameter(raw_name, module=None, unit=None):
    """
    Returns a dictionary with:
    status: Confirmed / Needs Review / Unmapped
    standard_name: canonical parameter key, or None
    """

    raw_name = str(raw_name or "").strip()

    result = {
        "raw_name": raw_name,
        "standard_name": None,
        "label": None,
        "module": None,
        "unit": None,
        "status": "Unmapped",
        "matched_by": None,
        "suggestions": [],
        "message": "No reliable parameter match found."
    }

    if not raw_name:
        result["message"] = "Parameter name is empty."
        return result

    # 1. Check manually confirmed saved mappings.
    saved = get_saved_mapping(raw_name, module, unit)

    if saved:
        key = saved.get("standard_name")

        if key in PARAMETERS:
            metadata = PARAMETERS[key]

            if (
                module_is_compatible(module, metadata["module"])
                and unit_is_compatible(unit, metadata["unit"])
            ):
                result.update({
                    "standard_name": key,
                    "label": metadata["label"],
                    "module": metadata["module"],
                    "unit": metadata["unit"],
                    "status": "Confirmed",
                    "matched_by": "Saved Manual Mapping",
                    "message": "Previously confirmed mapping."
                })
                return result

    # 2. Check exact database aliases.
    key = find_exact_parameter(raw_name)

    if key:
        metadata = PARAMETERS[key]

        module_ok = module_is_compatible(module, metadata["module"])
        unit_ok = unit_is_compatible(unit, metadata["unit"])

        if module_ok and unit_ok:
            result.update({
                "standard_name": key,
                "label": metadata["label"],
                "module": metadata["module"],
                "unit": metadata["unit"],
                "status": "Confirmed",
                "matched_by": "Exact Database Alias",
                "message": "Exact alias match. Confirm vehicle-specific meaning and units."
            })
            return result

        result.update({
            "standard_name": key,
            "label": metadata["label"],
            "module": metadata["module"],
            "unit": metadata["unit"],
            "status": "Needs Review",
            "matched_by": "Exact Alias With Compatibility Warning",
            "message": (
                "Parameter name matched, but supplied module or unit "
                "does not agree with the database."
            )
        })
        return result

    # 3. Fuzzy matches are suggestions only.
    suggestions = find_fuzzy_suggestions(raw_name)

    if suggestions:
        result.update({
            "status": "Needs Review",
            "matched_by": "Fuzzy Suggestion",
            "suggestions": suggestions,
            "message": (
                "Possible match found. Human confirmation is required. "
                "This mapping must not be treated as confirmed diagnostic data."
            )
        })

    return result


# =========================================================
# 10. MAP MULTIPLE COLUMNS
# =========================================================

def map_columns(columns, module=None, units=None):
    """
    Returns a dictionary:
    {
        original_column_name: mapping_result
    }
    """

    results = {}
    units = units or {}

    for column in columns:
        results[column] = map_parameter(
            raw_name=column,
            module=module,
            unit=units.get(column)
        )

    return results


# =========================================================
# 11. MAPPING SUMMARY
# =========================================================

def get_mapping_summary(mapped_columns=None):
    """
    Can summarize either:
    - A mapping dictionary returned by map_columns()
    - A list of mapping result dictionaries
    """

    if mapped_columns is None:
        return {
            "total": 0,
            "confirmed": 0,
            "needs_review": 0,
            "unmapped": 0
        }

    if isinstance(mapped_columns, dict):
        items = list(mapped_columns.values())
    else:
        items = list(mapped_columns)

    confirmed = sum(
        1 for item in items
        if item.get("status") == "Confirmed"
    )

    needs_review = sum(
        1 for item in items
        if item.get("status") == "Needs Review"
    )

    unmapped = sum(
        1 for item in items
        if item.get("status") == "Unmapped"
    )

    return {
        "total": len(items),
        "confirmed": confirmed,
        "needs_review": needs_review,
        "unmapped": unmapped
    }


# =========================================================
# 12. SELF TEST
# =========================================================

def run_mapper_self_test():

    test_names = [
        "Engine RPM",
        "Fuel Rail Pressure",
        "Low Side Fuel Pressure",
        "Actual Fuel Rail Pressure",
        "Commanded Fuel Rail Pressure",
        "Fuel Tank Pressure",
        "Fuel Level",
        "Battery Voltage",
        "Unknown Scanner Parameter"
    ]

    results = []

    for name in test_names:
        result = map_parameter(name)

        results.append({
            "input": name,
            "status": result["status"],
            "standard_name": result["standard_name"]
        })

    return results
