import pandas as pd
import numpy as np
import re
from io import BytesIO


PARAMETER_ALIASES = {
    "engine_rpm": [
        "engine rpm", "rpm", "engine speed", "motor speed"
    ],
    "coolant_temp": [
        "coolant temperature", "engine coolant temp",
        "ect", "coolant temp"
    ],
    "engine_load": [
        "engine load", "calculated load", "load value"
    ],
    "throttle_position": [
        "throttle position", "absolute throttle position",
        "throttle angle", "tps"
    ],
    "accelerator_position": [
        "accelerator pedal position", "app sensor",
        "accelerator position"
    ],
    "vehicle_speed": [
        "vehicle speed", "speed"
    ],
    "maf": [
        "maf", "mass air flow", "mass airflow"
    ],
    "map": [
        "map", "manifold absolute pressure", "intake manifold pressure"
    ],
    "intake_air_temp": [
        "intake air temperature", "iat"
    ],
    "fuel_pressure": [
        "fuel pressure", "fuel rail pressure",
        "rail pressure"
    ],
    "short_fuel_trim": [
        "short term fuel trim", "stft"
    ],
    "long_fuel_trim": [
        "long term fuel trim", "ltft"
    ],
    "o2_sensor": [
        "oxygen sensor", "o2 sensor", "lambda"
    ],
    "ignition_timing": [
        "ignition timing", "spark advance"
    ],
    "misfire": [
        "misfire", "cylinder misfire"
    ],
    "boost_pressure": [
        "boost pressure", "turbo pressure",
        "desired boost", "actual boost"
    ],
    "egr": [
        "egr", "exhaust gas recirculation"
    ],
    "dpf_pressure": [
        "dpf differential pressure", "dpf pressure"
    ],
    "dpf_soot": [
        "dpf soot", "soot mass", "particulate filter soot"
    ],
    "transmission_temp": [
        "transmission temperature", "trans fluid temp",
        "gearbox temperature"
    ],
    "current_gear": [
        "current gear", "actual gear"
    ],
    "commanded_gear": [
        "commanded gear", "desired gear", "target gear"
    ],
    "input_speed": [
        "input shaft speed", "turbine speed"
    ],
    "output_speed": [
        "output shaft speed"
    ],
    "tcc_slip": [
        "torque converter slip", "tcc slip"
    ],
    "battery_voltage": [
        "control module voltage", "battery voltage",
        "ecu voltage", "module voltage"
    ],
    "wheel_speed": [
        "wheel speed", "abs wheel speed"
    ],
    "steering_angle": [
        "steering angle", "steering wheel angle"
    ]
}


def normalize_name(name):
    name = str(name).strip().lower()
    name = re.sub(r"[^a-z0-9]+", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def identify_parameter(column_name):
    normalized = normalize_name(column_name)

    for standard_name, aliases in PARAMETER_ALIASES.items():
        for alias in aliases:
            if normalize_name(alias) in normalized:
                return standard_name

    return None


def read_scanner_csv(uploaded_file):
    raw = uploaded_file.getvalue()

    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin1"]
    separators = [None, ",", ";", "\t"]

    last_error = None

    for encoding in encodings:
        for separator in separators:
            try:
                df = pd.read_csv(
                    BytesIO(raw),
                    encoding=encoding,
                    sep=separator,
                    engine="python",
                    on_bad_lines="warn"
                )

                if not df.empty and len(df.columns) >= 1:
                    df.columns = [
                        str(c).strip() for c in df.columns
                    ]
                    return df

            except Exception as error:
                last_error = error

    raise ValueError(
        f"Unable to read CSV file: {last_error}"
    )


def analyze_csv(uploaded_file):
    df = read_scanner_csv(uploaded_file)

    detected = {}
    unmapped = []

    for column in df.columns:
        standard = identify_parameter(column)

        if standard:
            detected.setdefault(standard, []).append(column)
        else:
            unmapped.append(column)

    parameter_summary = []

    for standard, columns in detected.items():
        for column in columns:
            series = df[column]

            numeric = pd.to_numeric(
                series.astype(str).str.replace(",", ""),
                errors="coerce"
            )

            valid = numeric.dropna()

            parameter_summary.append({
                "parameter": standard,
                "source_column": column,
                "unit_or_format": "",
                "valid_readings": int(valid.count()),
                "missing_readings": int(numeric.isna().sum()),
                "minimum": (
                    float(valid.min()) if not valid.empty else None
                ),
                "maximum": (
                    float(valid.max()) if not valid.empty else None
                ),
                "average": (
                    float(valid.mean()) if not valid.empty else None
                ),
                "latest": (
                    float(valid.iloc[-1]) if not valid.empty else None
                )
            })

    return {
        "dataframe": df,
        "rows": len(df),
        "columns": list(df.columns),
        "detected": detected,
        "unmapped": unmapped,
        "summary": parameter_summary
    }


def get_csv_text_for_ai(result, max_rows=300):
    df = result["dataframe"].copy()

    # Limit data sent to AI to control token usage.
    if len(df) > max_rows:
        step = max(1, len(df) // max_rows)
        df = df.iloc[::step].head(max_rows)

    return df.to_csv(index=False)
