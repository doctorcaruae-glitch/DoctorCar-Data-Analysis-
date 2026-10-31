
import io
import re
import pandas as pd

from parameter_database import (
    identify_parameter,
    get_parameter_metadata
)


# --------------------------------------------------
# 1. CLEAN AND CONVERT NUMERIC VALUES
# --------------------------------------------------

def clean_number(value):

    if pd.isna(value):
        return None

    text = str(value).strip()

    if not text:
        return None

    if text.lower() in [
        "n/a", "na", "null", "none", "--", "-",
        "not available", "unsupported", "not supported"
    ]:
        return None

    # Remove thousands separators.
    text = text.replace(",", "")

    match = re.search(
        r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?",
        text
    )

    if not match:
        return None

    try:
        number = float(match.group(0))
        return number if pd.notna(number) else None
    except (ValueError, TypeError):
        return None


# --------------------------------------------------
# 2. READ CSV FILE
# --------------------------------------------------

def read_scanner_csv(file_bytes):

    if not file_bytes:
        raise ValueError("The uploaded CSV file is empty.")

    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin1"]
    separators = [None, ",", ";", "\t"]

    for encoding in encodings:

        for separator in separators:

            try:
                df = pd.read_csv(
                    io.BytesIO(file_bytes),
                    encoding=encoding,
                    sep=separator,
                    engine="python"
                )

                if len(df.columns) > 1 and len(df) >= 0:
                    return df

            except Exception:
                continue

    raise ValueError(
        "Unable to read CSV. Please export the scanner CSV again."
    )


# --------------------------------------------------
# 3. IDENTIFY TIME COLUMN
# --------------------------------------------------

def find_time_column(columns):

    possible_names = [
        "timestamp",
        "record time",
        "sample time",
        "recorded time",
        "date time",
        "datetime",
        "time",
        "date"
    ]

    for column in columns:

        name = str(column).strip().lower()

        if any(
            name == item or item in name
            for item in possible_names
        ):
            return column

    return None


# --------------------------------------------------
# 4. NUMERIC SERIES ANALYSIS
# --------------------------------------------------

def calculate_trend(values):

    values = pd.Series(values).dropna()

    if len(values) < 3:
        return "Insufficient readings"

    first = float(values.iloc[0])
    latest = float(values.iloc[-1])
    difference = latest - first

    scale = max(abs(first), abs(latest), 1)

    if abs(difference) <= scale * 0.01:
        return "Stable"

    if difference > 0:
        return "Increasing"

    return "Decreasing"


def summarize_values(values, source_column, parameter_key):

    metadata = get_parameter_metadata(parameter_key)

    values = pd.Series(values).dropna().astype(float)

    if len(values) == 0:
        numeric_values = []
    else:
        numeric_values = values.tolist()

    first_value = (
        float(values.iloc[0])
        if len(values) else None
    )

    latest_value = (
        float(values.iloc[-1])
        if len(values) else None
    )

    change = (
        latest_value - first_value
        if first_value is not None and latest_value is not None
        else None
    )

    return {
        "source_column": str(source_column),
        "label": metadata.get("label", parameter_key),
        "unit": metadata.get("unit", ""),
        "module": metadata.get("module", "Unknown"),

        "valid_count": int(len(values)),
        "missing_count": int(max(0, len(values) - len(numeric_values))),

        "min": float(values.min()) if len(values) else None,
        "max": float(values.max()) if len(values) else None,
        "average": float(values.mean()) if len(values) else None,
        "median": float(values.median()) if len(values) else None,

        "first": first_value,
        "latest": latest_value,
        "change": change,

        "trend": calculate_trend(values),

        "readings": numeric_values
    }


# --------------------------------------------------
# 5. ANALYZE COLUMN-BASED CSV
# --------------------------------------------------

