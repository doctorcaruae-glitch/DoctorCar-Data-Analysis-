
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
        "n/a",
        "na",
        "null",
        "none",
        "--",
        "-",
        "not available",
        "unsupported",
        "not supported"
    ]:
        return None

    text = text.replace(",", "")

    match = re.search(
        r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?",
        text
    )

    if not match:
        return None

    try:
        return float(match.group(0))
    except ValueError:
        return None


# --------------------------------------------------
# 2. READ CSV FILE
# --------------------------------------------------

def read_scanner_csv(file_bytes):

    encodings = [
        "utf-8-sig",
        "utf-8",
        "cp1252",
        "latin1"
    ]

    separators = [
        None,
        ",",
        ";",
        "\t"
    ]

    for encoding in encodings:

        for separator in separators:

            try:

                df = pd.read_csv(
                    io.BytesIO(file_bytes),
                    encoding=encoding,
                    sep=separator,
                    engine="python"
                )

                if len(df.columns) > 0:

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
        "time",
        "timestamp",
        "date",
        "record time",
        "sample time"
    ]

    for column in columns:

        name = str(column).lower()

        if any(item in name for item in possible_names):

            return column

    return None


# --------------------------------------------------
# 4. ANALYZE COLUMN-BASED CSV
# --------------------------------------------------

def analyze_column_data(df):

    detected = {}

    unmapped = []

    summary = {}

    time_column = find_time_column(df.columns)

    for column in df.columns:

        parameter_key = identify_parameter(column)

        if parameter_key:

            detected[column] = parameter_key

            metadata = get_parameter_metadata(
                parameter_key
            )

            values = df[column].apply(
                clean_number
            ).dropna()

            summary[parameter_key] = {

                "source_column": column,

                "label": metadata.get(
                    "label",
                    parameter_key
                ),

                "unit": metadata.get(
                    "unit",
                    ""
                ),

                "module": metadata.get(
                    "module",
                    "Unknown"
                ),

                "valid_count": int(
                    len(values)
                ),

                "missing_count": int(
                    len(df) - len(values)
                ),

                "min": (
                    float(values.min())
                    if len(values) else None
                ),

                "max": (
                    float(values.max())
                    if len(values) else None
                ),

                "average": (
                    float(values.mean())
                    if len(values) else None
                ),

                "latest": (
                    float(values.iloc[-1])
                    if len(values) else None
                )

            }

        elif column != time_column:

            unmapped.append(column)

    return {
        "detected": detected,
        "unmapped": unmapped,
        "summary": summary,
        "time_column": time_column
    }


# --------------------------------------------------
# 5. ANALYZE ROW-BASED CSV
# --------------------------------------------------

def analyze_row_data(df):

    if len(df.columns) < 2:

        return {
            "detected": {},
            "unmapped": list(df.columns),
            "summary": {},
            "time_column": None
        }

    name_column = None

    value_column = None

    for column in df.columns:

        name = str(column).lower()

        if any(word in name for word in [
            "parameter",
            "name",
            "pid",
            "item"
        ]):

            name_column = column

        if any(word in name for word in [
            "value",
            "reading",
            "data"
        ]):

            value_column = column

    if name_column is None:
        name_column = df.columns[0]

    if value_column is None:
        value_column = df.columns[1]

    detected = {}

    summary = {}

    for _, row in df.iterrows():

        parameter_name = row.get(
            name_column,
            ""
        )

        parameter_key = identify_parameter(
            parameter_name
        )

        if not parameter_key:
            continue

        value = clean_number(
            row.get(value_column)
        )

        metadata = get_parameter_metadata(
            parameter_key
        )

        detected[str(parameter_name)] = parameter_key

        summary[parameter_key] = {

            "source_column": (
                str(name_column)
                + " -> "
                + str(value_column)
            ),

            "label": metadata.get(
                "label",
                parameter_key
            ),

            "unit": metadata.get(
                "unit",
                ""
            ),

            "module": metadata.get(
                "module",
                "Unknown"
            ),

            "valid_count": (
                1 if value is not None else 0
            ),

            "missing_count": (
                0 if value is not None else 1
            ),

            "min": value,
            "max": value,
            "average": value,
            "latest": value

        }

    unmapped = [
        column
        for column in df.columns
        if column not in [
            name_column,
            value_column
        ]
    ]

    return {
        "detected": detected,
        "unmapped": unmapped,
        "summary": summary,
        "time_column": None
    }


# --------------------------------------------------
# 6. MAIN CSV ANALYZER
# --------------------------------------------------

def analyze_csv(uploaded_file):

    if hasattr(uploaded_file, "getvalue"):

        file_bytes = uploaded_file.getvalue()

    else:

        file_bytes = uploaded_file.read()

    df = read_scanner_csv(file_bytes)

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    column_result = analyze_column_data(df)

    # First try column-based structure.

    result = column_result

    # If no parameters were identified,
    # try row-based structure.

    if not result["summary"]:

        row_result = analyze_row_data(df)

        if row_result["summary"]:

            result = row_result

    return {

        "dataframe": df,

        "rows": int(len(df)),

        "columns": list(df.columns),

        "detected": result["detected"],

        "unmapped": result["unmapped"],

        "summary": result["summary"],

        "time_column": result["time_column"],

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
            )

        }

    }


# --------------------------------------------------
# 7. CONVERT CSV DATA FOR AI
# --------------------------------------------------

def get_csv_text_for_ai(
    result,
    max_rows=250
):

    df = result.get("dataframe")

    if df is None:

        return "No CSV data available."

    safe_df = df.head(max_rows).copy()

    return safe_df.to_csv(
        index=False
    )


# --------------------------------------------------
# 8. BUILD MULTI-MODULE AI SUMMARY
# --------------------------------------------------

def build_csv_ai_summary(module_results):

    output = []

    for module, result in (
        module_results or {}
    ).items():

        output.append(
            "\nMODULE: " + str(module)
        )

        output.append(
            "File: "
            + str(
                result.get(
                    "file_name",
                    "Unknown"
                )
            )
        )

        output.append(
            "Rows: "
            + str(
                result.get(
                    "rows",
                    0
                )
            )
        )

        output.append(
            "Recognized parameters: "
            + str(
                len(
                    result.get(
                        "summary",
                        {}
                    )
                )
            )
        )

        for key, item in result.get(
            "summary",
            {}
        ).items():

            output.append(

                "- "
                + str(
                    item.get(
                        "label",
                        key
                    )
                )
                + ": Latest="
                + str(item.get("latest"))
                + " "
                + str(item.get("unit", ""))
                + "; Minimum="
                + str(item.get("min"))
                + "; Maximum="
                + str(item.get("max"))
                + "; Valid readings="
                + str(item.get("valid_count"))
                + "; Missing readings="
                + str(item.get("missing_count"))

            )

        if result.get("unmapped"):

            output.append(
                "Unmapped columns: "
                + ", ".join(
                    map(
                        str,
                        result["unmapped"][:30]
                    )
                )
            )

    return "\n".join(output)
