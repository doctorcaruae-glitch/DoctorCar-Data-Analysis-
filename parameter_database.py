
"""
Doctor Car - Automotive Diagnostic Parameter Database

Purpose:
1. THINKDIAG CSV parameter identification
2. Parameter name and alias mapping
3. Units and module classification
4. Generic diagnostic parameter requirements

Note:
This is a generic database. Exact vehicle-specific parameter
availability must be confirmed using the vehicle and scanner.
"""

import re


# --------------------------------------------------
# 1. AUTOMOTIVE PARAMETER DATABASE
# --------------------------------------------------

PARAMETERS = {

    # ENGINE MODULE

    "engine_rpm": {
        "label": "Engine RPM",
        "unit": "rpm",
        "module": "Engine",
        "aliases": [
            "engine rpm",
            "rpm",
            "engine speed",
            "motor speed"
        ]
    },

    "coolant_temp": {
        "label": "Engine Coolant Temperature",
        "unit": "°C",
        "module": "Engine",
        "aliases": [
            "coolant temp",
            "engine coolant temperature",
            "ect",
            "coolant temperature"
        ]
    },

    "engine_load": {
        "label": "Calculated Engine Load",
        "unit": "%",
        "module": "Engine",
        "aliases": [
            "engine load",
            "calculated load",
            "calculated engine load"
        ]
    },

    "throttle_position": {
        "label": "Throttle Position",
        "unit": "%",
        "module": "Engine",
        "aliases": [
            "throttle position",
            "throttle angle",
            "absolute throttle position"
        ]
    },

    "accelerator_position": {
        "label": "Accelerator Pedal Position",
        "unit": "%",
        "module": "Engine",
        "aliases": [
            "accelerator position",
            "accelerator pedal position",
            "app sensor"
        ]
    },

    "vehicle_speed": {
        "label": "Vehicle Speed",
        "unit": "km/h",
        "module": "Engine",
        "aliases": [
            "vehicle speed",
            "car speed",
            "speed km/h"
        ]
    },

    "maf": {
        "label": "Mass Air Flow",
        "unit": "g/s",
        "module": "Engine",
        "aliases": [
            "maf",
            "mass air flow",
            "mass airflow"
        ]
    },

    "map": {
        "label": "Manifold Absolute Pressure",
        "unit": "kPa",
        "module": "Engine",
        "aliases": [
            "map",
            "manifold absolute pressure",
            "intake manifold pressure"
        ]
    },

    "intake_air_temp": {
        "label": "Intake Air Temperature",
        "unit": "°C",
        "module": "Engine",
        "aliases": [
            "intake air temp",
            "iat",
            "intake temperature"
        ]
    },

    "short_fuel_trim": {
        "label": "Short Term Fuel Trim",
        "unit": "%",
        "module": "Engine",
        "aliases": [
            "short fuel trim",
            "short term fuel trim",
            "stft"
        ]
    },

    "long_fuel_trim": {
        "label": "Long Term Fuel Trim",
        "unit": "%",
        "module": "Engine",
        "aliases": [
            "long fuel trim",
            "long term fuel trim",
            "ltft"
        ]
    },

    "ignition_timing": {
        "label": "Ignition Timing Advance",
        "unit": "degree",
        "module": "Engine",
        "aliases": [
            "ignition timing",
            "timing advance"
        ]
    },

    "fuel_pressure": {
        "label": "Fuel Pressure",
        "unit": "kPa",
        "module": "Engine",
        "aliases": [
            "fuel pressure",
            "rail pressure",
            "fuel rail pressure"
        ]
    },

    "o2_sensor": {
        "label": "Oxygen Sensor",
        "unit": "V",
        "module": "Engine",
        "aliases": [
            "o2 sensor",
            "oxygen sensor",
            "lambda sensor"
        ]
    },

    "misfire": {
        "label": "Misfire Count",
        "unit": "count",
        "module": "Engine",
        "aliases": [
            "misfire",
            "misfire count",
            "cylinder misfire"
        ]
    },

    "boost_pressure": {
        "label": "Boost Pressure",
        "unit": "kPa",
        "module": "Engine",
        "aliases": [
            "boost pressure",
            "turbo boost",
            "charge pressure"
        ]
    },

    "egr": {
        "label": "EGR Position",
        "unit": "%",
        "module": "Engine",
        "aliases": [
            "egr",
            "egr position",
            "egr command"
        ]
    },

    "dpf_pressure": {
        "label": "DPF Differential Pressure",
        "unit": "kPa",
        "module": "Engine",
        "aliases": [
            "dpf pressure",
            "differential pressure",
            "dpf differential pressure"
        ]
    },

    "dpf_soot": {
        "label": "DPF Soot Load",
        "unit": "%",
        "module": "Engine",
        "aliases": [
            "dpf soot",
            "soot load",
            "particulate filter soot"
        ]
    },


    # TRANSMISSION MODULE

    "transmission_temp": {
        "label": "Transmission Fluid Temperature",
        "unit": "°C",
        "module": "Transmission",
        "aliases": [
            "transmission temp",
            "transmission fluid temperature",
            "atf temp",
            "gearbox temperature"
        ]
    },

    "current_gear": {
        "label": "Current Gear",
        "unit": "",
        "module": "Transmission",
        "aliases": [
            "current gear",
            "actual gear",
            "selected gear"
        ]
    },

    "input_speed": {
        "label": "Transmission Input Speed",
        "unit": "rpm",
        "module": "Transmission",
        "aliases": [
            "input speed",
            "turbine speed",
            "input shaft speed"
        ]
    },

    "output_speed": {
        "label": "Transmission Output Speed",
        "unit": "rpm",
        "module": "Transmission",
        "aliases": [
            "output speed",
            "output shaft speed"
        ]
    },

    "tcc_slip": {
        "label": "Torque Converter Clutch Slip",
        "unit": "rpm",
        "module": "Transmission",
        "aliases": [
            "tcc slip",
            "torque converter slip",
            "lockup slip"
        ]
    },


    # ABS / ESC MODULE

    "wheel_speed": {
        "label": "Wheel Speed",
        "unit": "km/h",
        "module": "ABS/ESC",
        "aliases": [
            "wheel speed",
            "wheel speed sensor"
        ]
    },

    "steering_angle": {
        "label": "Steering Angle",
        "unit": "degree",
        "module": "ABS/ESC",
        "aliases": [
            "steering angle",
            "steering wheel angle"
        ]
    },

    "brake_switch": {
        "label": "Brake Switch Status",
        "unit": "",
        "module": "ABS/ESC",
        "aliases": [
            "brake switch",
            "stop lamp switch",
            "brake pedal switch"
        ]
    },

    "abs_pump": {
        "label": "ABS Pump Status",
        "unit": "",
        "module": "ABS/ESC",
        "aliases": [
            "abs pump",
            "hydraulic pump status"
        ]
    },


    # SRS MODULE

    "srs_status": {
        "label": "SRS / Airbag Status",
        "unit": "",
        "module": "SRS",
        "aliases": [
            "srs status",
            "airbag status",
            "supplemental restraint"
        ]
    },


    # EPS MODULE

    "steering_torque": {
        "label": "Steering Torque",
        "unit": "Nm",
        "module": "EPS",
        "aliases": [
            "steering torque",
            "eps torque"
        ]
    },


    # HVAC MODULE

    "ac_pressure": {
        "label": "A/C Refrigerant Pressure",
        "unit": "kPa",
        "module": "HVAC",
        "aliases": [
            "ac pressure",
            "a/c pressure",
            "refrigerant pressure"
        ]
    },


    # BATTERY / CHARGING MODULE

    "battery_voltage": {
        "label": "System / Battery Voltage",
        "unit": "V",
        "module": "Battery/Charging",
        "aliases": [
            "battery voltage",
            "control module voltage",
            "system voltage",
            "voltage"
        ]
    }

}