def analyze_column_data(df):

    detected = {}
    unmapped = []
    summary = {}

    time_column = find_time_column(df.columns)

    for column in df.columns:

        parameter_key = identify_parameter(column)

        if parameter_key:

            detected[str(column)] = parameter_key

            values = df[column].apply(clean_number)

            item = summarize_values(
                values,
                column,
                parameter_key
            )

            item["missing_count"] = int(
                values.isna().sum()
            )

            # Preserve all source columns if duplicate
            # columns map to the same parameter.
            if parameter_key in summary:

                previous = summary[parameter_key]

                combined = (
                    previous.get("readings", [])
                    + item.get("readings", [])
                )

                summary[parameter_key] = summarize_values(
                    combined,
                    str(previous.get("source_column"))
                    + " / "
                    + str(column),
                    parameter_key
                )

            else:
                summary[parameter_key] = item

        elif column != time_column:

            unmapped.append(str(column))

    return {
        "detected": detected,
        "unmapped": unmapped,
        "summary": summary,
        "time_column": time_column
    }


# --------------------------------------------------
# 6. ANALYZE ROW-BASED CSV
# --------------------------------------------------

def analyze_row_data(df):

    if len(df.columns) < 2:

        return {
            "detected": {},
            "unmapped": list(map(str, df.columns)),
            "summary": {},
            "time_column": None
        }

    name_column = None
    value_column = None

    for column in df.columns:

        name = str(column).strip().lower()

        if any(word in name for word in [
            "parameter", "name", "pid", "item"
        ]):
            name_column = column

        if any(word in name for word in [
            "value", "reading", "data"
        ]):
            value_column = column

    if name_column is None:
        name_column = df.columns[0]

    if value_column is None:
        value_column = df.columns[1]

    detected = {}
    unmapped_parameters = []
    grouped_values = {}

    for _, row in df.iterrows():

        parameter_name = row.get(name_column, "")

        parameter_key = identify_parameter(parameter_name)

        if not parameter_key:

            if str(parameter_name).strip():
                unmapped_parameters.append(
                    str(parameter_name)
                )

            continue

        value = clean_number(row.get(value_column))

        detected[str(parameter_name)] = parameter_key

        grouped_values.setdefault(
            parameter_key,
            []
        ).append(value)

    summary = {}

    for parameter_key, values in grouped_values.items():

        valid_values = [
            value for value in values
            if value is not None
        ]

        item = summarize_values(
            valid_values,
            str(name_column) + " -> " + str(value_column),
            parameter_key
        )

        item["missing_count"] = int(
            len(values) - len(valid_values)
        )

        summary[parameter_key] = item

    unmapped = list(dict.fromkeys(unmapped_parameters))

    return {
        "detected": detected,
        "unmapped": unmapped,
        "summary": summary,
        "time_column": find_time_column(df.columns)
    }


# --------------------------------------------------
# 7. REQUIRED PARAMETER CHECK
# --------------------------------------------------

def check_required_parameters(summary, required_parameters=None):

    if not required_parameters:
        return {
            "required": [],
            "available": [],
            "missing": []
        }

    required = []

    for item in required_parameters:

        if isinstance(item, str):
            required.append(item)

        elif isinstance(item, dict):
            key = item.get("key") or item.get("parameter")
            if key:
                required.append(str(key))

    required = list(dict.fromkeys(required))

    available = [
        key for key in required
        if key in summary
    ]

    missing = [
        key for key in required
        if key not in summary
    ]

    return {
        "required": required,
        "available": available,
        "missing": missing
    }


# --------------------------------------------------
# 8. CONDITION COMPARISON
# --------------------------------------------------

