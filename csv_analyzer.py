"""
Doctor Car - Advanced CSV Analyzer

Features:
- THINKDIAG / Autel scanner CSV support
- Column-based and row-based CSV handling
- Smart parameter mapping
- Confirmed vs Needs Review separation
- Unit and data-quality checks
- Missing-data detection
- Live-data trend analysis
- Operating-condition comparison
- AI-ready diagnostic summary

Important:
Unconfirmed parameter mappings are never treated as confirmed
diagnostic evidence.
"""

import csv
import io
import math
import re
from typing import Any, Dict, List, Optional

import pandas as pd

from parameter_database import (
    PARAMETERS,
    default_parameter_requirements,
)

from smart_parameter_mapper import (
    map_columns,
    map_parameter,
    get_mapping_summary,
)


# =========================================================
# 1. BASIC DATA CLEANING
# =========================================================

def clean_number(value):
    """Convert scanner values into numbers safely."""

    if value is None:
        return None

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return value

    text = str(value).strip()

    if not text:
        return None

    invalid_values = {
        "-", "--", "---", "n/a", "na", "null",
        "none", "not available", "invalid",
        "error", "no data"
    }

    if text.lower() in invalid_values:
        return None

    text = text.replace(",", "")

    match = re.search(
        r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?",
        text
    )

    if not match:
        return None

    try:
        number = float(match.group())

        if not math.isfinite(number):
            return None

        return number

    except (ValueError, TypeError):
        return None


def normalize_column_name(name):
    if name is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(name).strip()
    )


