
import re
import sqlite3
from difflib import SequenceMatcher
from pathlib import Path


# =========================================================
# DOCTOR CAR - SMART AUTO PARAMETER MAPPING ENGINE
# =========================================================

DEFAULT_DB = "doctor_car_history.db"

# Standard parameter names and known scanner aliases.
# Add new aliases here as real THINKDIAG CSV files are tested.

PARAMETER_DATABASE = {
    "Engine RPM": {
        "aliases": [
            "rpm", "engine rpm", "engine speed", "eng speed",
            "engine spd", "motor speed", "crankshaft speed"
        ],
        "units": ["rpm", "r/min", "1/min"]
    },

    "Engine Coolant Temperature": {
        "aliases": [
            "ect", "coolant temp", "coolant temperature",
            "engine coolant temp", "engine coolant temperature",
            "water temperature", "engine water temp"
        ],
        "units": ["c", "°c", "deg c", "f", "°f", "deg f"]
    },

    "Intake Air Temperature": {
        "aliases": [
            "iat", "intake air temp", "intake air temperature",
            "air intake temperature", "intake temp"
        ],
        "units": ["c", "°c", "f", "°f"]
    },

    "Mass Air Flow": {
        "aliases": [
            "maf", "maf sensor", "mass air flow",
            "mass airflow", "air flow rate"
        ],
        "units": ["g/s", "kg/h", "lb/min"]
    },

    "Manifold Absolute Pressure": {
        "aliases": [
            "map", "map sensor", "manifold pressure",
            "manifold absolute pressure", "intake manifold pressure"
        ],
        "units": ["kpa", "bar", "psi", "inhg"]
    },

    "Throttle Position": {
        "aliases": [
            "tp", "throttle position", "throttle angle",
            "throttle opening", "absolute throttle position"
        ],
        "units": ["%", "percent", "degree", "degrees"]
    },

    "Accelerator Pedal Position": {
        "aliases": [
            "app", "accelerator pedal position",
            "accelerator position", "pedal position"
        ],
        "units": ["%", "percent", "v"]
    },

    "Short Term Fuel Trim Bank 1": {
        "aliases": [
            "stft b1", "stft bank 1", "short term fuel trim bank 1",
            "short term fuel trim b1", "short fuel trim bank 1"
        ],
        "units": ["%", "percent"]
    },

    "Long Term Fuel Trim Bank 1": {
        "aliases": [
            "ltft b1", "ltft bank 1", "long term fuel trim bank 1",
            "long term fuel trim b1", "long fuel trim bank 1"
        ],
        "units": ["%", "percent"]
    },

    "Short Term Fuel Trim Bank 2": {
        "aliases": [
            "stft b2", "stft bank 2", "short term fuel trim bank 2"
        ],
        "units": ["%", "percent"]
    },

    "Long Term Fuel Trim Bank 2": {
        "aliases": [
            "ltft b2", "ltft bank 2", "long term fuel trim bank 2"
        ],
        "units": ["%", "percent"]
    },

    "Oxygen Sensor Voltage": {
        "aliases": [
            "o2 voltage", "oxygen sensor voltage",
            "o2 sensor voltage", "lambda sensor voltage"
        ],
        "units": ["v", "volt", "volts"]
    },

    "Fuel Rail Pressure": {
        "aliases": [
            "fuel rail pressure", "rail pressure",
            "fuel pressure", "high pressure fuel"
        ],
        "units": ["kpa", "bar", "mpa", "psi"]
    },

    "Vehicle Speed": {
        "aliases": [
            "vehicle speed", "vss", "car speed",
            "road speed", "speed"
        ],
        "units": ["km/h", "kph", "mph"]
    },

    "Battery Voltage": {
        "aliases": [
            "battery voltage", "control module voltage",
            "module voltage", "system voltage",
            "battery volt"
        ],
        "units": ["v", "volt", "volts"]
    },

    "Ignition Timing Advance": {
        "aliases": [
            "ignition timing", "timing advance",
            "spark advance", "ignition advance"
        ],
        "units": ["degree", "degrees", "deg", "°"]
    },

    "Engine Load": {
        "aliases": [
            "engine load", "calculated load",
            "calculated engine load", "load value"
        ],
        "units": ["%", "percent"]
    },

    "Fuel System Status": {
        "aliases": [
            "fuel system status", "fuel status",
            "fuel control status"
        ],
        "units": []
    },

    "Commanded Equivalence Ratio": {
        "aliases": [
            "equivalence ratio", "commanded equivalence ratio",
            "lambda", "commanded lambda"
        ],
        "units": []
    },

    "Coolant Fan Command": {
        "aliases": [
            "cooling fan command", "fan command",
            "radiator fan command", "cooling fan duty",
            "fan duty cycle"
        ],
        "units": ["%", "percent"]
    },
}


