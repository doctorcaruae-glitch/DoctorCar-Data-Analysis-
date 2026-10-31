
import pandas as pd
import io
import re
from difflib import SequenceMatcher

from parameter_database import (
    identify_parameter,
    get_parameter_metadata
)

from smart_parameter_mapper import (
    map_parameter,
    get_mapping_summary
)


# ============================================================
# BASIC HELPERS
# ============================================================

def clean_number(value):
    """Convert scanner values into numbers safely."""

    if pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()

    if not text:
        return None

    text = text.replace(",", "")
    text = text.replace("%", "")
    text = text.replace("°", "")

    match = re.search(r"-?\d+(?:\.\d+)?", text)

    if not match:
        return None

    try:
        return float(match.group())
    except (ValueError, TypeError):
        return None


def normalize_text(value):
    if value is None:
        return ""

    text = str(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# ============================================================
# SMART PARAMETER MAPPING
# ============================================================

def identify_smart_parameter(raw_name, module=""):
    """
    First use the existing parameter database.
    Then use Smart Parameter Mapper.
    Unconfirmed fuzzy matches are never treated as confirmed.
    """

    legacy_key = None

    try:
        legacy_key = identify_parameter(str(raw_name))
    except Exception:
        legacy_key = None

    try:
        mapping = map_parameter(
            str(raw_name),
            module=module or ""
        )
    except Exception as error:
        mapping = {
            "status": "Unmapped",
            "standard_name": None,
            "message": str(error)
        }

    if not isinstance(mapping, dict):
        mapping = {
            "status": "Unmapped",
            "standard_name": None
        }

    status = mapping.get("status", "Unmapped")
    standard_name = mapping.get("standard_name")

    # Existing database match is trusted.
    if legacy_key:
        return {
            "parameter_key": legacy_key,
            "standard_name": standard_name or str(raw_name),
            "status": "Confirmed",
            "source": "Existing Parameter Database",
            "mapping": mapping
        }

    # Smart mapper confirmed match.
    if status == "Confirmed" and standard_name:
        try:
            resolved_key = identify_parameter(standard_name)
        except Exception:
            resolved_key = None

        if resolved_key:
            return {
                "parameter_key": resolved_key,
                "standard_name": standard_name,
                "status": "Confirmed",
                "source": "Smart Parameter Mapper",
                "mapping": mapping
            }

        # The mapping is confirmed by the mapper,
        # but the old diagnostic database does not know this key.
        return {
            "parameter_key": None,
            "standard_name": standard_name,
            "status": "Needs Review",
            "source": "Smart Mapper - Database Key Missing",
            "mapping": mapping
        }

    return {
        "parameter_key": None,
        "standard_name": standard_name,
        "status": status,
        "source": "Smart Parameter Mapper",
        "mapping": mapping
    }


# ============================================================
# CSV READER
# ============================================================

def read_scanner_csv(uploaded_file):
    """
    Read scanner CSV files with different encodings
    and separators.
    """

    if uploaded_file is None:
        raise ValueError("No CSV file uploaded.")

    raw_data = uploaded_file.getvalue()

    if not raw_data:
        raise ValueError("The uploaded CSV file is empty.")

    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin1"]
    separators = [",", ";", "\t", "|"]

    last_error = None

    for encoding in encodings:
        for separator in separators:
            try:
                df = pd.read_csv(
                    io.BytesIO(raw_data),
                    encoding=encoding,
                    sep=separator,
                    engine="python"
                )

                if len(df.columns) > 1 and len(df) > 0:
                    df.columns = [
                        str(col).strip()
                        for col in df.columns
                    ]
                    return df

            except Exception as error:
                last_error = error

    # Try automatic separator detection.
    for encoding in encodings:
        try:
            df = pd.read_csv(
                io.BytesIO(raw_data),
                encoding=encoding,
                sep=None,
                engine="python"
            )

            if len(df.columns) > 1 and len(df) > 0:
                df.columns = [
                    str(col).strip()
                    for col in df.columns
                ]
                return df

        except Exception as error:
            last_error = error

    raise ValueError(
        "Could not read this scanner CSV file. "
        "Please check the file format. "
        f"Details: {last_error}"
    )


# ============================================================
# TIME COLUMN DETECTION
# ============================================================

def find_time_column(df):

    if df is None or df.empty:
        return None

    time_keywords = [
        "time",
        "timestamp",
        "elapsed time",
        "sample time",
        "record time",
        "date time"
    ]

    for column in df.columns:
        name = normalize_text(column)

        if any(keyword in name for keyword in time_keywords):
            return column

    return None


# ============================================================
# TREND ANALYSIS
# ============================================================

def calculate_trend(values):

    numeric_values = [
        clean_number(value)
        for value in values
    ]

    numeric_values = [
        value for value in numeric_values
        if value is not None
    ]

    if len(numeric_values) < 2:
        return "Insufficient Data"

    first = numeric_values[0]
    last = numeric_values[-1]

    difference = last - first

    if abs(difference) < 0.0001:
        return "Stable"

    if difference > 0:
        return "Increasing"

    return "Decreasing"


# ============================================================
# VALUE SUMMARY
# ============================================================

def summarize_values(values, parameter_key=None):

    numeric_values = [
        clean_number(value)
        for value in values
    ]

    numeric_values = [
        value for value in numeric_values
        if value is not None
    ]

    result = {
        "count": len(numeric_values),
        "missing_count": max(
            0,
            len(values) - len(numeric_values)
        ),
        "min": None,
        "max": None,
        "average": None,
        "first": None,
        "last": None,
        "trend": "Insufficient Data",
        "metadata": {}
    }

    if not numeric_values:
        return result

    result["min"] = min(numeric_values)
    result["max"] = max(numeric_values)
    result["average"] = sum(numeric_values) / len(numeric_values)
    result["first"] = numeric_values[0]
    result["last"] = numeric_values[-1]
    result["trend"] = calculate_trend(numeric_values)

    if parameter_key:
        try:
            metadata = get_parameter_metadata(parameter_key)
            if isinstance(metadata, dict):
                result["metadata"] = metadata
        except Exception:
            pass

    return result


# ============================================================
# COLUMN-BASED CSV ANALYSIS
# ============================================================

def analyze_column_data(df, module=""):

    detected = {}
    unmapped = []
    needs_review = []
    mapping_details = []

    for column in df.columns:

        mapping_result = identify_smart_parameter(
            column,
            module=module
        )

        status = mapping_result["status"]
        parameter_key = mapping_result["parameter_key"]

        detail = {
            "raw_name": str(column),
            "standard_name": mapping_result["standard_name"],
            "status": status,
            "source": mapping_result["source"],
            "parameter_key": parameter_key
        }

        mapping_details.append(detail)

        if status == "Confirmed" and parameter_key:

            summary = summarize_values(
                df[column].tolist(),
                parameter_key
            )

            summary["column_name"] = str(column)
            summary["standard_name"] = (
                mapping_result["standard_name"]
            )
            summary["mapping_status"] = "Confirmed"

            detected[str(column)] = {
                "parameter_key": parameter_key,
                "standard_name": mapping_result["standard_name"],
                "summary": summary,
                "values": df[column].tolist()
            }

        elif status == "Needs Review":
            needs_review.append(detail)

        else:
            unmapped.append(str(column))

    return {
        "detected": detected,
        "unmapped": unmapped,
        "needs_review": needs_review,
        "mapping_details": mapping_details
    }


# ============================================================
# ROW-BASED CSV ANALYSIS
# ============================================================

def analyze_row_data(df, module=""):

    detected = {}
    unmapped = []
    needs_review = []
    mapping_details = []

    if df.empty:
        return {
            "detected": detected,
            "unmapped": unmapped,
            "needs_review": needs_review,
            "mapping_details": mapping_details
        }

    for index, row in df.iterrows():

        if len(row) < 2:
            continue

        raw_name = str(row.iloc[0]).strip()

        if not raw_name or raw_name.lower() == "nan":
            continue

        mapping_result = identify_smart_parameter(
            raw_name,
            module=module
        )

        status = mapping_result["status"]
        parameter_key = mapping_result["parameter_key"]

        detail = {
            "raw_name": raw_name,
            "standard_name": mapping_result["standard_name"],
            "status": status,
            "source": mapping_result["source"],
            "parameter_key": parameter_key
        }

        mapping_details.append(detail)

        values = row.iloc[1:].tolist()

        if status == "Confirmed" and parameter_key:

            summary = summarize_values(
                values,
                parameter_key
            )

            summary["row_name"] = raw_name
            summary["standard_name"] = (
                mapping_result["standard_name"]
            )
            summary["mapping_status"] = "Confirmed"

            detected[raw_name] = {
                "parameter_key": parameter_key,
                "standard_name": mapping_result["standard_name"],
                "summary": summary,
                "values": values
            }

        elif status == "Needs Review":
            needs_review.append(detail)

        else:
            unmapped.append(raw_name)

    return {
        "detected": detected,
        "unmapped": unmapped,
        "needs_review": needs_review,
        "mapping_details": mapping_details
    }


# ============================================================
# REQUIRED PARAMETER CHECK
# ============================================================

def check_required_parameters(
    detected,
    required_parameters=None
):

    if not required_parameters:
        return {
            "required": [],
            "found": [],
            "missing": []
        }

    found_keys = set()

    for item in detected.values():
        key = item.get("parameter_key")
        if key:
            found_keys.add(key)

    found = []
    missing = []

    for parameter in required_parameters:

        if parameter in found_keys:
            found.append(parameter)
        else:
            missing.append(parameter)

    return {
        "required": required_parameters,
        "found": found,
        "missing": missing
    }


# ============================================================
# CONDITION COMPARISON
# ============================================================

def compare_conditions(
    df,
    detected,
    condition_column
):

    comparisons = {}

    if (
        condition_column not in df.columns
        or condition_column is None
    ):
        return comparisons

    conditions = df[condition_column].dropna().unique()

    if len(conditions) < 2:
        return comparisons

    for column_name, parameter_data in detected.items():

        if column_name not in df.columns:
            continue

        parameter_comparison = {}

        for condition in conditions:

            subset = df[
                df[condition_column] == condition
            ][column_name]

            summary = summarize_values(
                subset.tolist(),
                parameter_data.get("parameter_key")
            )

            parameter_comparison[str(condition)] = summary

        comparisons[column_name] = parameter_comparison

    return comparisons


# ============================================================
# MAIN CSV ANALYSIS
# ============================================================

def analyze_csv(
    uploaded_file,
    required_parameters=None,
    condition_column=None,
    module=""
):

    df = read_scanner_csv(uploaded_file)

    if df.empty:
        raise ValueError("CSV file contains no data rows.")

    time_column = find_time_column(df)

    # Detect whether the CSV is column-based or row-based.
    column_result = analyze_column_data(
        df,
        module=module
    )

    row_result = analyze_row_data(
        df,
        module=module
    )

    # Choose the layout with more confirmed parameters.
    if len(row_result["detected"]) > len(column_result["detected"]):
        selected = row_result
        csv_layout = "Row Based"
    else:
        selected = column_result
        csv_layout = "Column Based"

    detected = selected["detected"]
    unmapped = selected["unmapped"]
    needs_review = selected["needs_review"]
    mapping_details = selected["mapping_details"]

    required_check = check_required_parameters(
        detected,
        required_parameters
    )

    condition_comparisons = {}

    if condition_column:
        condition_comparisons = compare_conditions(
            df,
            detected,
            condition_column
        )

    total_parameters = len(mapping_details)

    confirmed_count = sum(
        1 for item in mapping_details
        if item["status"] == "Confirmed"
    )

    review_count = len(needs_review)
    unmapped_count = len(unmapped)

    data_quality = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "total_parameters": total_parameters,
        "confirmed_parameters": confirmed_count,
        "needs_review": review_count,
        "unmapped_parameters": unmapped_count,
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "csv_layout": csv_layout
    }

    mapping_summary = {
        "total": total_parameters,
        "confirmed": confirmed_count,
        "needs_review": review_count,
        "unmapped": unmapped_count
    }

    try:
        external_mapping_summary = get_mapping_summary()
    except Exception:
        external_mapping_summary = None

    return {
        "dataframe": df,
        "rows": df.to_dict(orient="records"),
        "columns": list(df.columns),
        "detected": detected,
        "unmapped": unmapped,
        "needs_review": needs_review,
        "mapping_details": mapping_details,
        "mapping_summary": mapping_summary,
        "saved_mapping_summary": external_mapping_summary,
        "summary": {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "detected_parameters": len(detected),
            "unmapped_parameters": len(unmapped)
        },
        "time_column": time_column,
        "required_parameters": required_check,
        "condition_comparisons": condition_comparisons,
        "file_name": getattr(
            uploaded_file,
            "name",
            "scanner_data.csv"
        ),
        "data_quality": data_quality,
        "csv_layout": csv_layout
    }


