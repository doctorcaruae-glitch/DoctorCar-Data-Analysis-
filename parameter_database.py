
"""
Doctor Car - Advanced Automotive Diagnostic Parameter Database

Includes:
- Scanner parameter identification
- Parameter aliases and module classification
- Complaint-based diagnostic profiles
- Fuel starvation vs fuel pump diagnostic support
- Required live-data recommendations
- Physical confirmation test recommendations
- Backward-compatible public functions

IMPORTANT:
Generic diagnostic guidance only.
Vehicle-specific OEM specifications and procedures must be verified.
Missing or unsupported data must never be treated as zero or normal.
"""

import re


# =========================================================
# 1. AUTOMOTIVE PARAMETER DATABASE
# =========================================================

PARAMETERS = {

    # ---------------- ENGINE ----------------

    "engine_rpm": {
        "label": "Engine RPM", "unit": "rpm", "module": "Engine",
        "aliases": ["engine rpm", "rpm", "engine speed", "motor speed"]
    },
    "coolant_temp": {
        "label": "Engine Coolant Temperature", "unit": "°C", "module": "Engine",
        "aliases": ["coolant temp", "engine coolant temperature", "ect", "coolant temperature"]
    },
    "engine_load": {
        "label": "Calculated Engine Load", "unit": "%", "module": "Engine",
        "aliases": ["engine load", "calculated load", "calculated engine load"]
    },
    "throttle_position": {
        "label": "Throttle Position", "unit": "%", "module": "Engine",
        "aliases": ["throttle position", "throttle angle", "absolute throttle position"]
    },
    "accelerator_position": {
        "label": "Accelerator Pedal Position", "unit": "%", "module": "Engine",
        "aliases": ["accelerator position", "accelerator pedal position", "app sensor"]
    },
    "vehicle_speed": {
        "label": "Vehicle Speed", "unit": "km/h", "module": "Engine",
        "aliases": ["vehicle speed", "car speed", "speed km/h"]
    },
    "maf": {
        "label": "Mass Air Flow", "unit": "g/s", "module": "Engine",
        "aliases": ["maf", "mass air flow", "mass airflow"]
    },
    "map": {
        "label": "Manifold Absolute Pressure", "unit": "kPa", "module": "Engine",
        "aliases": ["map sensor", "manifold absolute pressure", "intake manifold pressure"]
    },
    "intake_air_temp": {
        "label": "Intake Air Temperature", "unit": "°C", "module": "Engine",
        "aliases": ["intake air temp", "iat", "intake temperature"]
    },
    "short_fuel_trim": {
        "label": "Short Term Fuel Trim", "unit": "%", "module": "Engine",
        "aliases": ["short fuel trim", "short term fuel trim", "stft"]
    },
    "long_fuel_trim": {
        "label": "Long Term Fuel Trim", "unit": "%", "module": "Engine",
        "aliases": ["long fuel trim", "long term fuel trim", "ltft"]
    },
    "ignition_timing": {
        "label": "Ignition Timing Advance", "unit": "degree", "module": "Engine",
        "aliases": ["ignition timing", "timing advance"]
    },
    "fuel_pressure": {
        "label": "Fuel Pressure", "unit": "kPa", "module": "Engine",
        "aliases": ["fuel pressure", "rail pressure", "fuel rail pressure"]
    },
    "fuel_low_pressure": {
        "label": "Low-Side Fuel Pressure", "unit": "kPa", "module": "Engine",
        "aliases": ["low fuel pressure", "low side fuel pressure", "low pressure fuel",
                    "fuel supply pressure", "feed pressure"]
    },
    "fuel_high_pressure": {
        "label": "High-Side Fuel Pressure", "unit": "kPa", "module": "Engine",
        "aliases": ["high fuel pressure", "high side fuel pressure",
                    "high pressure fuel", "high pressure pump pressure"]
    },
    "fuel_rail_pressure_actual": {
        "label": "Actual Fuel Rail Pressure", "unit": "kPa", "module": "Engine",
        "aliases": ["actual fuel rail pressure", "fuel rail pressure actual",
                    "actual rail pressure", "rail pressure actual"]
    },
    "fuel_rail_pressure_commanded": {
        "label": "Commanded Fuel Rail Pressure", "unit": "kPa", "module": "Engine",
        "aliases": ["commanded fuel rail pressure", "desired fuel rail pressure",
                    "target rail pressure", "fuel rail pressure desired",
                    "rail pressure commanded"]
    },
    "fuel_pump_command": {
        "label": "Fuel Pump Command", "unit": "%", "module": "Engine",
        "aliases": ["fuel pump command", "fuel pump duty cycle",
                    "fuel pump control", "fuel pump activation"]
    },
    "fuel_pump_current": {
        "label": "Fuel Pump Current", "unit": "A", "module": "Engine",
        "aliases": ["fuel pump current", "fuel pump amperage",
                    "fuel pump amp draw"]
    },
    "fuel_level": {
        "label": "Fuel Level", "unit": "%", "module": "Engine",
        "aliases": ["fuel level", "fuel tank level", "fuel gauge level",
                    "fuel level sensor", "fuel quantity"]
    },
    "fuel_tank_pressure": {
        "label": "Fuel Tank Pressure", "unit": "kPa", "module": "Engine",
        "aliases": ["fuel tank pressure", "tank pressure",
                    "fuel tank vacuum", "tank vacuum pressure"]
    },
    "fuel_tank_vacuum": {
        "label": "Fuel Tank Vacuum", "unit": "kPa", "module": "Engine",
        "aliases": ["fuel tank vacuum", "tank vacuum"]
    },
    "evap_purge_command": {
        "label": "EVAP Purge Command", "unit": "%", "module": "Engine",
        "aliases": ["evap purge command", "purge valve command",
                    "canister purge duty cycle"]
    },
    "evap_vent_status": {
        "label": "EVAP Vent Valve Status", "unit": "", "module": "Engine",
        "aliases": ["evap vent status", "vent valve status",
                    "canister vent valve", "fuel tank vent valve"]
    },
    "fuel_system_status": {
        "label": "Fuel System Status", "unit": "", "module": "Engine",
        "aliases": ["fuel system status", "fuel system 1 status"]
    },
    "o2_sensor": {
        "label": "Oxygen Sensor", "unit": "V", "module": "Engine",
        "aliases": ["oxygen sensor", "lambda sensor"]
    },
    "o2_upstream": {
        "label": "Upstream Oxygen / Air Fuel Sensor", "unit": "",
        "module": "Engine",
        "aliases": ["upstream o2", "o2 sensor upstream", "bank 1 sensor 1",
                    "b1s1", "air fuel ratio sensor", "afr sensor"]
    },
    "o2_downstream": {
        "label": "Downstream Oxygen Sensor", "unit": "V", "module": "Engine",
        "aliases": ["downstream o2", "o2 sensor downstream",
                    "bank 1 sensor 2", "b1s2"]
    },
    "misfire": {
        "label": "Engine Misfire Count", "unit": "count", "module": "Engine",
        "aliases": ["misfire", "misfire count", "total misfire"]
    },

    # Cylinder-specific misfire counters
    **{
        f"misfire_cylinder_{i}": {
            "label": f"Cylinder {i} Misfire Count",
            "unit": "count",
            "module": "Engine",
            "aliases": [
                f"cylinder {i} misfire",
                f"cyl {i} misfire",
                f"misfire cyl {i}"
            ]
        }
        for i in range(1, 9)
    },

    "boost_pressure": {
        "label": "Boost Pressure", "unit": "kPa", "module": "Engine",
        "aliases": ["boost pressure", "turbo boost", "charge pressure"]
    },
    "egr": {
        "label": "EGR Position", "unit": "%", "module": "Engine",
        "aliases": ["egr position", "egr command"]
    },
    "dpf_pressure": {
        "label": "DPF Differential Pressure", "unit": "kPa", "module": "Engine",
        "aliases": ["dpf pressure", "dpf differential pressure",
                    "differential pressure sensor"]
    },
    "dpf_soot": {
        "label": "DPF Soot Load", "unit": "%", "module": "Engine",
        "aliases": ["dpf soot", "soot load", "particulate filter soot"]
    },
    "catalyst_temp": {
        "label": "Catalyst Temperature", "unit": "°C", "module": "Engine",
        "aliases": ["catalyst temperature", "catalytic converter temperature",
                    "cat temperature"]
    },
    "catalyst_monitor": {
        "label": "Catalyst Monitor Status", "unit": "", "module": "Engine",
        "aliases": ["catalyst monitor", "catalyst readiness", "cat monitor status"]
    },
    "commanded_equivalence_ratio": {
        "label": "Commanded Equivalence Ratio", "unit": "", "module": "Engine",
        "aliases": ["commanded equivalence ratio", "commanded lambda"]
    },

    # ---------------- COOLING SYSTEM ----------------

    "cooling_fan_command": {
        "label": "Cooling Fan Command", "unit": "%", "module": "Engine",
        "aliases": ["cooling fan command", "fan command", "cooling fan duty cycle"]
    },
    "cooling_fan_status": {
        "label": "Cooling Fan Status", "unit": "", "module": "Engine",
        "aliases": ["cooling fan status", "fan status", "radiator fan status"]
    },
    "cooling_fan_speed": {
        "label": "Cooling Fan Speed", "unit": "rpm", "module": "Engine",
        "aliases": ["cooling fan speed", "radiator fan speed"]
    },
    "thermostat_status": {
        "label": "Thermostat Status", "unit": "", "module": "Engine",
        "aliases": ["thermostat status", "thermostat monitor"]
    },
    "coolant_level": {
        "label": "Coolant Level", "unit": "", "module": "Engine",
        "aliases": ["coolant level", "coolant reservoir level"]
    },
    "coolant_pump_command": {
        "label": "Coolant Pump Command", "unit": "%", "module": "Engine",
        "aliases": ["coolant pump command", "water pump command", "electric water pump"]
    },
    "radiator_outlet_temp": {
        "label": "Radiator Outlet Temperature", "unit": "°C", "module": "Engine",
        "aliases": ["radiator outlet temperature", "radiator outlet temp"]
    },

    # ---------------- TRANSMISSION ----------------

    "transmission_temp": {
        "label": "Transmission Fluid Temperature", "unit": "°C",
        "module": "Transmission",
        "aliases": ["transmission temp", "transmission fluid temperature",
                    "atf temp", "gearbox temperature"]
    },
    "current_gear": {
        "label": "Current Gear", "unit": "", "module": "Transmission",
        "aliases": ["current gear", "actual gear", "selected gear"]
    },
    "input_speed": {
        "label": "Transmission Input Speed", "unit": "rpm",
        "module": "Transmission",
        "aliases": ["input shaft speed", "turbine speed", "transmission input speed"]
    },
    "output_speed": {
        "label": "Transmission Output Speed", "unit": "rpm",
        "module": "Transmission",
        "aliases": ["output shaft speed", "transmission output speed"]
    },
    "tcc_slip": {
        "label": "Torque Converter Clutch Slip", "unit": "rpm",
        "module": "Transmission",
        "aliases": ["tcc slip", "torque converter slip", "lockup slip"]
    },

    # ---------------- ABS / ESC ----------------

    "wheel_speed": {
        "label": "Wheel Speed", "unit": "km/h", "module": "ABS/ESC",
        "aliases": ["wheel speed"]
    },
    "steering_angle": {
        "label": "Steering Angle", "unit": "degree", "module": "ABS/ESC",
        "aliases": ["steering angle", "steering wheel angle"]
    },
    "brake_switch": {
        "label": "Brake Switch Status", "unit": "", "module": "ABS/ESC",
        "aliases": ["brake switch", "stop lamp switch", "brake pedal switch"]
    },
    "abs_pump": {
        "label": "ABS Pump Status", "unit": "", "module": "ABS/ESC",
        "aliases": ["abs pump", "hydraulic pump status"]
    },

    # ---------------- SRS ----------------

    "srs_status": {
        "label": "SRS / Airbag Status", "unit": "", "module": "SRS",
        "aliases": ["srs status", "airbag status", "supplemental restraint status"]
    },
    "srs_deployment_status": {
        "label": "Airbag Deployment Status", "unit": "", "module": "SRS",
        "aliases": ["deployment status", "airbag deployment status", "deployment record"]
    },
    "srs_crash_data": {
        "label": "SRS Crash Data Status", "unit": "", "module": "SRS",
        "aliases": ["crash data status", "crash event data", "collision data"]
    },
    "srs_circuit_status": {
        "label": "SRS Circuit Status", "unit": "", "module": "SRS",
        "aliases": ["airbag circuit status", "squib circuit status",
                    "pretensioner circuit status"]
    },

    # ---------------- EPS ----------------

    "steering_torque": {
        "label": "Steering Torque", "unit": "Nm", "module": "EPS",
        "aliases": ["steering torque", "eps torque"]
    },

    # ---------------- HVAC ----------------

    "ac_pressure": {
        "label": "A/C Refrigerant Pressure", "unit": "kPa", "module": "HVAC",
        "aliases": ["ac pressure", "a/c pressure", "refrigerant pressure"]
    },
    "ac_request": {
        "label": "A/C Request", "unit": "", "module": "HVAC",
        "aliases": ["ac request", "a/c request", "air conditioning request"]
    },
    "ac_compressor_status": {
        "label": "A/C Compressor Status", "unit": "", "module": "HVAC",
        "aliases": ["ac compressor status", "compressor status", "a/c clutch status"]
    },
    "evaporator_temp": {
        "label": "Evaporator Temperature", "unit": "°C", "module": "HVAC",
        "aliases": ["evaporator temperature", "evaporator temp"]
    },

    # ---------------- BATTERY / CHARGING ----------------

    "battery_voltage": {
        "label": "System / Battery Voltage", "unit": "V",
        "module": "Battery/Charging",
        "aliases": ["battery voltage", "control module voltage", "system voltage"]
    },
    "alternator_command": {
        "label": "Alternator Command", "unit": "%", "module": "Battery/Charging",
        "aliases": ["alternator command", "generator command"]
    },

    # ---------------- OTHER MODULES ----------------

    "tpms_pressure": {
        "label": "Tyre Pressure", "unit": "kPa", "module": "TPMS",
        "aliases": ["tire pressure", "tyre pressure", "tpms pressure"]
    },
    "adas_status": {
        "label": "ADAS System Status", "unit": "", "module": "ADAS",
        "aliases": ["adas status", "adas system status"]
    },
    "hybrid_battery_soc": {
        "label": "Hybrid Battery State of Charge", "unit": "%",
        "module": "Hybrid/EV",
        "aliases": ["hybrid battery soc", "hv battery state of charge"]
    }
}