# =========================================================
# NORMALIZATION
# =========================================================

def normalize_name(value):
    """Normalize scanner column names for comparison."""
    if value is None:
        return ""

    text = str(value).strip().lower()

    # Remove bracketed unit text from the name.
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"\[[^\]]*\]", " ", text)

    text = text.replace("_", " ")
    text = text.replace("-", " ")
    text = re.sub(r"[^a-z0-9%]+", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_unit(value):
    if value is None:
        return ""

    unit = str(value).strip().lower()
    unit = unit.replace("°", "deg")
    unit = unit.replace(" ", "")
    return unit


def extract_unit(column_name):
    """Extract a unit if the column name contains one."""
    if column_name is None:
        return ""

    text = str(column_name)

    patterns = [
        r"\(([^()]*)\)",
        r"\[([^\[\]]*)\]"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return normalize_unit(match.group(1))

    return ""


# =========================================================
# DATABASE
# =========================================================

def initialize_mapping_database(db_path=DEFAULT_DB):
    """Create the persistent mapping table."""
    connection = sqlite3.connect(db_path)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS parameter_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_name TEXT NOT NULL,
            normalized_name TEXT NOT NULL,
            standard_name TEXT NOT NULL,
            module TEXT DEFAULT '',
            unit TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(normalized_name, module, unit)
        )
    """)

    connection.commit()
    connection.close()


def get_saved_mapping(raw_name, module="", unit="", db_path=DEFAULT_DB):
    """Look for a previously confirmed mapping."""
    initialize_mapping_database(db_path)

    normalized = normalize_name(raw_name)
    module = str(module or "").strip().lower()
    unit = normalize_unit(unit)

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row

    # Prefer an exact module and unit match.
    row = connection.execute("""
        SELECT standard_name
        FROM parameter_mappings
        WHERE normalized_name = ?
          AND module = ?
          AND unit = ?
        LIMIT 1
    """, (normalized, module, unit)).fetchone()

    # Allow a general mapping only when saved without module/unit.
    if row is None:
        row = connection.execute("""
            SELECT standard_name
            FROM parameter_mappings
            WHERE normalized_name = ?
              AND module = ''
              AND unit = ''
            LIMIT 1
        """, (normalized,)).fetchone()

    connection.close()

    return row["standard_name"] if row else None


def save_confirmed_mapping(
    raw_name,
    standard_name,
    module="",
    unit="",
    db_path=DEFAULT_DB
):
    """Save a mapping only after user confirmation."""
    if standard_name not in PARAMETER_DATABASE:
        raise ValueError("Unknown standard parameter name.")

    initialize_mapping_database(db_path)

    normalized = normalize_name(raw_name)
    if not normalized:
        raise ValueError("Parameter name cannot be empty.")

    module = str(module or "").strip().lower()
    unit = normalize_unit(unit)

    connection = sqlite3.connect(db_path)

    connection.execute("""
        INSERT INTO parameter_mappings (
            raw_name,
            normalized_name,
            standard_name,
            module,
            unit
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(normalized_name, module, unit)
        DO UPDATE SET
            raw_name = excluded.raw_name,
            standard_name = excluded.standard_name,
            created_at = CURRENT_TIMESTAMP
    """, (
        str(raw_name),
        normalized,
        standard_name,
        module,
        unit
    ))

    connection.commit()
    connection.close()


# =========================================================
# MATCHING ENGINE
# =========================================================

def unit_is_compatible(standard_name, unit):
    """Reject obviously incompatible units."""
    unit = normalize_unit(unit)

    if not unit:
        return True

    allowed = PARAMETER_DATABASE[standard_name]["units"]

    # If no unit rules exist, do not reject based on unit.
    if not allowed:
        return True

    allowed = [normalize_unit(item) for item in allowed]

    return unit in allowed


def find_exact_match(raw_name, unit=""):
    normalized = normalize_name(raw_name)

    for standard_name, details in PARAMETER_DATABASE.items():
        possible_names = [
            normalize_name(standard_name)
        ] + [
            normalize_name(alias)
            for alias in details["aliases"]
        ]

        if normalized in possible_names:
            if unit_is_compatible(standard_name, unit):
                return standard_name

            return None

    return None


def find_fuzzy_match(raw_name, unit=""):
    """
    Suggest a possible match.
    Fuzzy results are never automatically confirmed.
    """
    normalized = normalize_name(raw_name)

    if not normalized:
        return None, 0.0

    best_name = None
    best_score = 0.0

    for standard_name, details in PARAMETER_DATABASE.items():
        if not unit_is_compatible(standard_name, unit):
            continue

        possible_names = [
            normalize_name(standard_name)
        ] + [
            normalize_name(alias)
            for alias in details["aliases"]
        ]

        for candidate in possible_names:
            score = SequenceMatcher(
                None,
                normalized,
                candidate
            ).ratio()

            if score > best_score:
                best_score = score
                best_name = standard_name

    if best_score >= 0.65:
        return best_name, round(best_score, 2)

    return None, round(best_score, 2)


# =========================================================
# MAIN MAPPING FUNCTION
# =========================================================

def map_parameter(
    raw_name,
    module="",
    unit=None,
    db_path=DEFAULT_DB
):
    """
    Returns:
    Confirmed / Needs Review / Unmapped
    """

    detected_unit = unit if unit is not None else extract_unit(raw_name)

    # 1. Previously confirmed user mapping.
    saved = get_saved_mapping(
        raw_name,
        module,
        detected_unit,
        db_path
    )

    if saved:
        return {
            "raw_name": raw_name,
            "standard_name": saved,
            "status": "Confirmed",
            "method": "Saved Mapping",
            "confidence": 1.0,
            "unit": detected_unit
        }

    # 2. Exact alias matching.
    exact = find_exact_match(raw_name, detected_unit)

    if exact:
        return {
            "raw_name": raw_name,
            "standard_name": exact,
            "status": "Confirmed",
            "method": "Exact Alias",
            "confidence": 1.0,
            "unit": detected_unit
        }

    # 3. Fuzzy suggestion - never auto-confirm.
    suggestion, score = find_fuzzy_match(
        raw_name,
        detected_unit
    )

    if suggestion:
        return {
            "raw_name": raw_name,
            "standard_name": suggestion,
            "status": "Needs Review",
            "method": "Fuzzy Suggestion",
            "confidence": score,
            "unit": detected_unit
        }

    # 4. No safe match.
    return {
        "raw_name": raw_name,
        "standard_name": None,
        "status": "Unmapped",
        "method": "No Match",
        "confidence": 0.0,
        "unit": detected_unit
    }


def map_columns(columns, module="", db_path=DEFAULT_DB):
    """Map a list of CSV column names."""
    results = []

    for column in columns:
        results.append(
            map_parameter(
                raw_name=column,
                module=module,
                db_path=db_path
            )
        )

    return results


def get_mapping_summary(results):
    """Count mapping results."""
    summary = {
        "total": len(results),
        "confirmed": 0,
        "needs_review": 0,
        "unmapped": 0
    }

    for item in results:
        status = item.get("status")

        if status == "Confirmed":
            summary["confirmed"] += 1
        elif status == "Needs Review":
            summary["needs_review"] += 1
        elif status == "Unmapped":
            summary["unmapped"] += 1

    return summary


# =========================================================
# BASIC SELF TEST
# =========================================================

if __name__ == "__main__":
    test_columns = [
        "Engine RPM",
        "ECT (°C)",
        "Coolant Temp",
        "STFT B1 (%)",
        "Battery Voltage (V)",
        "Unknown Sensor Value"
    ]

    print("\nDOCTOR CAR - SMART PARAMETER MAPPING TEST\n")

    results = map_columns(
        test_columns,
        module="Engine"
    )

    for item in results:
        print(
            item["raw_name"],
            "->",
            item["standard_name"],
            "|",
            item["status"],
            "|",
            item["method"]
        )

    print("\nSUMMARY:")
    print(get_mapping_summary(results))