def detect_unit(column_name):
    """Extract a unit written in a column heading."""

    if not column_name:
        return None

    text = str(column_name).strip()

    patterns = [
        r"\(([^()]*)\)\s*$",
        r"\[([^\[\]]*)\]\s*$",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return match.group(1).strip()

    return None


# =========================================================
# 2. CSV READING
# =========================================================

def read_scanner_csv(uploaded_file):
    """
    Read a CSV from Streamlit UploadedFile, file path,
    bytes, or file-like object.
    """

    if isinstance(uploaded_file, pd.DataFrame):
        return uploaded_file.copy()

    if isinstance(uploaded_file, bytes):
        raw_data = uploaded_file

    elif isinstance(uploaded_file, str):
        with open(uploaded_file, "rb") as file:
            raw_data = file.read()

    else:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass

        raw_data = uploaded_file.read()

    if isinstance(raw_data, str):
        raw_data = raw_data.encode("utf-8-sig")

    if not raw_data:
        raise ValueError("The uploaded CSV file is empty.")

    encodings = [
        "utf-8-sig",
        "utf-8",
        "cp1252",
        "latin1",
    ]

    decoded = None

    for encoding in encodings:
        try:
            decoded = raw_data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    if decoded is None:
        raise ValueError(
            "Unable to read CSV encoding. "
            "Please export the scanner data as UTF-8 CSV."
        )

    try:
        dialect = csv.Sniffer().sniff(
            decoded[:10000],
            delimiters=",;\t|"
        )

        delimiter = dialect.delimiter

    except Exception:
        delimiter = ","

    try:
        dataframe = pd.read_csv(
            io.StringIO(decoded),
            sep=delimiter,
            dtype=str,
            on_bad_lines="skip"
        )

    except Exception:
        dataframe = pd.read_csv(
            io.StringIO(decoded),
            sep=None,
            engine="python",
            dtype=str,
            on_bad_lines="skip"
        )

    dataframe.columns = [
        normalize_column_name(column)
        for column in dataframe.columns
    ]

    dataframe = dataframe.dropna(
        axis=0,
        how="all"
    )

    dataframe = dataframe.dropna(
        axis=1,
        how="all"
    )

    if dataframe.empty:
        raise ValueError(
            "No usable data was found in the CSV file."
        )

    return dataframe


# =========================================================
# 3. TIME COLUMN DETECTION
# =========================================================

def find_time_column(dataframe):

    keywords = [
        "time",
        "timestamp",
        "elapsed",
        "seconds",
        "record time",
        "sample time",
    ]

    for column in dataframe.columns:

        name = str(column).lower()

        if any(keyword in name for keyword in keywords):
            return column

    return None


# =========================================================
# 4. NUMERIC DATA EXTRACTION
# =========================================================

def get_numeric_series(dataframe, column):

    if column not in dataframe.columns:
        return pd.Series(dtype=float)

    return dataframe[column].apply(clean_number)


def calculate_trend(values):
    """
    Calculate a basic trend.

    This does not determine whether a value is healthy.
    Vehicle-specific specifications are still required.
    """

    numbers = [
        float(value)
        for value in values
        if value is not None
        and not pd.isna(value)
    ]

    if len(numbers) < 2:
        return {
            "trend": "Insufficient Data",
            "change": None,
            "first_value": numbers[0] if numbers else None,
            "last_value": numbers[-1] if numbers else None,
        }

    first_value = numbers[0]
    last_value = numbers[-1]
    change = last_value - first_value

    if abs(change) < 0.000001:
        trend = "Stable"

    elif change > 0:
        trend = "Increasing"

    else:
        trend = "Decreasing"

    return {
        "trend": trend,
        "change": change,
        "first_value": first_value,
        "last_value": last_value,
    }


def summarize_values(values):

    numbers = [
        float(value)
        for value in values
        if value is not None
        and not pd.isna(value)
    ]

    if not numbers:
        return {
            "count": 0,
            "minimum": None,
            "maximum": None,
            "average": None,
            "first": None,
            "last": None,
        }

    return {
        "count": len(numbers),
        "minimum": min(numbers),
        "maximum": max(numbers),
        "average": sum(numbers) / len(numbers),
        "first": numbers[0],
        "last": numbers[-1],
    }


# =========================================================
# 5. INDIVIDUAL COLUMN ANALYSIS
# =========================================================

def analyze_column_data(dataframe, column):

    values = get_numeric_series(
        dataframe,
        column
    )

    valid_values = values.dropna().tolist()

    summary = summarize_values(valid_values)

    trend = calculate_trend(valid_values)

    total_rows = len(dataframe)

    missing_count = total_rows - len(valid_values)

    missing_percentage = (
        (missing_count / total_rows) * 100
        if total_rows
        else 0
    )

    return {
        "column": column,
        "unit": detect_unit(column),
        "summary": summary,
        "trend": trend,
        "missing_count": missing_count,
        "missing_percentage": round(
            missing_percentage,
            2
        ),
        "valid_count": len(valid_values),
    }


# =========================================================
# 6. ROW-ORIENTED DATA ANALYSIS
# =========================================================

def analyze_row_data(dataframe):

    """
    Detect common scanner formats where parameters are listed
    vertically instead of being separate columns.

    Example:
    Parameter | Value | Unit
    RPM       | 750   | rpm
    Coolant   | 92    | °C
    """

    if dataframe.empty:
        return []

    column_lookup = {
        str(column).strip().lower(): column
        for column in dataframe.columns
    }

    parameter_candidates = [
        "parameter",
        "name",
        "pid",
        "description",
        "data item",
        "item",
    ]

    value_candidates = [
        "value",
        "actual value",
        "current value",
        "reading",
        "data",
    ]

    unit_candidates = [
        "unit",
        "units",
    ]

    parameter_column = next(
        (
            column_lookup[key]
            for key in parameter_candidates
            if key in column_lookup
        ),
        None
    )

    value_column = next(
        (
            column_lookup[key]
            for key in value_candidates
            if key in column_lookup
        ),
        None
    )

    unit_column = next(
        (
            column_lookup[key]
            for key in unit_candidates
            if key in column_lookup
        ),
        None
    )

    if not parameter_column or not value_column:
        return []

    results = []

    for _, row in dataframe.iterrows():

        parameter_name = row.get(parameter_column)

        value = row.get(value_column)

        unit = (
            row.get(unit_column)
            if unit_column
            else None
        )

        if pd.isna(parameter_name):
            continue

        numeric_value = clean_number(value)

        results.append({
            "parameter": str(parameter_name).strip(),
            "value": numeric_value,
            "raw_value": str(value),
            "unit": (
                str(unit).strip()
                if unit is not None and not pd.isna(unit)
                else None
            ),
        })

    return results


# =========================================================
# 7. PARAMETER MAPPING
# =========================================================

def build_parameter_mapping(dataframe, module=None):

    columns = list(dataframe.columns)

    units = {
        column: detect_unit(column)
        for column in columns
    }

    try:
        mapped = map_columns(
            columns,
            module=module,
            units=units
        )

    except Exception as error:

        mapped = {}

        for column in columns:

            try:
                mapped[column] = map_parameter(
                    column,
                    module=module,
                    unit=units.get(column)
                )

            except Exception:
                mapped[column] = {
                    "status": "Needs Review",
                    "standard_name": None,
                    "raw_name": column,
                    "reason": "Mapping could not be completed.",
                }

    return mapped


def separate_confirmed_and_review(mapped_columns):

    confirmed = {}
    needs_review = {}
    unmapped = {}

    for raw_name, result in mapped_columns.items():

        if not isinstance(result, dict):
            unmapped[raw_name] = result
            continue

        status = result.get("status", "")

        if status == "Confirmed":

            standard_name = result.get("standard_name")

            if standard_name:
                confirmed[raw_name] = result
            else:
                unmapped[raw_name] = result

        elif status == "Needs Review":
            needs_review[raw_name] = result

        else:
            unmapped[raw_name] = result

    return confirmed, needs_review, unmapped


# =========================================================
# 8. REQUIRED PARAMETER CHECK
# =========================================================

def check_required_parameters(
    required_parameters,
    confirmed_parameters
):

    required_parameters = required_parameters or []

    confirmed_names = set()

    for result in confirmed_parameters.values():

        if isinstance(result, dict):

            name = result.get("standard_name")

            if name:
                confirmed_names.add(name)

    missing = [
        parameter
        for parameter in required_parameters
        if parameter not in confirmed_names
    ]

    available = [
        parameter
        for parameter in required_parameters
        if parameter in confirmed_names
    ]

    return {
        "required": required_parameters,
        "available": available,
        "missing": missing,
        "complete": len(missing) == 0,
    }


# =========================================================
# 9. CONDITION COMPARISON
# =========================================================

def compare_conditions(
    dataframe,
    condition_column=None,
    parameter_columns=None
):

    """
    Compare numeric parameters across operating conditions.

    Example:
    Idle vs Acceleration
    Engine OFF vs Engine ON

    This is descriptive comparison, not an OEM pass/fail test.
    """

    if not condition_column:
        return {}

    if condition_column not in dataframe.columns:
        return {}

    parameter_columns = parameter_columns or []

    results = {}

    conditions = dataframe[
        condition_column
    ].dropna().unique()

    for column in parameter_columns:

        condition_results = {}

        for condition in conditions:

            subset = dataframe[
                dataframe[condition_column] == condition
            ]

            values = get_numeric_series(
                subset,
                column
            ).dropna().tolist()

            condition_results[str(condition)] = (
                summarize_values(values)
            )

        results[column] = condition_results

    return results


# =========================================================
# 10. DATA QUALITY CHECK
# =========================================================

def check_data_quality(dataframe):

    total_rows = len(dataframe)
    total_columns = len(dataframe.columns)

    if total_rows == 0 or total_columns == 0:

        return {
            "status": "Invalid",
            "total_rows": total_rows,
            "total_columns": total_columns,
            "duplicate_rows": 0,
            "empty_cells": 0,
            "empty_percentage": 100,
            "warnings": ["No usable CSV data found."],
        }

    duplicate_rows = int(
        dataframe.duplicated().sum()
    )

    empty_cells = int(
        dataframe.isna().sum().sum()
    )

    total_cells = total_rows * total_columns

    empty_percentage = (
        (empty_cells / total_cells) * 100
        if total_cells
        else 0
    )

    warnings = []

    if duplicate_rows:
        warnings.append(
            f"{duplicate_rows} duplicate rows detected."
        )

    if empty_cells:
        warnings.append(
            f"{empty_cells} empty cells detected."
        )

    if total_rows < 2:
        warnings.append(
            "Only one data row is available. Trend analysis is limited."
        )

    if total_columns < 2:
        warnings.append(
            "Very few columns detected."
        )

    status = (
        "Good"
        if empty_percentage < 20 and total_rows >= 2
        else "Review Required"
    )

    return {
        "status": status,
        "total_rows": total_rows,
        "total_columns": total_columns,
        "duplicate_rows": duplicate_rows,
        "empty_cells": empty_cells,
        "empty_percentage": round(
            empty_percentage,
            2
        ),
        "warnings": warnings,
    }


# =========================================================
# 11. MAIN CSV ANALYSIS
# =========================================================

def analyze_csv(
    uploaded_file,
    required_parameters=None,
    condition_column=None,
    module=None,
    complaint=None
):

    dataframe = read_scanner_csv(uploaded_file)

    file_name = getattr(
        uploaded_file,
        "name",
        "scanner_data.csv"
    )

    time_column = find_time_column(dataframe)

    row_data = analyze_row_data(dataframe)

    mapped_columns = build_parameter_mapping(
        dataframe,
        module=module
    )

    confirmed, needs_review, unmapped = (
        separate_confirmed_and_review(
            mapped_columns
        )
    )

    detected = {}

    for raw_column, mapping in confirmed.items():

        standard_name = mapping.get("standard_name")

        if not standard_name:
            continue

        detected[standard_name] = {
            "raw_column": raw_column,
            "mapping": mapping,
            "analysis": analyze_column_data(
                dataframe,
                raw_column
            ),
        }

    if required_parameters is None:

        try:
            required_parameters = (
                default_parameter_requirements(
                    module or "",
                    complaint or ""
                )
            )

        except Exception:
            required_parameters = []

    required_check = check_required_parameters(
        required_parameters,
        confirmed
    )

    numeric_columns = [
        column
        for column in dataframe.columns
        if get_numeric_series(
            dataframe,
            column
        ).notna().any()
    ]

    condition_comparisons = compare_conditions(
        dataframe,
        condition_column=condition_column,
        parameter_columns=numeric_columns
    )

    data_quality = check_data_quality(
        dataframe
    )

    try:
        mapping_summary = get_mapping_summary(
            mapped_columns
        )

    except Exception:
        mapping_summary = {
            "confirmed": len(confirmed),
            "needs_review": len(needs_review),
            "unmapped": len(unmapped),
        }

    summary = {
        "total_rows": len(dataframe),
        "total_columns": len(dataframe.columns),
        "confirmed_parameters": len(confirmed),
        "parameters_needing_review": len(needs_review),
        "unmapped_parameters": len(unmapped),
        "required_parameters_available": len(
            required_check["available"]
        ),
        "required_parameters_missing": len(
            required_check["missing"]
        ),
        "data_quality": data_quality["status"],
    }

    return {
        "dataframe": dataframe,
        "rows": row_data,
        "columns": list(dataframe.columns),
        "detected": detected,
        "confirmed": confirmed,
        "needs_review": needs_review,
        "unmapped": unmapped,
        "mapped_columns": mapped_columns,
        "mapping_summary": mapping_summary,
        "summary": summary,
        "time_column": time_column,
        "required_parameters": required_check,
        "condition_comparisons": condition_comparisons,
        "file_name": file_name,
        "data_quality": data_quality,
    }


# =========================================================
# 12. AI-READY CSV SUMMARY
# =========================================================

def get_csv_text_for_ai(analysis):

    if not isinstance(analysis, dict):
        return "CSV analysis data is unavailable."

    lines = []

    lines.append("DOCTOR CAR - SCANNER CSV ANALYSIS")
    lines.append("=" * 45)

    lines.append(
        f"File: {analysis.get('file_name', 'Unknown')}"
    )

    summary = analysis.get("summary", {})

    lines.append(
        f"Rows: {summary.get('total_rows', 0)}"
    )

    lines.append(
        f"Columns: {summary.get('total_columns', 0)}"
    )

    lines.append(
        f"Data Quality: {summary.get('data_quality', 'Unknown')}"
    )

    lines.append("")
    lines.append("CONFIRMED PARAMETERS")
    lines.append("-" * 30)

    detected = analysis.get("detected", {})

    if not detected:
        lines.append(
            "No confirmed parameters were identified."
        )

    for standard_name, item in detected.items():

        details = item.get("analysis", {})

        value_summary = details.get(
            "summary",
            {}
        )

        trend = details.get(
            "trend",
            {}
        )

        lines.append(
            f"{standard_name}: "
            f"minimum={value_summary.get('minimum')}, "
            f"maximum={value_summary.get('maximum')}, "
            f"average={value_summary.get('average')}, "
            f"first={value_summary.get('first')}, "
            f"last={value_summary.get('last')}, "
            f"trend={trend.get('trend')}"
        )

    lines.append("")
    lines.append("PARAMETERS NEEDING REVIEW")
    lines.append("-" * 30)

    for raw_name, result in (
        analysis.get("needs_review", {}).items()
    ):

        lines.append(
            f"{raw_name}: "
            f"{result.get('standard_name') or 'Not identified'}"
        )

    lines.append("")
    lines.append("UNMAPPED PARAMETERS")
    lines.append("-" * 30)

    for raw_name in analysis.get("unmapped", {}):
        lines.append(str(raw_name))

    required = analysis.get(
        "required_parameters",
        {}
    )

    lines.append("")
    lines.append("REQUIRED PARAMETER CHECK")
    lines.append("-" * 30)

    lines.append(
        "Available: "
        + ", ".join(required.get("available", []))
    )

    lines.append(
        "Missing: "
        + ", ".join(required.get("missing", []))
    )

    quality = analysis.get(
        "data_quality",
        {}
    )

    lines.append("")
    lines.append("DATA QUALITY WARNINGS")

    for warning in quality.get("warnings", []):
        lines.append(f"- {warning}")

    lines.append("")
    lines.append(
        "DIAGNOSTIC LIMITATION: "
        "CSV trends alone do not establish component failure. "
        "Interpret values using vehicle-specific specifications, "
        "operating conditions, DTCs, freeze-frame data and "
        "physical confirmation tests. Missing values must not "
        "be treated as zero or normal."
    )

    return "\n".join(lines)


def build_csv_ai_summary(analysis):

    return get_csv_text_for_ai(analysis)


# =========================================================
# 13. QUICK SELF-TEST
# =========================================================

def run_csv_analyzer_self_test():

    test_data = pd.DataFrame({
        "Engine RPM (rpm)": [
            "750",
            "780",
            "820",
        ],
        "Coolant Temperature (°C)": [
            "88",
            "90",
            "92",
        ],
        "Fuel Pressure (kPa)": [
            "350",
            "345",
            "340",
        ],
    })

    result = analyze_csv(
        test_data,
        required_parameters=[]
    )

    return {
        "success": isinstance(result, dict),
        "rows": result.get("summary", {}).get("total_rows"),
        "columns": result.get("summary", {}).get("total_columns"),
        "confirmed_parameters": result.get(
            "summary",
            {}
        ).get("confirmed_parameters"),
    }