def compare_conditions(df, detected, condition_column):

    if (
        condition_column not in df.columns
        or not detected
    ):
        return {}

    comparisons = {}

    condition_values = (
        df[condition_column]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    if len(condition_values) < 2:
        return {}

    for source_column, parameter_key in detected.items():

        if source_column not in df.columns:
            continue

        groups = {}

        for condition in condition_values:

            mask = (
                df[condition_column].astype(str) == condition
            )

            values = (
                df.loc[mask, source_column]
                .apply(clean_number)
                .dropna()
            )

            if len(values):

                groups[condition] = {
                    "count": int(len(values)),
                    "average": float(values.mean()),
                    "minimum": float(values.min()),
                    "maximum": float(values.max()),
                    "latest": float(values.iloc[-1])
                }

        if len(groups) >= 2:

            comparisons[parameter_key] = {
                "source_column": str(source_column),
                "condition_column": str(condition_column),
                "groups": groups
            }

    return comparisons


# --------------------------------------------------
# 9. MAIN CSV ANALYZER
# --------------------------------------------------

def analyze_csv(
    uploaded_file,
    required_parameters=None,
    condition_column=None
):

    if hasattr(uploaded_file, "getvalue"):
        file_bytes = uploaded_file.getvalue()
    else:
        file_bytes = uploaded_file.read()

    df = read_scanner_csv(file_bytes)

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    if df.empty:
        raise ValueError("The CSV file contains no data rows.")

    column_result = analyze_column_data(df)

    result = column_result

    # Try row-based format if column-based detection fails.
    if not result["summary"]:

        row_result = analyze_row_data(df)

        if row_result["summary"]:
            result = row_result

    required_check = check_required_parameters(
        result["summary"],
        required_parameters
    )

    comparisons = {}

    if condition_column:
        comparisons = compare_conditions(
            df,
            result["detected"],
            condition_column
        )

    return {
        "dataframe": df,

        "rows": int(len(df)),
        "columns": list(df.columns),

        "detected": result["detected"],
        "unmapped": result["unmapped"],
        "summary": result["summary"],

        "time_column": result["time_column"],

        "required_parameters": required_check,

        "condition_comparisons": comparisons,

        "file_name": getattr(
            uploaded_file,
            "name",
            "uploaded.csv"
        ),

        "data_quality": {
            "row_count": int(len(df)),

            "recognized_parameter_count": len(
                result["summary"]
            ),

            "unmapped_columns": result["unmapped"],

            "time_column": (
                str(result["time_column"])
                if result["time_column"]
                else None
            ),

            "required_parameter_count": len(
                required_check["required"]
            ),

            "missing_required_parameter_count": len(
                required_check["missing"]
            )
        }
    }


# --------------------------------------------------
# 10. CONVERT CSV DATA FOR AI
# --------------------------------------------------

def get_csv_text_for_ai(result, max_rows=250):

    df = result.get("dataframe")

    if df is None:
        return "No CSV data available."

    safe_df = df.head(max_rows).copy()

    return safe_df.to_csv(index=False)


# --------------------------------------------------
# 11. BUILD MULTI-MODULE AI SUMMARY
# --------------------------------------------------

def build_csv_ai_summary(module_results):

    output = []

    for module, result in (module_results or {}).items():

        output.append("\nMODULE: " + str(module))

        output.append(
            "File: "
            + str(result.get("file_name", "Unknown"))
        )

        output.append(
            "Rows: "
            + str(result.get("rows", 0))
        )

        output.append(
            "Recognized parameters: "
            + str(len(result.get("summary", {})))
        )

        for key, item in result.get("summary", {}).items():

            output.append(
                "- "
                + str(item.get("label", key))
                + ": Latest="
                + str(item.get("latest"))
                + " "
                + str(item.get("unit", ""))
                + "; First="
                + str(item.get("first"))
                + "; Minimum="
                + str(item.get("min"))
                + "; Maximum="
                + str(item.get("max"))
                + "; Average="
                + str(item.get("average"))
                + "; Trend="
                + str(item.get("trend"))
                + "; Change="
                + str(item.get("change"))
                + "; Valid readings="
                + str(item.get("valid_count"))
                + "; Missing readings="
                + str(item.get("missing_count"))
            )

        required = result.get("required_parameters", {})

        if required.get("missing"):

            output.append(
                "Missing required parameters: "
                + ", ".join(required["missing"])
            )

        if result.get("condition_comparisons"):

            output.append("CONDITION COMPARISONS:")

            for key, comparison in result[
                "condition_comparisons"
            ].items():

                output.append(
                    str(key)
                    + ": "
                    + str(comparison.get("groups"))
                )

        if result.get("unmapped"):

            output.append(
                "Unmapped columns/parameters: "
                + ", ".join(
                    map(str, result["unmapped"][:30])
                )
            )

    return "\n".join(output)