# =========================================================
# 2. MODULE LIST
# =========================================================

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


# =========================================================
# 3. DIAGNOSTIC PROFILES
# =========================================================

DIAGNOSTIC_PROFILES = {

    "fuel_delivery": {
        "label": "Fuel Delivery / Fuel Pressure Problem",
        "keywords": [
            "fuel pressure", "low fuel pressure", "fuel pump",
            "fuel supply", "fuel starvation", "fuel delivery",
            "engine stalls", "engine stalled", "stalls while driving",
            "cuts off while driving", "no fuel", "fuel problem",
            "crank no start", "cranks but does not start",
            "long crank", "hard starting"
        ],
        "modules": ["Engine", "BCM/Body Electrical"],
        "parameters": [
            "engine_rpm", "engine_load", "vehicle_speed",
            "battery_voltage", "fuel_level",
            "fuel_pressure", "fuel_low_pressure",
            "fuel_high_pressure", "fuel_rail_pressure_actual",
            "fuel_rail_pressure_commanded",
            "fuel_pump_command", "fuel_pump_current",
            "fuel_system_status", "short_fuel_trim",
            "long_fuel_trim"
        ],
        "tests": [
            "Record all DTCs and freeze-frame data before clearing any codes.",
            "Compare commanded and actual fuel rail pressure during cranking, idle and suitable load conditions.",
            "Check low-side fuel supply pressure using the vehicle-specific procedure and approved equipment.",
            "Check high-side pressure only using the OEM-approved procedure; do not loosen high-pressure fuel lines.",
            "Check fuel pump power supply, ground, control signal and current draw where applicable.",
            "Check fuel filter, lines, restrictions and fuel quality where applicable.",
            "Repeat pressure checks under the conditions in which the complaint occurs.",
            "Do not condemn the fuel pump from a low-pressure DTC alone."
        ]
    },

    "fuel_starvation": {
        "label": "Possible Fuel Starvation / Fuel Exhaustion",
        "keywords": [
            "ran out of fuel", "fuel ran out", "empty fuel tank",
            "fuel finished", "fuel finished while driving",
            "stopped due to fuel", "engine stopped due to fuel",
            "started after refueling", "starts after adding fuel",
            "start after refueling", "fuel starvation"
        ],
        "modules": ["Engine", "BCM/Body Electrical"],
        "parameters": [
            "fuel_level", "fuel_pressure", "fuel_low_pressure",
            "fuel_high_pressure", "fuel_rail_pressure_actual",
            "fuel_rail_pressure_commanded", "engine_rpm",
            "vehicle_speed", "battery_voltage", "fuel_pump_command"
        ],
        "tests": [
            "Record DTCs and freeze-frame data before clearing codes.",
            "Compare the dashboard fuel indication with the actual fuel quantity using a suitable verification method.",
            "Record whether the engine restarted after adding fuel.",
            "Check whether fuel pressure recovered after refueling.",
            "Check fuel-level sender, wiring and instrument data if the displayed level appears inaccurate.",
            "Check for air entry or loss of fuel supply where applicable.",
            "Treat low-pressure DTCs recorded during fuel starvation as possible consequences until independently verified.",
            "After correcting the cause, clear codes and verify whether they return."
        ]
    },

    "fuel_tank_ventilation": {
        "label": "Fuel Tank Ventilation / EVAP Restriction",
        "keywords": [
            "fuel tank vacuum", "tank vacuum", "fuel tank deformation",
            "fuel tank bulging", "fuel tank collapse", "tank collapsed",
            "tank deformation", "fuel tank pressure",
            "fuel tank vent", "fuel tank breathing",
            "blocked tank vent", "evap vent", "ventilation blockage"
        ],
        "modules": ["Engine", "BCM/Body Electrical"],
        "parameters": [
            "fuel_tank_pressure", "fuel_tank_vacuum",
            "evap_vent_status", "evap_purge_command",
            "fuel_level", "fuel_low_pressure",
            "fuel_rail_pressure_actual", "engine_rpm"
        ],
        "tests": [
            "Inspect the fuel tank for deformation, damage and incorrect mounting.",
            "Inspect tank ventilation hoses, vent valve and EVAP components using the OEM procedure.",
            "Check tank pressure or vacuum with suitable equipment and compare with vehicle specifications.",
            "Check for blocked, kinked or incorrectly routed ventilation lines.",
            "Check whether the fuel supply problem changes under the same conditions after the ventilation fault is corrected.",
            "Do not assume tank deformation is caused by vacuum until the ventilation system and pressure behavior are verified.",
            "Do not open a fuel tank or fuel system without the required fire and vapor safety precautions."
        ]
    },

    "fuel_level_error": {
        "label": "Fuel Level Indication / Sender Problem",
        "keywords": [
            "fuel gauge incorrect", "fuel level incorrect",
            "fuel meter wrong", "fuel percentage wrong",
            "fuel gauge not accurate", "fuel gauge stuck",
            "fuel level sensor", "fuel sender",
            "shows fuel but empty", "fuel reading incorrect"
        ],
        "modules": ["Engine", "BCM/Body Electrical"],
        "parameters": [
            "fuel_level", "battery_voltage", "engine_rpm",
            "vehicle_speed"
        ],
        "tests": [
            "Compare displayed fuel level with actual fuel quantity.",
            "Check fuel-level sender resistance or signal using the OEM procedure.",
            "Inspect sender wiring, connectors, grounds and instrument/BCM data.",
            "For dual-sender tanks, check both sender signals and the specified calculation strategy.",
            "Check whether tank shape, internal baffles or vehicle angle can affect the reading.",
            "Do not replace the fuel pump assembly until the sender fault is isolated; some vehicles integrate the sender into the pump module."
        ]
    },

    "overheating": {
        "label": "Engine Overheating",
        "keywords": [
            "overheat", "overheating", "engine hot",
            "temperature high", "coolant temperature",
            "coolant loss", "engine temperature"
        ],
        "modules": ["Engine"],
        "parameters": [
            "coolant_temp", "engine_rpm", "vehicle_speed",
            "engine_load", "cooling_fan_command",
            "cooling_fan_status", "cooling_fan_speed",
            "thermostat_status", "ac_request",
            "ac_compressor_status", "coolant_pump_command",
            "radiator_outlet_temp"
        ],
        "tests": [
            "Check coolant level only when engine is cold.",
            "Check cooling fan physical operation.",
            "Check thermostat operation using a safe temperature test.",
            "Perform cooling system pressure test.",
            "Check radiator flow and temperature distribution.",
            "Inspect water pump, belt and coolant circulation.",
            "Consider combustion gas test if symptoms indicate head gasket leakage."
        ]
    },

    "misfire": {
        "label": "Engine Misfire / Vibration",
        "keywords": [
            "misfire", "engine vibration", "engine shaking",
            "rough idle", "rough running", "cylinder misfire",
            "engine missing", "missing"
        ],
        "modules": ["Engine"],
        "parameters": [
            "engine_rpm", "engine_load", "coolant_temp",
            "short_fuel_trim", "long_fuel_trim", "maf", "map",
            "ignition_timing", "fuel_pressure", "misfire",
            *[f"misfire_cylinder_{i}" for i in range(1, 9)]
        ],
        "tests": [
            "Check cylinder-specific misfire counters.",
            "Inspect spark plugs and ignition coils.",
            "Use a controlled coil swap test where appropriate.",
            "Check injector operation and wiring.",
            "Check compression if ignition and fuel tests do not explain the fault.",
            "Compare fuel trims at idle and raised RPM."
        ]
    },

    "ac_power_loss": {
        "label": "Power Loss / Vibration When A/C Is ON",
        "keywords": [
            "ac power loss", "a/c power loss", "power loss ac",
            "power loss when ac", "vibration when ac",
            "vibration ac", "ac on vibration", "engine weak ac",
            "air conditioner power loss"
        ],
        "modules": ["Engine", "HVAC"],
        "parameters": [
            "engine_rpm", "engine_load", "throttle_position",
            "short_fuel_trim", "long_fuel_trim", "maf", "map",
            "ignition_timing", "misfire", "ac_request",
            "ac_compressor_status", "ac_pressure",
            "cooling_fan_status"
        ],
        "tests": [
            "Record comparable data with A/C OFF and ON.",
            "Check compressor engagement and abnormal mechanical load.",
            "Check engine idle compensation.",
            "Check cylinder misfire counters during A/C engagement.",
            "Inspect compressor belt and tensioner.",
            "Check refrigerant pressure using approved equipment."
        ]
    },

    "catalyst_o2": {
        "label": "Catalytic Converter / Oxygen Sensor",
        "keywords": [
            "catalytic converter", "catalyst", "catalyst efficiency",
            "p0420", "p0430", "o2 sensor", "oxygen sensor",
            "lambda sensor", "emission problem"
        ],
        "modules": ["Engine"],
        "parameters": [
            "o2_sensor", "o2_upstream", "o2_downstream",
            "short_fuel_trim", "long_fuel_trim", "engine_rpm",
            "engine_load", "coolant_temp", "maf", "map",
            "catalyst_temp", "catalyst_monitor",
            "commanded_equivalence_ratio"
        ],
        "tests": [
            "Compare upstream and downstream sensor behavior under suitable operating conditions.",
            "Check sensor heater and wiring faults.",
            "Inspect exhaust leaks before and around sensors.",
            "Check fuel mixture and misfire problems.",
            "Check catalyst temperature and exhaust restriction if indicated.",
            "Verify catalyst monitor results using vehicle-specific procedures."
        ]
    },

    "transmission": {
        "label": "Transmission / Gearbox Problem",
        "keywords": [
            "transmission", "gearbox", "gear shift", "gear problem",
            "hard shift", "jerk while shifting", "slipping",
            "gear slip", "delayed engagement"
        ],
        "modules": ["Transmission", "Engine"],
        "parameters": [
            "transmission_temp", "current_gear", "input_speed",
            "output_speed", "tcc_slip", "engine_rpm",
            "vehicle_speed", "engine_load"
        ],
        "tests": [
            "Compare commanded gear and actual gear if available.",
            "Check transmission fluid condition and level using OEM procedure.",
            "Compare input and output speed data.",
            "Check TCC slip under suitable driving conditions.",
            "Review transmission DTC and freeze-frame data."
        ]
    },

    "srs_airbag": {
        "label": "Airbag / SRS Diagnosis",
        "keywords": [
            "airbag", "srs", "airbag light", "airbag deployed",
            "airbag deployment", "pretensioner",
            "seat belt pretensioner", "resistor bypass", "airbag bypass"
        ],
        "modules": ["SRS"],
        "parameters": [
            "srs_status", "srs_deployment_status",
            "srs_crash_data", "srs_circuit_status"
        ],
        "tests": [
            "Read all SRS DTCs and module information.",
            "Check deployment history using supported OEM procedures.",
            "Inspect correct part numbers and physical components.",
            "Check wiring and connectors using approved SRS procedures.",
            "Investigate suspected resistor bypass through qualified inspection.",
            "Never probe airbag squib circuits with a test lamp or ordinary multimeter."
        ]
    },

    "cooling_fan": {
        "label": "Cooling Fan Problem",
        "keywords": [
            "fan not working", "radiator fan", "cooling fan",
            "fan problem", "fan not running"
        ],
        "modules": ["Engine"],
        "parameters": [
            "coolant_temp", "cooling_fan_command",
            "cooling_fan_status", "cooling_fan_speed",
            "ac_request", "vehicle_speed", "engine_rpm"
        ],
        "tests": [
            "Compare ECU fan command with actual fan operation.",
            "Inspect fan fuse, relay, wiring and motor.",
            "Use supported active test if available.",
            "Check temperature sensor accuracy."
        ]
    },

    "battery_charging": {
        "label": "Battery / Charging Problem",
        "keywords": [
            "battery", "charging", "alternator", "not charging",
            "battery drain", "starting problem", "no start"
        ],
        "modules": ["Battery/Charging", "Engine"],
        "parameters": [
            "battery_voltage", "alternator_command",
            "engine_rpm", "engine_load"
        ],
        "tests": [
            "Perform battery health test.",
            "Measure charging voltage under suitable conditions.",
            "Check alternator output and wiring.",
            "Perform parasitic draw test if battery drains while parked."
        ]
    },

    "dpf": {
        "label": "DPF / Diesel Emission Problem",
        "keywords": [
            "dpf", "diesel particulate filter", "soot",
            "regeneration", "regen", "dpf blockage"
        ],
        "modules": ["Engine"],
        "parameters": [
            "dpf_pressure", "dpf_soot", "coolant_temp",
            "engine_rpm", "engine_load", "vehicle_speed",
            "catalyst_temp"
        ],
        "tests": [
            "Check DPF differential pressure sensor and hoses.",
            "Check soot load and regeneration history.",
            "Check exhaust temperature sensors.",
            "Investigate causes of excessive soot production.",
            "Do not force regeneration until vehicle-specific safety checks are completed."
        ]
    },

    "steering": {
        "label": "Power Steering / EPS Problem",
        "keywords": [
            "steering", "hard steering", "eps",
            "power steering", "steering noise"
        ],
        "modules": ["EPS", "ABS/ESC"],
        "parameters": [
            "steering_torque", "steering_angle", "battery_voltage"
        ],
        "tests": [
            "Check EPS and ABS DTCs.",
            "Inspect steering wiring and connectors.",
            "Check power supply and ground.",
            "Verify steering angle calibration where required."
        ]
    }
}