# --------------------------------------------------
# 2. MODULE LIST
# --------------------------------------------------

MODULES = [

    "Engine",
    "Transmission",
    "ABS/ESC",
    "SRS",
    "EPS",
    "HVAC",
    "AWD/4WD",
    "ADAS",
    "BCM/Body Electrical",
    "Battery/Charging",
    "Hybrid/EV",
    "TPMS",
    "Other OEM Modules"

]


# --------------------------------------------------
# 3. PARAMETER NAME NORMALIZATION
# --------------------------------------------------

def normalize_text(value):

    value = str(value or "").strip().lower()

    value = value.replace("%", " percent ")

    value = re.sub(r"[_\-\/]+", " ", value)

    value = re.sub(r"[^a-z0-9° ]+", " ", value)

    value = re.sub(r"\s+", " ", value)

    return value.strip()


# --------------------------------------------------
# 4. IDENTIFY PARAMETER
# --------------------------------------------------

def identify_parameter(column_name):

    name = normalize_text(column_name)

    if not name:
        return None

    for key, meta in PARAMETERS.items():

        candidates = [
            key.replace("_", " "),
            meta["label"]
        ] + meta["aliases"]

        for alias in candidates:

            alias_name = normalize_text(alias)

            if name == alias_name:
                return key

            # Avoid matching very short names inside unrelated columns.
            if len(alias_name) >= 5 and alias_name in name:
                return key

    return None


# --------------------------------------------------
# 5. GET PARAMETER INFORMATION
# --------------------------------------------------

def get_parameter_metadata(parameter_key):

    return PARAMETERS.get(parameter_key, {})


# --------------------------------------------------
# 6. GENERIC PARAMETER REQUIREMENTS
# --------------------------------------------------

def default_parameter_requirements(vehicle, complaint, modules):

    complaint_text = str(complaint or "").lower()

    selected_modules = set(modules or ["Engine"])

    # Complaint-based module suggestions.

    if any(word in complaint_text for word in [
        "gear",
        "transmission",
        "shift",
        "jerk",
        "slip"
    ]):
        selected_modules.add("Transmission")

    if any(word in complaint_text for word in [
        "brake",
        "abs",
        "traction",
        "stability",
        "wheel"
    ]):
        selected_modules.add("ABS/ESC")

    if any(word in complaint_text for word in [
        "steering",
        "eps",
        "hard steering"
    ]):
        selected_modules.add("EPS")

    if any(word in complaint_text for word in [
        "battery",
        "charging",
        "alternator",
        "start"
    ]):
        selected_modules.add("Battery/Charging")

    requirements = []

    for key, meta in PARAMETERS.items():

        if meta["module"] not in selected_modules:
            continue

        priority = "Optional"

        if key in [
            "engine_rpm",
            "coolant_temp",
            "battery_voltage"
        ]:
            priority = "Must Have"

        requirements.append({

            "parameter": key,

            "label": meta["label"],

            "unit": meta["unit"],

            "module": meta["module"],

            "priority": priority,

            "note": (
                "Generic suggestion only. "
                "Availability depends on vehicle, ECU and scanner."
            )

        })

    return requirements