# ============================================================
# CSV DATA FOR AI ANALYSIS
# ============================================================

def get_csv_text_for_ai(df, max_rows=100):

    if df is None or df.empty:
        return "No CSV data available."

    limited_df = df.head(max_rows)

    return limited_df.to_csv(index=False)


# ============================================================
# BUILD AI SUMMARY
# ============================================================

def build_csv_ai_summary(analysis_result):

    if not analysis_result:
        return "No CSV analysis available."

    lines = []

    lines.append("SCANNER CSV ANALYSIS")
    lines.append("====================")

    lines.append(
        f"CSV Layout: {analysis_result.get('csv_layout', 'Unknown')}"
    )

    quality = analysis_result.get("data_quality", {})

    lines.append(
        f"Rows: {quality.get('total_rows', 0)}"
    )

    lines.append(
        f"Columns: {quality.get('total_columns', 0)}"
    )

    lines.append(
        f"Missing Cells: {quality.get('missing_cells', 0)}"
    )

    lines.append(
        f"Duplicate Rows: {quality.get('duplicate_rows', 0)}"
    )

    lines.append("")
    lines.append("PARAMETER MAPPING")
    lines.append("-----------------")

    mapping_summary = analysis_result.get(
        "mapping_summary",
        {}
    )

    lines.append(
        f"Confirmed: {mapping_summary.get('confirmed', 0)}"
    )

    lines.append(
        f"Needs Review: {mapping_summary.get('needs_review', 0)}"
    )

    lines.append(
        f"Unmapped: {mapping_summary.get('unmapped', 0)}"
    )

    lines.append("")
    lines.append("CONFIRMED PARAMETERS")
    lines.append("--------------------")

    detected = analysis_result.get("detected", {})

    if not detected:
        lines.append("No confirmed parameters detected.")

    for column_name, item in detected.items():

        summary = item.get("summary", {})

        lines.append(
            f"\nParameter: {item.get('standard_name', column_name)}"
        )

        lines.append(
            f"Original Scanner Name: {column_name}"
        )

        lines.append(
            f"Minimum: {summary.get('min')}"
        )

        lines.append(
            f"Maximum: {summary.get('max')}"
        )

        lines.append(
            f"Average: {summary.get('average')}"
        )

        lines.append(
            f"First Value: {summary.get('first')}"
        )

        lines.append(
            f"Last Value: {summary.get('last')}"
        )

        lines.append(
            f"Trend: {summary.get('trend')}"
        )

    lines.append("")
    lines.append("PARAMETERS NEEDING REVIEW")
    lines.append("-------------------------")

    needs_review = analysis_result.get("needs_review", [])

    if not needs_review:
        lines.append("None.")

    for item in needs_review:
        lines.append(
            f"{item.get('raw_name')} -> "
            f"{item.get('standard_name')} "
            f"(Status: {item.get('status')})"
        )

    lines.append("")
    lines.append("UNMAPPED PARAMETERS")
    lines.append("-------------------")

    unmapped = analysis_result.get("unmapped", [])

    if not unmapped:
        lines.append("None.")

    for item in unmapped:
        lines.append(str(item))

    lines.append("")
    lines.append("IMPORTANT DIAGNOSTIC RULES")
    lines.append("--------------------------")
    lines.append(
        "Do not assume a missing parameter is zero."
    )
    lines.append(
        "Do not treat an unconfirmed parameter mapping as verified data."
    )
    lines.append(
        "Do not diagnose a failed component using a DTC or one live-data "
        "reading alone."
    )
    lines.append(
        "Consider vehicle details, operating conditions, DTCs, freeze-frame "
        "data and physical test results before suggesting a root cause."
    )

    return "\n".join(lines)