# =========================================================
# 4. TEXT NORMALIZATION
# =========================================================

def normalize_text(value):
    value = str(value or "").strip().lower()
    value = value.replace("%", " percent ")
    value = re.sub(r"[_\-/]+", " ", value)
    value = re.sub(r"[^a-z0-9° ]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


# =========================================================
# 5. IDENTIFY PARAMETER
# =========================================================

def identify_parameter(column_name):
    name = normalize_text(column_name)

    if not name:
        return None

    # Exact matches first.
    for key, meta in PARAMETERS.items():
        candidates = [key.replace("_", " "), meta["label"]] + meta["aliases"]

        for alias in candidates:
            if name == normalize_text(alias):
                return key

    # Safer phrase matching.
    for key, meta in PARAMETERS.items():
        candidates = [meta["label"]] + meta["aliases"]

        for alias in candidates:
            alias_name = normalize_text(alias)

            if len(alias_name) < 7:
                continue

            pattern = (
                r"(?<![a-z0-9])"
                + re.escape(alias_name)
                + r"(?![a-z0-9])"
            )

            if re.search(pattern, name):
                return key

    return None


# =========================================================
# 6. PARAMETER METADATA
# =========================================================

def get_parameter_metadata(parameter_key):
    return PARAMETERS.get(parameter_key, {})


# =========================================================
# 7. DIAGNOSTIC PROFILE DETECTION
# =========================================================

def detect_diagnostic_profiles(complaint):
    complaint_text = normalize_text(complaint)
    matched = []

    for profile_key, profile in DIAGNOSTIC_PROFILES.items():
        for keyword in profile["keywords"]:
            keyword_text = normalize_text(keyword)

            if not keyword_text:
                continue

            # Match full phrases, not arbitrary partial words.
            pattern = (
                r"(?<![a-z0-9])"
                + re.escape(keyword_text)
                + r"(?![a-z0-9])"
            )

            if re.search(pattern, complaint_text):
                matched.append(profile_key)
                break

    return matched


# =========================================================
# 8. GET DIAGNOSTIC PROFILE
# =========================================================

def get_diagnostic_profile(profile_key):
    return DIAGNOSTIC_PROFILES.get(profile_key, {})


# =========================================================
# 9. GET COMPLAINT-BASED MODULES
# =========================================================

def suggest_modules(complaint):
    selected = {"Engine"}

    for profile_key in detect_diagnostic_profiles(complaint):
        selected.update(DIAGNOSTIC_PROFILES[profile_key]["modules"])

    return [module for module in MODULES if module in selected]


# =========================================================
# 10. REQUIRED PARAMETER RECOMMENDATIONS
# =========================================================

def default_parameter_requirements(vehicle, complaint, modules=None):
    matched_profiles = detect_diagnostic_profiles(complaint)

    # Important: supplied modules must not exclude modules required
    # by the detected complaint profiles.
    selected_modules = set(modules or [])
    selected_modules.update(suggest_modules(complaint))

    if not selected_modules:
        selected_modules.add("Engine")

    required_keys = []
    profile_tests = []

    for profile_key in matched_profiles:
        profile = DIAGNOSTIC_PROFILES[profile_key]
        selected_modules.update(profile["modules"])
        required_keys.extend(profile["parameters"])
        profile_tests.extend(profile["tests"])

    required_keys = list(dict.fromkeys(required_keys))

    if not required_keys:
        required_keys = [
            "engine_rpm",
            "coolant_temp",
            "engine_load",
            "vehicle_speed",
            "battery_voltage"
        ]

    requirements = []

    for key in required_keys:
        meta = PARAMETERS.get(key)

        if not meta:
            continue

        if meta["module"] not in selected_modules:
            continue

        requirements.append({
            "parameter": key,
            "label": meta["label"],
            "unit": meta["unit"],
            "module": meta["module"],
            "priority": "Must Have",
            "note": (
                "Recommended for this complaint. Confirm availability "
                "in the vehicle ECU and scanner. This is not an OEM pass/fail limit."
            )
        })

    # Optional parameters from selected modules.
    for key, meta in PARAMETERS.items():
        if meta["module"] not in selected_modules:
            continue

        if key in required_keys:
            continue

        requirements.append({
            "parameter": key,
            "label": meta["label"],
            "unit": meta["unit"],
            "module": meta["module"],
            "priority": "Optional",
            "note": (
                "Additional parameter. Select only if supported "
                "and relevant to the diagnostic case."
            )
        })

    return requirements


# =========================================================
# 11. PHYSICAL TEST RECOMMENDATIONS
# =========================================================

def get_recommended_tests(complaint):
    tests = []

    for profile_key in detect_diagnostic_profiles(complaint):
        tests.extend(DIAGNOSTIC_PROFILES[profile_key]["tests"])

    return list(dict.fromkeys(tests))


# =========================================================
# 12. DIAGNOSTIC SUMMARY
# =========================================================

def get_complaint_diagnostic_summary(complaint):
    matched_profiles = detect_diagnostic_profiles(complaint)

    return {
        "matched_profiles": matched_profiles,
        "modules": suggest_modules(complaint),
        "recommended_tests": get_recommended_tests(complaint),
        "profile_found": bool(matched_profiles)
    }


# =========================================================
# 13. PROFILE INFORMATION FOR OTHER MODULES
# =========================================================

def get_all_diagnostic_profiles():
    """Return available diagnostic profiles for the application."""
    return DIAGNOSTIC_PROFILES


def get_all_parameters():
    """Return the full parameter database."""
    return PARAMETERS
