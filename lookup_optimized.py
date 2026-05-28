_CORE = r'''import math
_ROW_DICTS = None
def row_dicts(name, unit_system="metric"):
    global _ROW_DICTS
    if _ROW_DICTS is None:
        from thermo_data_optimized import row_dicts as loaded_row_dicts
        _ROW_DICTS = loaded_row_dicts
    return _ROW_DICTS(name, unit_system)

# =========================================================
# LOOKUP.PY  (optimized for TI-Nspire CX II)
# Keep this file in the same folder as thermo_data_optimized.py.
# =========================================================

GO_BACK = "__GO_BACK__"
QUIT_CANCELLED = "__QUIT_CANCELLED__"

MAX_LINES = 8
NEXT_PAGE_OPTION = "9"
PREV_PAGE_OPTION = "0"
BACK_OPTION = "8"

HISTORY = []

SUPPORTED_FLUIDS = [
    "Water",
    "R22",
    "R134a",
    "Ammonia",
    "Propane",
]

BASE_IDEAL_GAS_OPTIONS = [
    "Air",
    "N2",
    "O2",
    "CO2",
    "CO",
    "H2O",
    "Helium",
]


def _safe_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except:
        return None


def _error_dict(message):
    return {"error": str(message)}


def _is_error(result):
    return type(result) is dict and "error" in result


# =========================================================
# TABLE / PROPERTY LOOKUP CORE
# =========================================================

def linear_interpolate(x, x1, y1, x2, y2):
    if x2 == x1:
        return y1
    return y1 + (y2 - y1) * (x - x1) / (x2 - x1)


def get_temp_key(unit_system):
    s = str(unit_system).strip().lower()
    if s == "si":
        return "T_C"
    if s == "english":
        return "T_F"
    raise ValueError("Unknown unit system.")


def _unit_system_key(unit_system):
    s = str(unit_system).strip().lower()
    if s in ("si", "metric"):
        return "metric"
    return "imperial"


IDEAL_GAS_MOLAR_MASS = {
    "air": 28.97,
    "n2": 28.0134,
    "o2": 31.999,
    "co2": 44.01,
    "co": 28.01,
    "h2o": 18.01528,
    "helium": 4.0026,
}

IDEAL_GAS_LABELS = {
    "air": "Air",
    "n2": "N2",
    "o2": "O2",
    "co2": "CO2",
    "co": "CO",
    "h2o": "H2O",
    "helium": "Helium",
}

IDEAL_GAS_ALIASES = {
    "air": "air",
    "air (equivalent)": "air",
    "n2": "n2",
    "nitrogen": "n2",
    "o2": "o2",
    "oxygen": "o2",
    "co2": "co2",
    "carbon dioxide": "co2",
    "co": "co",
    "carbon monoxide": "co",
    "h2o": "h2o",
    "water": "h2o",
    "water vapor": "h2o",
    "steam": "h2o",
    "helium": "helium",
    "he": "helium",
}

IDEAL_GAS_TABLE_NAMES = {
    "air": "air_ideal_gas_properties",
    "n2": "n2_ideal_gas_properties_selected",
    "o2": "o2_ideal_gas_properties_selected",
    "co2": "co2_ideal_gas_properties_selected",
    "co": "co_ideal_gas_properties_selected",
    "h2o": "h2o_ideal_gas_properties_selected",
}

def _normal_gas_alias(value):
    text = str(value).strip().lower()
    text = text.replace("—", "-").replace("_", " ")
    while "  " in text:
        text = text.replace("  ", " ")
    return text


def _formula_key(value):
    formula = str(value).strip()
    if not formula or formula in ("-", "—"):
        return None
    return formula.lower()


def _a1_default_gas_key(substance, formula):
    alias = _normal_gas_alias(substance)
    if alias in IDEAL_GAS_ALIASES:
        return IDEAL_GAS_ALIASES[alias]
    formula_key = _formula_key(formula)
    if formula_key is not None:
        return formula_key
    return alias


def _a1_default_gas_label(substance, formula, key):
    alias = _normal_gas_alias(substance)
    preferred = {
        "air (equivalent)": "Air",
        "carbon dioxide": "CO2",
        "carbon monoxide": "CO",
        "water": "H2O",
        "nitrogen": "N2",
        "oxygen": "O2",
        "hydrogen": "H2",
        "methane": "CH4",
        "ethylene": "C2H4",
        "acetylene": "C2H2",
        "sulfur dioxide": "SO2",
    }
    if alias in preferred:
        return preferred[alias]
    if key in IDEAL_GAS_LABELS:
        return IDEAL_GAS_LABELS[key]
    return str(substance).strip()


def _register_ideal_gas(key, label, molar_mass, aliases):
    if key is None or molar_mass is None:
        return
    IDEAL_GAS_MOLAR_MASS[key] = float(molar_mass)
    IDEAL_GAS_LABELS.setdefault(key, label)
    IDEAL_GAS_ALIASES[_normal_gas_alias(key)] = key
    IDEAL_GAS_ALIASES[_normal_gas_alias(label)] = key
    for alias in aliases:
        if alias is not None and str(alias).strip():
            IDEAL_GAS_ALIASES[_normal_gas_alias(alias)] = key


def _load_a1_ideal_gas_options():
    options = list(BASE_IDEAL_GAS_OPTIONS)
    try:
        rows = row_dicts("table_a1_atomic_or_molecular_weights_and_critical_properties", unit_system="metric")
    except:
        rows = []

    for row in rows:
        substance = row.get("substance", row.get("Substance", ""))
        formula = row.get("chemical_formula", row.get("Chemical_Formula", ""))
        molar_mass = row.get("M_kg_per_kmol", row.get("M_lb_per_lbmol", None))
        if molar_mass is None:
            continue
        # Solid entries in A-1 have no useful gas-state critical data.
        if _normal_gas_alias(substance) in ("carbon", "copper"):
            continue
        key = _a1_default_gas_key(substance, formula)
        label = _a1_default_gas_label(substance, formula, key)
        _register_ideal_gas(key, label, molar_mass, (substance, formula))
        if label not in options:
            options.append(label)

    return options


IDEAL_GAS_OPTIONS = None

def get_ideal_gas_options():
    global IDEAL_GAS_OPTIONS
    if IDEAL_GAS_OPTIONS is None:
        IDEAL_GAS_OPTIONS = _load_a1_ideal_gas_options()
    return IDEAL_GAS_OPTIONS


def _canonical_ideal_gas_key(fluid):
    alias = _normal_gas_alias(fluid)
    return IDEAL_GAS_ALIASES.get(alias, alias)


def _is_supported_real_fluid_name(fluid):
    key = str(fluid).strip().lower()
    return key in {item.lower() for item in SUPPORTED_FLUIDS}


# Pre-built set for O(1) membership tests
R_UNIVERSAL_KJ_PER_KMOL_K = 8.314
BTU_PER_KJ = 0.429922614
LBM_PER_KG = 2.20462262185
PSIA_PER_BAR = 14.5037738
BTU_PER_LBM_PER_KJ_PER_KG = 0.429922614
KJ_PER_KG_PER_BTU_PER_LBM = 1.0 / BTU_PER_LBM_PER_KJ_PER_KG
BTU_PER_LBM_R_PER_KJ_PER_KG_K = 0.2388458966
KJ_PER_KG_K_PER_BTU_PER_LBM_R = 1.0 / BTU_PER_LBM_R_PER_KJ_PER_KG_K
FT3_PER_LBM_PER_M3_PER_KG = 16.01846337
M3_PER_KG_PER_FT3_PER_LBM = 1.0 / FT3_PER_LBM_PER_M3_PER_KG


def _to_kelvin(temp_value, unit_system):
    t = float(temp_value)
    if _unit_system_key(unit_system) == "metric":
        return t
    return t * 5.0 / 9.0


def _from_kelvin(temp_k, unit_system):
    if _unit_system_key(unit_system) == "metric":
        return float(temp_k)
    return float(temp_k) * 9.0 / 5.0


def _pressure_to_bar(pressure_value, unit_system):
    p = float(pressure_value)
    if _unit_system_key(unit_system) == "metric":
        return p
    return p / PSIA_PER_BAR


def _pressure_from_bar(pressure_bar, unit_system):
    if _unit_system_key(unit_system) == "metric":
        return float(pressure_bar)
    return float(pressure_bar) * PSIA_PER_BAR


def _ideal_gas_temp_key(unit_system):
    if _unit_system_key(unit_system) == "metric":
        return "T_K"
    return "T_R"


def _ideal_gas_pressure_key(unit_system):
    if _unit_system_key(unit_system) == "metric":
        return "pressure_bar"
    return "pressure_psia"


def is_ideal_gas(fluid):
    key = _canonical_ideal_gas_key(fluid)
    if key in IDEAL_GAS_MOLAR_MASS:
        return True
    get_ideal_gas_options()
    return _canonical_ideal_gas_key(fluid) in IDEAL_GAS_MOLAR_MASS


def _ideal_gas_R(fluid):
    gas = _canonical_ideal_gas_key(fluid)
    mm = IDEAL_GAS_MOLAR_MASS.get(gas)
    if mm is None:
        return None
    return R_UNIVERSAL_KJ_PER_KMOL_K / mm


def _btu_per_lb_from_kj_per_kg(value):
    return float(value) * BTU_PER_KJ / LBM_PER_KG


def _psia_from_bar(value):
    return float(value) * PSIA_PER_BAR


# ---- Ideal-gas table cache (built once per gas) ----
_IDEAL_GAS_ROWS_CACHE = {}


def _ideal_gas_table_rows_si(fluid):
    gas = _canonical_ideal_gas_key(fluid)
    if gas in _IDEAL_GAS_ROWS_CACHE:
        return _IDEAL_GAS_ROWS_CACHE[gas]

    if gas == "helium":
        r = _ideal_gas_R("helium")
        cp = 2.5 * r
        cv = cp - r
        rows = []
        for T in range(200, 2001, 10):
            t = float(T)
            rows.append({
                "T_K": t,
                "h_kJ_per_kg": cp * t,
                "u_kJ_per_kg": cv * t,
                "s0_kJ_per_kg_K": cp * math.log(t),
            })
        _IDEAL_GAS_ROWS_CACHE[gas] = rows
        return rows

    table_name = IDEAL_GAS_TABLE_NAMES.get(gas)
    if table_name is None:
        _IDEAL_GAS_ROWS_CACHE[gas] = []
        return []

    raw_rows = row_dicts(table_name, unit_system="metric")
    if not raw_rows:
        _IDEAL_GAS_ROWS_CACHE[gas] = []
        return []

    out = []
    molar_mass = IDEAL_GAS_MOLAR_MASS[gas]
    if gas == "air":
        for row in raw_rows:
            out.append({
                "T_K": float(row["T_K"]),
                "h_kJ_per_kg": float(row["h_kJ_per_kg"]),
                "u_kJ_per_kg": float(row["u_kJ_per_kg"]),
                "s0_kJ_per_kg_K": float(row["s0_kJ_per_kg_K"]),
                "pr": row.get("pr"),
                "vr": row.get("vr"),
            })
    else:
        for row in raw_rows:
            out.append({
                "T_K": float(row["T_K"]),
                "h_kJ_per_kg": float(row["h_kJ_per_kmol"]) / molar_mass,
                "u_kJ_per_kg": float(row["u_kJ_per_kmol"]) / molar_mass,
                "s0_kJ_per_kg_K": float(row["s0_kJ_per_kmol_K"]) / molar_mass,
            })
    out.sort(key=lambda r: r["T_K"])
    _IDEAL_GAS_ROWS_CACHE[gas] = out
    return out


# ---- Binary search helpers ----

def _bisect_left_key(rows, key, value):
    """Return index i such that rows[i-1][key] < value <= rows[i][key]."""
    lo, hi = 0, len(rows)
    while lo < hi:
        mid = (lo + hi) >> 1
        if rows[mid][key] < value:
            lo = mid + 1
        else:
            hi = mid
    return lo


def _interp_ideal_rows_by_temperature(rows, temp_k):
    if not rows:
        return None
    if temp_k < rows[0]["T_K"] or temp_k > rows[-1]["T_K"]:
        return None

    i = _bisect_left_key(rows, "T_K", temp_k)
    if i < len(rows) and rows[i]["T_K"] == temp_k:
        return rows[i].copy()

    # rows[i-1]["T_K"] < temp_k < rows[i]["T_K"]
    if i == 0 or i >= len(rows):
        return None
    low = rows[i - 1]
    high = rows[i]
    out = {}
    tk_lo = low["T_K"]
    tk_hi = high["T_K"]
    for k in low:
        try:
            out[k] = linear_interpolate(temp_k, tk_lo, low[k], tk_hi, high[k])
        except:
            out[k] = low[k]
    return out


def _ideal_gas_find_temperature_from_property(rows, key, target_value):
    usable = [row for row in rows if key in row and row[key] is not None]
    if not usable:
        return None
    usable.sort(key=lambda r: r[key])
    if target_value < usable[0][key] or target_value > usable[-1][key]:
        return None

    i = _bisect_left_key(usable, key, target_value)
    if i < len(usable) and usable[i][key] == target_value:
        return usable[i]["T_K"]
    if i == 0 or i >= len(usable):
        return None
    low = usable[i - 1]
    high = usable[i]
    return linear_interpolate(target_value, low[key], low["T_K"], high[key], high["T_K"])



def _convert_ideal_input_to_si(unit_system, h=None, u=None, s=None, v=None):
    if _unit_system_key(unit_system) == "metric":
        return h, u, s, v
    if h is not None:
        h = float(h) * KJ_PER_KG_PER_BTU_PER_LBM
    if u is not None:
        u = float(u) * KJ_PER_KG_PER_BTU_PER_LBM
    if s is not None:
        s = float(s) * KJ_PER_KG_K_PER_BTU_PER_LBM_R
    if v is not None:
        v = float(v) * M3_PER_KG_PER_FT3_PER_LBM
    return h, u, s, v


def _add_ideal_gas_display_units(row, unit_system):
    if _unit_system_key(unit_system) == "imperial":
        if "h_kJ_per_kg" in row:
            row["h_Btu_per_lb"] = row["h_kJ_per_kg"] * BTU_PER_LBM_PER_KJ_PER_KG
        if "u_kJ_per_kg" in row:
            row["u_Btu_per_lb"] = row["u_kJ_per_kg"] * BTU_PER_LBM_PER_KJ_PER_KG
        if "s_kJ_per_kg_K" in row:
            row["s_Btu_per_lb_R"] = row["s_kJ_per_kg_K"] * BTU_PER_LBM_R_PER_KJ_PER_KG_K
        if "s0_kJ_per_kg_K" in row:
            row["s0_Btu_per_lbR"] = row["s0_kJ_per_kg_K"] * BTU_PER_LBM_R_PER_KJ_PER_KG_K
        if "v_m3_per_kg" in row:
            row["v_ft3_per_lb"] = row["v_m3_per_kg"] * FT3_PER_LBM_PER_M3_PER_KG
        if "R_kJ_per_kg_K" in row:
            row["R_Btu_per_lb_R"] = row["R_kJ_per_kg_K"] * BTU_PER_LBM_R_PER_KJ_PER_KG_K
        if "cp_kJ_per_kg_K" in row:
            row["cp_Btu_per_lb_R"] = row["cp_kJ_per_kg_K"] * BTU_PER_LBM_R_PER_KJ_PER_KG_K
        row["_display_unit_system"] = "English"
    else:
        row["_display_unit_system"] = "SI"
    return row


def _sat_property_keys_for_row(row, prop_symbol):
    if prop_symbol == "v":
        if "vf_m3_per_kg" in row and "vg_m3_per_kg" in row:
            return "vf_m3_per_kg", "vg_m3_per_kg"
        if "vf_ft3_per_lb" in row and "vg_ft3_per_lb" in row:
            return "vf_ft3_per_lb", "vg_ft3_per_lb"
    if prop_symbol == "u":
        if "uf_kJ_per_kg" in row and "ug_kJ_per_kg" in row:
            return "uf_kJ_per_kg", "ug_kJ_per_kg"
        if "uf_Btu_per_lb" in row and "ug_Btu_per_lb" in row:
            return "uf_Btu_per_lb", "ug_Btu_per_lb"
    if prop_symbol == "h":
        if "hf_kJ_per_kg" in row and "hg_kJ_per_kg" in row:
            return "hf_kJ_per_kg", "hg_kJ_per_kg"
        if "hf_Btu_per_lb" in row and "hg_Btu_per_lb" in row:
            return "hf_Btu_per_lb", "hg_Btu_per_lb"
    if prop_symbol == "s":
        if "sf_kJ_per_kg_K" in row and "sg_kJ_per_kg_K" in row:
            return "sf_kJ_per_kg_K", "sg_kJ_per_kg_K"
        if "sf_Btu_per_lb_R" in row and "sg_Btu_per_lb_R" in row:
            return "sf_Btu_per_lb_R", "sg_Btu_per_lb_R"
        if "sf_Btu_per_lbR" in row and "sg_Btu_per_lbR" in row:
            return "sf_Btu_per_lbR", "sg_Btu_per_lbR"
    return None, None


def _sat_liquid_key_for_row(row, prop_symbol):
    f_key, _ = _sat_property_keys_for_row(row, prop_symbol)
    return f_key


def _ideal_gas_state_row(fluid, unit_system, temp_k, pressure_bar):
    rows = _ideal_gas_table_rows_si(fluid)
    interp = _interp_ideal_rows_by_temperature(rows, float(temp_k))
    if interp is None:
        return _error_dict("Temperature is outside the ideal-gas table range.")

    r = _ideal_gas_R(fluid)
    pb = float(pressure_bar)
    tk = float(temp_k)
    s_actual = interp["s0_kJ_per_kg_K"] - r * math.log(pb)
    v = r * tk / (pb * 100.0)

    row = {
        "region": "ideal_gas",
        "T_K": tk,
        "T_C": tk - 273.15,
        "T_R": tk * 9.0 / 5.0,
        "T_F": (tk - 273.15) * 9.0 / 5.0 + 32.0,
        "pressure_bar": pb,
        "pressure_psia": _psia_from_bar(pb),
        "h_kJ_per_kg": interp["h_kJ_per_kg"],
        "u_kJ_per_kg": interp["u_kJ_per_kg"],
        "s0_kJ_per_kg_K": interp["s0_kJ_per_kg_K"],
        "s_kJ_per_kg_K": s_actual,
        "v_m3_per_kg": v,
        "R_kJ_per_kg_K": r,
        "ideal_gas": True,
    }
    if interp.get("pr") is not None:
        row["pr"] = interp["pr"]
    if interp.get("vr") is not None:
        row["vr"] = interp["vr"]
    if str(fluid).strip().lower() == "helium":
        row["cp_kJ_per_kg_K"] = 2.5 * r
        row["k"] = 5.0 / 3.0
    return _add_ideal_gas_display_units(row, unit_system)


def _ideal_gas_law_only_state_row(fluid, unit_system, temp_k, pressure_bar):
    r = _ideal_gas_R(fluid)
    if r is None:
        return _error_dict("Ideal-gas constant is not available.")
    pb = float(pressure_bar)
    tk = float(temp_k)
    if pb <= 0.0 or tk <= 0.0:
        return _error_dict("Ideal-gas pressure and temperature must be positive.")
    row = {
        "region": "ideal_gas",
        "T_K": tk,
        "T_C": tk - 273.15,
        "T_R": tk * 9.0 / 5.0,
        "T_F": (tk - 273.15) * 9.0 / 5.0 + 32.0,
        "pressure_bar": pb,
        "pressure_psia": _psia_from_bar(pb),
        "v_m3_per_kg": r * tk / (pb * 100.0),
        "R_kJ_per_kg_K": r,
        "ideal_gas": True,
        "note": "A-1 gas: only ideal-gas law properties are available.",
    }
    return _add_ideal_gas_display_units(row, unit_system)


def idealGasLookUp(gas_name, unit_system, temp=None, pressure=None, h=None, u=None, s=None, v=None, sat_state=None):
    if sat_state is not None:
        return _error_dict("Ideal gases do not use saturated-state inputs.")

    gas = _canonical_ideal_gas_key(gas_name)
    if not is_ideal_gas(gas):
        return _error_dict("Not an ideal-gas fluid.")

    temp = _safe_float(temp)
    pressure = _safe_float(pressure)
    h = _safe_float(h)
    u = _safe_float(u)
    s = _safe_float(s)
    v = _safe_float(v)
    h, u, s, v = _convert_ideal_input_to_si(unit_system, h=h, u=u, s=s, v=v)

    temp_k = _to_kelvin(temp, unit_system) if temp is not None else None
    pressure_bar = _pressure_to_bar(pressure, unit_system) if pressure is not None else None
    rows = _ideal_gas_table_rows_si(gas)

    if not rows:
        if temp_k is not None and pressure_bar is not None and h is None and u is None and s is None:
            if v is not None:
                r = _ideal_gas_R(gas)
                expected_v = r * temp_k / (100.0 * pressure_bar) if r is not None else None
                if expected_v is None or not _close_enough(expected_v, v):
                    return _error_dict("Inputs are inconsistent with the ideal-gas law.")
            return _ideal_gas_law_only_state_row(gas, unit_system, temp_k, pressure_bar)
        if temp_k is not None and v is not None and h is None and u is None and s is None:
            r = _ideal_gas_R(gas)
            if r is None or float(v) <= 0.0:
                return _error_dict("Ideal-gas constant and specific volume must be positive.")
            pressure_bar = r * temp_k / (100.0 * float(v))
            return _ideal_gas_law_only_state_row(gas, unit_system, temp_k, pressure_bar)
        if pressure_bar is not None and v is not None and h is None and u is None and s is None:
            r = _ideal_gas_R(gas)
            if r is None or r == 0.0:
                return _error_dict("Ideal-gas constant is not available.")
            temp_k = pressure_bar * 100.0 * float(v) / r
            return _ideal_gas_law_only_state_row(gas, unit_system, temp_k, pressure_bar)
        return _error_dict("Caloric ideal-gas data are not available for this A-1 gas.")

    if temp_k is not None and pressure_bar is not None and h is None and u is None and s is None and v is None:
        return _ideal_gas_state_row(gas, unit_system, temp_k, pressure_bar)

    if temp_k is not None and pressure_bar is not None and s is not None:
        row = _ideal_gas_state_row(gas, unit_system, temp_k, pressure_bar)
        if _is_error(row):
            return row
        if abs(float(row["s_kJ_per_kg_K"]) - float(s)) > 1e-4:
            return _error_dict("Inputs are inconsistent for the resolved ideal-gas state.")
        return row

    if temp_k is not None and pressure_bar is not None and h is not None:
        row = _ideal_gas_state_row(gas, unit_system, temp_k, pressure_bar)
        if _is_error(row):
            return row
        if abs(float(row["h_kJ_per_kg"]) - float(h)) > 1e-3:
            return _error_dict("Inputs are inconsistent for the resolved ideal-gas state.")
        return row

    if temp_k is not None and pressure_bar is not None and u is not None:
        row = _ideal_gas_state_row(gas, unit_system, temp_k, pressure_bar)
        if _is_error(row):
            return row
        if abs(float(row["u_kJ_per_kg"]) - float(u)) > 1e-3:
            return _error_dict("Inputs are inconsistent for the resolved ideal-gas state.")
        return row

    if temp_k is not None and pressure_bar is not None and v is not None:
        row = _ideal_gas_state_row(gas, unit_system, temp_k, pressure_bar)
        if _is_error(row):
            return row
        if not _close_enough(float(row["v_m3_per_kg"]), float(v)):
            return _error_dict("Inputs are inconsistent for the resolved ideal-gas state.")
        return row

    if pressure_bar is not None and h is not None:
        t_guess = _ideal_gas_find_temperature_from_property(rows, "h_kJ_per_kg", float(h))
        if t_guess is None:
            return _error_dict("Could not determine ideal-gas temperature from enthalpy.")
        return _ideal_gas_state_row(gas, unit_system, t_guess, pressure_bar)

    if pressure_bar is not None and u is not None:
        t_guess = _ideal_gas_find_temperature_from_property(rows, "u_kJ_per_kg", float(u))
        if t_guess is None:
            return _error_dict("Could not determine ideal-gas temperature from internal energy.")
        return _ideal_gas_state_row(gas, unit_system, t_guess, pressure_bar)

    if pressure_bar is not None and s is not None:
        r = _ideal_gas_R(gas)
        target_s0 = float(s) + r * math.log(float(pressure_bar))
        t_guess = _ideal_gas_find_temperature_from_property(rows, "s0_kJ_per_kg_K", target_s0)
        if t_guess is None:
            return _error_dict("Could not determine ideal-gas temperature from entropy and pressure.")
        return _ideal_gas_state_row(gas, unit_system, t_guess, pressure_bar)

    if temp_k is not None and s is not None:
        interp = _interp_ideal_rows_by_temperature(rows, temp_k)
        if interp is None:
            return _error_dict("Temperature is outside the ideal-gas table range.")
        r = _ideal_gas_R(gas)
        pressure_bar = math.exp((interp["s0_kJ_per_kg_K"] - float(s)) / r)
        return _ideal_gas_state_row(gas, unit_system, temp_k, pressure_bar)

    if temp_k is not None and v is not None:
        r = _ideal_gas_R(gas)
        pressure_bar = r * temp_k / (100.0 * float(v))
        return _ideal_gas_state_row(gas, unit_system, temp_k, pressure_bar)

    if pressure_bar is not None and v is not None:
        r = _ideal_gas_R(gas)
        if r is None or r == 0.0:
            return _error_dict("Ideal-gas constant is not available.")
        temp_k = pressure_bar * 100.0 * float(v) / r
        return _ideal_gas_state_row(gas, unit_system, temp_k, pressure_bar)

    return _error_dict("Unsupported ideal-gas input combination.")


def get_all_gas_data(gas_name, unit_system="metric"):
    gas = str(gas_name).lower()

    out = {
        "saturated_temperature": [],
        "saturated_pressure": [],
        "superheated": [],
        "compressed": [],
    }

    if is_ideal_gas(gas) and not _is_supported_real_fluid_name(gas):
        out["ideal_gas"] = _ideal_gas_table_rows_si(gas)
        return out

    try:
        out["saturated_temperature"] = row_dicts(gas + "_saturated_temperature", unit_system=unit_system)
    except:
        pass
    try:
        out["saturated_pressure"] = row_dicts(gas + "_saturated_pressure", unit_system=unit_system)
    except:
        pass
    try:
        out["superheated"] = row_dicts(gas + "_superheated", unit_system=unit_system)
    except:
        pass
    try:
        out["compressed"] = row_dicts(gas + "_compressed", unit_system=unit_system)
    except:
        pass

    return out


def find_property_keys(row):
    keys = {"u": None, "h": None, "s": None, "v": None, "T": None, "p": None}
    for key in row:
        if key.startswith("u"):
            keys["u"] = key
        elif key.startswith("h"):
            keys["h"] = key
        elif key.startswith("s"):
            keys["s"] = key
        elif key.startswith("v"):
            keys["v"] = key
        elif key.startswith("T_"):
            keys["T"] = key
        elif key.startswith("pressure_"):
            keys["p"] = key
    return keys


def _floatify_row(row):
    # thermo_data already returns floats; this is a no-op for fresh data
    # but retained for safety with any external/legacy data.
    out = {}
    for key, val in row.items():
        if type(val) is float or type(val) is int:
            out[key] = val
        else:
            try:
                out[key] = float(val)
            except:
                out[key] = val
    return out


def _interp_between_rows(x, low_row, high_row, x_key, region_name):
    out = {}
    x_lo = low_row[x_key]
    x_hi = high_row[x_key]
    for key in low_row:
        try:
            out[key] = linear_interpolate(x, x_lo, low_row[key], x_hi, high_row[key])
        except:
            out[key] = low_row[key]
    out["region"] = region_name
    return out


def _lookup_1d(rows, x, x_key, region_name):
    """Interpolate a 1-D table using binary search. Rows need not be pre-sorted."""
    if not rows:
        return None

    x = float(x)
    clean = [r for r in rows if x_key in r]
    if not clean:
        return None
    clean.sort(key=lambda r: float(r[x_key]))

    if x < float(clean[0][x_key]) or x > float(clean[-1][x_key]):
        return None

    lo, hi = 0, len(clean)
    while lo < hi:
        mid = (lo + hi) >> 1
        if float(clean[mid][x_key]) < x:
            lo = mid + 1
        else:
            hi = mid

    if lo < len(clean) and float(clean[lo][x_key]) == x:
        out = _floatify_row(clean[lo].copy())
        out["region"] = region_name
        return out

    if lo == 0 or lo >= len(clean):
        return None

    return _interp_between_rows(x, _floatify_row(clean[lo - 1]), _floatify_row(clean[lo]), x_key, region_name)


def _group_rows_by(rows, group_key):
    groups = {}
    for row in rows:
        g = row.get(group_key)
        if g is None:
            continue
        if g not in groups:
            groups[g] = []
        groups[g].append(row)
    return groups


def _interpolate_candidates_at_fixed_axis(rows, fixed_key, fixed_value, group_key, region_name):
    candidates = []
    groups = _group_rows_by(rows, group_key)
    for _, group_rows in groups.items():
        row = _lookup_1d(group_rows, fixed_value, fixed_key, region_name)
        if row is not None:
            candidates.append(row)
    return candidates


# Alias kept for backward compatibility
_interpolate_candidates_at_fixedAxis = _interpolate_candidates_at_fixed_axis


def _interpolate_from_candidates_by_property(candidates, property_key, target_value, region_name):
    if not candidates:
        return None

    target_value = float(target_value)
    usable = [_floatify_row(r.copy()) for r in candidates if property_key in r]
    if not usable:
        return None
    usable.sort(key=lambda r: float(r[property_key]))

    lo, hi = 0, len(usable)
    while lo < hi:
        mid = (lo + hi) >> 1
        if float(usable[mid][property_key]) < target_value:
            lo = mid + 1
        else:
            hi = mid

    if lo < len(usable) and float(usable[lo][property_key]) == target_value:
        usable[lo]["region"] = region_name
        return usable[lo]

    if lo == 0 or lo >= len(usable):
        return None

    return _interp_between_rows(target_value, usable[lo - 1], usable[lo], property_key, region_name)



def _sat_property_keys(prop_symbol):
    if prop_symbol == "v":
        return "vf_m3_per_kg", "vg_m3_per_kg"
    if prop_symbol == "u":
        return "uf_kJ_per_kg", "ug_kJ_per_kg"
    if prop_symbol == "h":
        return "hf_kJ_per_kg", "hg_kJ_per_kg"
    if prop_symbol == "s":
        return "sf_kJ_per_kg_K", "sg_kJ_per_kg_K"
    raise ValueError("Unknown property symbol.")


def _copy_sat_common_props(out, row, phase_suffix):
    # phase_suffix: "f" for liquid, "g" for vapor
    pairs = [
        ("v_m3_per_kg", "v" + phase_suffix + "_m3_per_kg"),
        ("u_kJ_per_kg", "u" + phase_suffix + "_kJ_per_kg"),
        ("h_kJ_per_kg", "h" + phase_suffix + "_kJ_per_kg"),
        ("s_kJ_per_kg_K", "s" + phase_suffix + "_kJ_per_kg_K"),
        ("v_ft3_per_lb", "v" + phase_suffix + "_ft3_per_lb"),
        ("u_Btu_per_lb", "u" + phase_suffix + "_Btu_per_lb"),
        ("h_Btu_per_lb", "h" + phase_suffix + "_Btu_per_lb"),
        ("s_Btu_per_lb_R", "s" + phase_suffix + "_Btu_per_lb_R"),
        ("s_Btu_per_lbR", "s" + phase_suffix + "_Btu_per_lbR"),
    ]
    for out_key, in_key in pairs:
        if in_key in row:
            out[out_key] = row[in_key]
    return out


def _sat_mixture_from_row(row, prop_symbol, target_value, sat_state=None):
    row = _floatify_row(row)
    sat_state_norm = None if sat_state is None else str(sat_state).strip().lower()

    f_key, g_key = _sat_property_keys_for_row(row, prop_symbol)
    if f_key is None or g_key is None:
        return None

    yf = float(row[f_key])
    yg = float(row[g_key])

    if sat_state_norm in ("liquid", "sat liquid", "saturated liquid", "f"):
        out = row.copy()
        out["quality"] = 0.0
        _copy_sat_common_props(out, row, "f")
        out["region"] = "saturated_liquid"
        return out

    if sat_state_norm in ("vapor", "vapour", "sat vapor", "saturated vapor", "g"):
        out = row.copy()
        out["quality"] = 1.0
        _copy_sat_common_props(out, row, "g")
        out["region"] = "saturated_vapor"
        return out

    if yg == yf:
        return None
    if not (yf <= target_value <= yg):
        return None

    q = (target_value - yf) / (yg - yf)
    out = row.copy()
    out["quality"] = q

    sat_pairs = [
        ("v_m3_per_kg", "vf_m3_per_kg", "vg_m3_per_kg"),
        ("u_kJ_per_kg", "uf_kJ_per_kg", "ug_kJ_per_kg"),
        ("h_kJ_per_kg", "hf_kJ_per_kg", "hg_kJ_per_kg"),
        ("s_kJ_per_kg_K", "sf_kJ_per_kg_K", "sg_kJ_per_kg_K"),
        ("v_ft3_per_lb", "vf_ft3_per_lb", "vg_ft3_per_lb"),
        ("u_Btu_per_lb", "uf_Btu_per_lb", "ug_Btu_per_lb"),
        ("h_Btu_per_lb", "hf_Btu_per_lb", "hg_Btu_per_lb"),
        ("s_Btu_per_lb_R", "sf_Btu_per_lb_R", "sg_Btu_per_lb_R"),
        ("s_Btu_per_lbR", "sf_Btu_per_lbR", "sg_Btu_per_lbR"),
    ]
    for out_key, low_key, high_key in sat_pairs:
        if low_key in row and high_key in row:
            out[out_key] = row[low_key] + q * (row[high_key] - row[low_key])

    out["region"] = "saturated_mixture"
    return out


def _target_property_symbol(h=None, u=None, s=None, v=None):
    props = {"h": h, "u": u, "s": s, "v": v}
    provided = [k for k, val in props.items() if val is not None]
    if len(provided) > 1:
        raise ValueError("Only one of h, u, s, v may be provided.")
    if not provided:
        return None, None
    symbol = provided[0]
    return symbol, float(props[symbol])


def _lookup_non_sat_with_temp(rows, temp_key, temp_value, prop_symbol, prop_value, region_name):
    if not rows:
        return None
    pressure_key = find_property_keys(rows[0])["p"]
    if pressure_key is None:
        return None
    candidates = _interpolate_candidates_at_fixed_axis(
        rows, temp_key, float(temp_value), pressure_key, region_name
    )
    if not candidates:
        return None
    property_key = find_property_keys(candidates[0])[prop_symbol]
    if property_key is None:
        return None
    return _interpolate_from_candidates_by_property(candidates, property_key, float(prop_value), region_name)


def _lookup_non_sat_with_pressure(rows, pressure_value, prop_symbol, prop_value, region_name, temp_key):
    if not rows:
        return None
    pressure_key = find_property_keys(rows[0])["p"]
    if pressure_key is None:
        return None
    candidates = _interpolate_candidates_at_fixed_axis(
        rows, pressure_key, float(pressure_value), temp_key, region_name
    )
    if not candidates:
        return None
    if prop_symbol == "T":
        property_key = temp_key
    else:
        property_key = find_property_keys(candidates[0])[prop_symbol]
        if property_key is None:
            return None
    return _interpolate_from_candidates_by_property(candidates, property_key, float(prop_value), region_name)


_REGION_ALIASES = {
    "sat": "saturated_temperature",
    "saturated": "saturated_temperature",
    "sat_temp": "saturated_temperature",
    "saturated_temperature": "saturated_temperature",
    "sat_pressure": "saturated_pressure",
    "saturated_pressure": "saturated_pressure",
    "superheated": "superheated",
    "compressed": "compressed",
}


def gasLookUp(
    gas_name,
    unit_system,
    temp=None,
    pressure=None,
    region=None,
    h=None,
    u=None,
    s=None,
    v=None,
    sat_state=None
):
    try:
        if is_ideal_gas(gas_name) and not _is_supported_real_fluid_name(gas_name):
            return idealGasLookUp(
                gas_name, unit_system,
                temp=temp, pressure=pressure,
                h=h, u=u, s=s, v=v,
                sat_state=sat_state
            )

        temp = _safe_float(temp)
        pressure = _safe_float(pressure)
        h = _safe_float(h)
        u = _safe_float(u)
        s = _safe_float(s)
        v = _safe_float(v)

        data = get_all_gas_data(gas_name, unit_system)
        temp_key = get_temp_key(unit_system)
        prop_symbol, prop_value = _target_property_symbol(h=h, u=u, s=s, v=v)

        if region is not None:
            region = str(region).strip().lower()
            if region not in _REGION_ALIASES:
                return _error_dict("Unknown region.")
            region = _REGION_ALIASES[region]

        if temp is None and pressure is None and prop_symbol is None:
            return _error_dict("Need at least temp, pressure, or one of h/u/s/v.")

        sat_t_rows = data.get("saturated_temperature", [])
        sat_p_rows = data.get("saturated_pressure", [])
        super_rows = data.get("superheated", [])
        comp_rows = data.get("compressed", [])

        p_key_sat = None
        if sat_p_rows:
            p_key_sat = find_property_keys(sat_p_rows[0])["p"]

        # --- T only ---
        if temp is not None and pressure is None and prop_symbol is None:
            if region is None or region == "saturated_temperature":
                row = _lookup_1d(sat_t_rows, temp, temp_key, "saturated_temperature")
                if row is not None:
                    if sat_state is not None:
                        sat_out = _sat_mixture_from_row(row, "h", float(row[_sat_liquid_key_for_row(row, "h")]), sat_state=sat_state)
                        if sat_out is not None:
                            return sat_out
                        return _error_dict("Could not resolve saturated liquid/vapor state.")
                    return row
            return _error_dict("Could not find a saturated-temperature state for that temperature.")

        # --- P only ---
        if pressure is not None and temp is None and prop_symbol is None:
            if region is None or region == "saturated_pressure":
                row = _lookup_1d(sat_p_rows, pressure, p_key_sat, "saturated_pressure")
                if row is not None:
                    if sat_state is not None:
                        sat_out = _sat_mixture_from_row(row, "h", float(row[_sat_liquid_key_for_row(row, "h")]), sat_state=sat_state)
                        if sat_out is not None:
                            return sat_out
                        return _error_dict("Could not resolve saturated liquid/vapor state.")
                    return row
            return _error_dict("Could not find a saturated-pressure state for that pressure.")

        # --- T and P ---
        if temp is not None and pressure is not None and prop_symbol is None:
            if not sat_p_rows:
                sat_row = None
            else:
                sat_row = _lookup_1d(sat_p_rows, pressure, p_key_sat, "saturated_pressure")
            if sat_row is None:
                row = _lookup_non_sat_with_pressure(super_rows, pressure, "T", temp, "superheated", temp_key)
                if row is not None:
                    return row
                row = _lookup_non_sat_with_pressure(comp_rows, pressure, "T", temp, "compressed", temp_key)
                if row is not None:
                    return row
                return _error_dict("Could not find a state for that temp and pressure.")

            sat_temp_at_p = float(sat_row[temp_key])

            if abs(temp - sat_temp_at_p) < 1e-9:
                if sat_state is not None:
                    sat_out = _sat_mixture_from_row(sat_row, "h", float(sat_row[_sat_liquid_key_for_row(sat_row, "h")]), sat_state=sat_state)
                    if sat_out is not None:
                        return sat_out
                    return _error_dict("Could not resolve saturated liquid/vapor state.")
                out = sat_row.copy()
                out["region"] = "saturated_pressure"
                return out

            if temp > sat_temp_at_p:
                row = _lookup_non_sat_with_pressure(super_rows, pressure, "T", temp, "superheated", temp_key)
                if row is not None:
                    return row
                sat_t_row = _lookup_1d(sat_t_rows, temp, temp_key, "saturated_temperature")
                if sat_t_row is not None:
                    out = sat_t_row.copy()
                    out["region"] = "superheated_approx"
                    _copy_sat_common_props(out, out, "g")
                    if p_key_sat is not None:
                        out[p_key_sat] = pressure
                    return out
                return _error_dict("Could not find a superheated state for that temp and pressure.")

            if temp < sat_temp_at_p:
                row = _lookup_non_sat_with_pressure(comp_rows, pressure, "T", temp, "compressed", temp_key)
                if row is not None:
                    return row
                sat_t_row = _lookup_1d(sat_t_rows, temp, temp_key, "saturated_temperature")
                if sat_t_row is not None:
                    out = sat_t_row.copy()
                    out["region"] = "compressed_approx"
                    _copy_sat_common_props(out, out, "f")
                    if p_key_sat is not None:
                        out[p_key_sat] = pressure
                    return out
                return _error_dict("Could not find a compressed state for that temp and pressure.")

        # --- T + property ---
        if temp is not None and pressure is None and prop_symbol is not None:
            allowed_regions = [region] if region is not None else ["saturated_temperature", "compressed", "superheated"]

            if "saturated_temperature" in allowed_regions:
                sat_row = _lookup_1d(sat_t_rows, temp, temp_key, "saturated_temperature")
                if sat_row is not None:
                    sat_mix = _sat_mixture_from_row(sat_row, prop_symbol, prop_value, sat_state=sat_state)
                    if sat_mix is not None:
                        return sat_mix

            if "compressed" in allowed_regions:
                row = _lookup_non_sat_with_temp(comp_rows, temp_key, temp, prop_symbol, prop_value, "compressed")
                if row is not None:
                    return row

            if "superheated" in allowed_regions:
                row = _lookup_non_sat_with_temp(super_rows, temp_key, temp, prop_symbol, prop_value, "superheated")
                if row is not None:
                    return row

            return _error_dict("No state found from temp plus property.")

        # --- P + property ---
        if pressure is not None and temp is None and prop_symbol is not None:
            allowed_regions = [region] if region is not None else ["saturated_pressure", "compressed", "superheated"]

            if "saturated_pressure" in allowed_regions and sat_p_rows:
                sat_row = _lookup_1d(sat_p_rows, pressure, p_key_sat, "saturated_pressure")
                if sat_row is not None:
                    sat_mix = _sat_mixture_from_row(sat_row, prop_symbol, prop_value, sat_state=sat_state)
                    if sat_mix is not None:
                        return sat_mix

            if "compressed" in allowed_regions:
                row = _lookup_non_sat_with_pressure(comp_rows, pressure, prop_symbol, prop_value, "compressed", temp_key)
                if row is not None:
                    return row

            if "superheated" in allowed_regions:
                row = _lookup_non_sat_with_pressure(super_rows, pressure, prop_symbol, prop_value, "superheated", temp_key)
                if row is not None:
                    return row

            return _error_dict("No state found from pressure plus property.")

        # --- T + P + property (consistency check) ---
        if temp is not None and pressure is not None and prop_symbol is not None:
            state_row = gasLookUp(
                gas_name=gas_name, unit_system=unit_system,
                temp=temp, pressure=pressure,
                region=region, sat_state=sat_state
            )
            if _is_error(state_row):
                return state_row

            keys = find_property_keys(state_row)
            prop_key = keys.get(prop_symbol)
            if prop_key is not None and prop_key in state_row:
                try:
                    if abs(float(state_row[prop_key]) - float(prop_value)) < 1e-6:
                        return state_row
                except:
                    pass

            if state_row.get("region") in (
                "saturated_pressure", "saturated_temperature",
                "saturated_mixture", "saturated_liquid", "saturated_vapor"
            ):
                sat_mix = _sat_mixture_from_row(state_row, prop_symbol, prop_value, sat_state=sat_state)
                if sat_mix is not None:
                    return sat_mix

            return _error_dict("Inputs are inconsistent for the resolved state.")

        if temp is None and pressure is None and prop_symbol is not None:
            return _error_dict("A single property alone is not enough to determine state.")

        return _error_dict("Unsupported input combination.")

    except:
        return _error_dict("Lookup failed.")


def get_property(
    gas_name,
    unit_system,
    property_name,
    temp=None,
    pressure=None,
    region=None,
    h=None,
    u=None,
    s=None,
    v=None,
    sat_state=None
):
    try:
        requested = str(property_name).strip().lower()

        property_aliases = {
            "temperature": ("t", "temp", "temperature"),
            "pressure": ("p", "pressure"),
            "v": ("v", "specific volume", "volume"),
            "u": ("u", "internal energy"),
            "h": ("h", "enthalpy"),
            "s": ("s", "entropy"),
            "quality": ("q", "x", "quality"),
        }

        canonical_request = None
        for key, aliases in property_aliases.items():
            if requested in aliases:
                canonical_request = key
                break

        if canonical_request is None:
            return None

        row = gasLookUp(
            gas_name=gas_name, unit_system=unit_system,
            temp=temp, pressure=pressure, region=region,
            h=h, u=u, s=s, v=v, sat_state=sat_state
        )

        if row is None or _is_error(row):
            return None

        if canonical_request == "temperature":
            for key in row:
                if key.startswith("T_"):
                    return row[key]
            return None

        if canonical_request == "pressure":
            for key in row:
                if key.startswith("pressure_"):
                    return row[key]
            return None

        if canonical_request == "quality":
            return row.get("quality")

        direct_keys = {
            "v": "v_m3_per_kg",
            "u": "u_kJ_per_kg",
            "h": "h_kJ_per_kg",
            "s": "s_kJ_per_kg_K",
        }

        direct_key = direct_keys[canonical_request]
        if direct_key in row:
            return row[direct_key]

        if "quality" in row:
            q = row["quality"]
            sat_keys = {
                "v": ("vf_m3_per_kg", "vg_m3_per_kg"),
                "u": ("uf_kJ_per_kg", "ug_kJ_per_kg"),
                "h": ("hf_kJ_per_kg", "hg_kJ_per_kg"),
                "s": ("sf_kJ_per_kg_K", "sg_kJ_per_kg_K"),
            }
            f_key, g_key = sat_keys[canonical_request]
            if f_key in row and g_key in row:
                return row[f_key] + q * (row[g_key] - row[f_key])

        return None

    except:
        return None


# =========================================================
# STATE RESOLUTION AFTER SOLVING h
# =========================================================

def resolve_state_from_constraints(
    fluid,
    unit_system,
    solved_h=None,
    descriptor=None,
    temp=None,
    pressure=None
):
    if descriptor in ("saturated liquid", "saturated vapor") and not is_ideal_gas(fluid):
        if temp not in (None, 0):
            row = gasLookUp(fluid, unit_system, temp=temp, sat_state=descriptor)
        elif pressure not in (None, 0):
            row = gasLookUp(fluid, unit_system, pressure=pressure, sat_state=descriptor)
        else:
            return _error_dict("Need T or P for saturated state resolution.")
        if _is_error(row):
            return row
        return row

    if temp not in (None, 0) and pressure not in (None, 0):
        row = gasLookUp(fluid, unit_system, temp=temp, pressure=pressure)
        if _is_error(row):
            return row
        return row

    if temp not in (None, 0) and solved_h is not None:
        row = gasLookUp(fluid, unit_system, temp=temp, h=solved_h)
        if _is_error(row):
            return row
        return row

    if pressure not in (None, 0) and solved_h is not None:
        row = gasLookUp(fluid, unit_system, pressure=pressure, h=solved_h)
        if _is_error(row):
            return row
        return row

    return _error_dict("Not enough information to resolve full state.")


def state_summary_lines(state_name, row):
    if row is None or _is_error(row):
        return [state_name + ": unavailable"]

    lines = [state_name + ":"]
    if "region" in row:
        lines.append("region = " + str(row["region"]))
    if "quality" in row:
        lines.append("quality = " + str(row["quality"]))

    for key in (
        "T_K", "T_R", "T_C", "T_F",
        "pressure_bar", "pressure_psia",
        "h_kJ_per_kg", "u_kJ_per_kg",
        "s_kJ_per_kg_K", "s0_kJ_per_kg_K", "v_m3_per_kg"
    ):
        if key in row:
            lines.append(key + " = " + str(row[key]))

    return lines



# =========================================================
# SHARED INPUT / SOLVER HELPERS
# =========================================================

def _prompt_yes_no(title):
    lines = [
        title,
        "",
        "1. Yes",
        "2. No",
    ]
    choice = paged_choice(lines, ["1", "2"])
    if choice == GO_BACK:
        return GO_BACK
    return choice == "1"


def safe_input_unknown_float(prompt):
    while True:
        raw = input(prompt).strip()
        nav = _handle_global_nav(raw)
        if nav == GO_BACK:
            return GO_BACK
        if nav == QUIT_CANCELLED:
            continue

        if raw == "" or raw.lower() == "u":
            return None

        try:
            return float(raw)
        except:
            print("Enter a number or u for unknown.")


def safe_input_optional_unknown_float(prompt, blank_value=None):
    while True:
        raw = input(prompt).strip()
        nav = _handle_global_nav(raw)
        if nav == GO_BACK:
            return GO_BACK
        if nav == QUIT_CANCELLED:
            continue

        if raw == "":
            return blank_value
        if raw.lower() == "u":
            return None

        try:
            return float(raw)
        except:
            print("Enter a number, u for unknown, or blank for default.")


def _close_enough(a, b, tol=1e-5):
    if a is None or b is None:
        return True
    scale = max(1.0, abs(float(a)), abs(float(b)))
    return abs(float(a) - float(b)) <= tol * scale

# =========================================================
# TI-NSPIRE DISPLAY / MENU SECTION
# =========================================================

def quit_app():
    clear_screen()
    print_padded_page(["Quit Thermo?", "", "1. Yes", "2. No"], MAX_LINES)
    choice = input("Option: ").strip().lower()
    if choice in ("1", "y", "yes", "q"):
        raise SystemExit
    return None


def _handle_global_nav(value):
    v = str(value).strip().lower()
    if v == "q":
        quit_app()
        return QUIT_CANCELLED
    if v == "b":
        return GO_BACK
    return None


def clear_screen():
    # TI-Nspire shell has no true clear-screen.
    # Too many blank lines can leave stray prompts visible.
    print(" ")
    print(" ")


def wait_for_enter(message="Press Enter..."):
    value = input(message).strip()
    nav = _handle_global_nav(value)
    if nav == GO_BACK:
        return GO_BACK
    if nav == QUIT_CANCELLED:
        return QUIT_CANCELLED
    return None


def split_pages(lines, max_lines=MAX_LINES):
    pages = []
    current = []
    for line in lines:
        current.append(str(line))
        if len(current) >= max_lines:
            pages.append(current)
            current = []
    if current:
        pages.append(current)
    if not pages:
        pages = [[]]
    return pages


def print_padded_page(page_lines, max_lines):
    count = 0
    for line in page_lines:
        print(line)
        count += 1
    while count < max_lines:
        print(" ")
        count += 1


def show_page_lines(lines, page_index=0, max_lines=MAX_LINES, show_back=False):
    pages = split_pages(lines, max_lines=max_lines)
    if page_index < 0:
        page_index = 0
    if page_index >= len(pages):
        page_index = len(pages) - 1

    clear_screen()
    print_padded_page(pages[page_index], max_lines)

    footer = []
    if len(pages) > 1 and page_index < len(pages) - 1:
        footer.append(NEXT_PAGE_OPTION + ". Next")
    if len(pages) > 1 and page_index > 0:
        footer.append(PREV_PAGE_OPTION + ". Prev")
    if show_back:
        footer.append(BACK_OPTION + ". Menu")
    footer.append("b. Back   q. Quit")
    print("   ".join(footer))
    return len(pages), page_index


def paged_choice(lines, valid_options, max_lines=MAX_LINES, show_back=False):
    page_index = 0
    while True:
        page_count, page_index = show_page_lines(
            lines, page_index=page_index,
            max_lines=max_lines, show_back=show_back
        )
        choice = input("Option: ").strip()
        nav = _handle_global_nav(choice)
        if nav == GO_BACK:
            return GO_BACK
        if nav == QUIT_CANCELLED:
            continue
        if nav == QUIT_CANCELLED:
            continue

        if page_count > 1 and choice == NEXT_PAGE_OPTION and page_index < page_count - 1:
            page_index += 1
            continue
        if page_count > 1 and choice == PREV_PAGE_OPTION and page_index > 0:
            page_index -= 1
            continue
        if show_back and choice == BACK_OPTION:
            return BACK_OPTION
        if choice in valid_options:
            return choice

        clear_screen()
        print("Invalid option.")
        nav = wait_for_enter()
        if nav == GO_BACK:
            return GO_BACK
        if nav == QUIT_CANCELLED:
            continue
        if nav == QUIT_CANCELLED:
            continue


def safe_input_float(prompt, allow_blank=True, blank_value=None):
    while True:
        raw = input(prompt).strip()
        nav = _handle_global_nav(raw)
        if nav == GO_BACK:
            return GO_BACK
        if nav == QUIT_CANCELLED:
            continue

        if raw == "":
            if allow_blank:
                return blank_value
            print("Input required.")
            continue

        try:
            return float(raw)
        except:
            print("Enter a valid number.")


def display_message(lines, max_lines=MAX_LINES):
    pages = split_pages(lines, max_lines=max_lines)
    page_index = 0
    while True:
        clear_screen()
        print_padded_page(pages[page_index], max_lines)

        if len(pages) > 1:
            if page_index < len(pages) - 1:
                prompt = "Enter=Next b=Back q=Quit: "
            else:
                prompt = "Enter=Done b=Back q=Quit: "
        else:
            prompt = "Enter=Done b=Back q=Quit: "

        choice = input(prompt).strip()
        nav = _handle_global_nav(choice)
        if nav == QUIT_CANCELLED:
            continue

        if choice == "":
            if page_index < len(pages) - 1:
                page_index += 1
                continue
            return None

        if nav == GO_BACK:
            if page_index > 0:
                page_index -= 1
                continue
            return GO_BACK

        print("Press Enter.")
        nav = wait_for_enter()
        if nav == GO_BACK:
            if page_index > 0:
                page_index -= 1
                continue
            return GO_BACK
        if nav == QUIT_CANCELLED:
            continue


# =========================================================
# DISPLAY FORMATTING HELPERS
# =========================================================

def _display_number(value):
    if type(value) is int:
        return str(value)
    if type(value) is float:
        return ("%.6g" % value)
    try:
        f = float(value)
        return ("%.6g" % f)
    except:
        return str(value)


_DISPLAY_KEY_MAP = {
    "region": ("region", ""),
    "quality": ("q", ""),
    "ideal_gas": ("ideal gas", ""),
    "note": ("note", ""),

    "T_C": ("T", "C"),
    "T_F": ("T", "F"),
    "T_K": ("T", "K"),
    "T_R": ("T", "R"),

    "pressure_bar": ("P", "bar"),
    "pressure_psia": ("P", "psia"),
    "pressure_lbf_per_in2": ("P", "psia"),

    "v_m3_per_kg": ("v", "m^3/kg"),
    "u_kJ_per_kg": ("u", "kJ/kg"),
    "h_kJ_per_kg": ("h", "kJ/kg"),
    "s_kJ_per_kg_K": ("s", "kJ/(kg*K)"),
    "s0_kJ_per_kg_K": ("s0", "kJ/(kg*K)"),

    "v_ft3_per_lb": ("v", "ft^3/lbm"),
    "u_Btu_per_lb": ("u", "Btu/lbm"),
    "h_Btu_per_lb": ("h", "Btu/lbm"),
    "s_Btu_per_lb_R": ("s", "Btu/(lbm*R)"),
    "s_Btu_per_lbR": ("s", "Btu/(lbm*R)"),
    "s0_Btu_per_lbR": ("s0", "Btu/(lbm*R)"),

    "R_kJ_per_kg_K": ("R", "kJ/(kg*K)"),
    "R_Btu_per_lb_R": ("R", "Btu/(lbm*R)"),
    "cp_kJ_per_kg_K": ("cp", "kJ/(kg*K)"),
    "cp_Btu_per_lb_R": ("cp", "Btu/(lbm*R)"),
    "k": ("k", ""),
    "pr": ("pr", ""),
    "vr": ("vr", ""),
}


def _display_name_unit(key):
    if key in _DISPLAY_KEY_MAP:
        return _DISPLAY_KEY_MAP[key]

    sat_si = {
        "vf_m3_per_kg": ("vf", "m^3/kg"),
        "vg_m3_per_kg": ("vg", "m^3/kg"),
        "uf_kJ_per_kg": ("uf", "kJ/kg"),
        "ug_kJ_per_kg": ("ug", "kJ/kg"),
        "hf_kJ_per_kg": ("hf", "kJ/kg"),
        "hg_kJ_per_kg": ("hg", "kJ/kg"),
        "hfg_kJ_per_kg": ("hfg", "kJ/kg"),
        "sf_kJ_per_kg_K": ("sf", "kJ/(kg*K)"),
        "sg_kJ_per_kg_K": ("sg", "kJ/(kg*K)"),
    }
    if key in sat_si:
        return sat_si[key]

    sat_en = {
        "vf_ft3_per_lb": ("vf", "ft^3/lbm"),
        "vg_ft3_per_lb": ("vg", "ft^3/lbm"),
        "uf_Btu_per_lb": ("uf", "Btu/lbm"),
        "ug_Btu_per_lb": ("ug", "Btu/lbm"),
        "hf_Btu_per_lb": ("hf", "Btu/lbm"),
        "hg_Btu_per_lb": ("hg", "Btu/lbm"),
        "hfg_Btu_per_lb": ("hfg", "Btu/lbm"),
        "sf_Btu_per_lb_R": ("sf", "Btu/(lbm*R)"),
        "sg_Btu_per_lb_R": ("sg", "Btu/(lbm*R)"),
        "sf_Btu_per_lbR": ("sf", "Btu/(lbm*R)"),
        "sg_Btu_per_lbR": ("sg", "Btu/(lbm*R)"),
    }
    if key in sat_en:
        return sat_en[key]

    return key, ""


def _display_line(key, value):
    name, unit = _display_name_unit(key)
    value_text = "u" if value is None else _display_number(value)
    if unit and value_text != "u":
        return name + " = " + value_text + " " + unit
    return name + " = " + value_text


def _result_unit_mode(result):
    if result.get("_display_unit_system") == "English":
        return "english"
    if result.get("_display_unit_system") == "SI":
        return "metric"

    english_markers = [
        "T_F", "pressure_psia", "pressure_lbf_per_in2",
        "h_Btu_per_lb", "hf_Btu_per_lb", "u_Btu_per_lb",
        "v_ft3_per_lb", "s_Btu_per_lb_R", "s_Btu_per_lbR",
    ]
    for key in english_markers:
        if key in result:
            return "english"
    return "metric"


def _preferred_display_keys(result):
    mode = _result_unit_mode(result)
    if mode == "english":
        return (
            "region", "quality",
            "T_R" if result.get("ideal_gas") else "T_F",
            "pressure_psia", "pressure_lbf_per_in2",
            "v_ft3_per_lb", "u_Btu_per_lb", "h_Btu_per_lb", "s_Btu_per_lb_R", "s_Btu_per_lbR",
            "vf_ft3_per_lb", "vg_ft3_per_lb",
            "uf_Btu_per_lb", "ug_Btu_per_lb",
            "hf_Btu_per_lb", "hfg_Btu_per_lb", "hg_Btu_per_lb",
            "sf_Btu_per_lb_R", "sg_Btu_per_lb_R", "sf_Btu_per_lbR", "sg_Btu_per_lbR",
            "s0_Btu_per_lbR", "R_Btu_per_lb_R", "cp_Btu_per_lb_R", "k", "pr", "vr",
        )
    return (
        "region", "quality",
        "T_K" if result.get("ideal_gas") else "T_C",
        "pressure_bar",
        "v_m3_per_kg", "u_kJ_per_kg", "h_kJ_per_kg", "s_kJ_per_kg_K",
        "vf_m3_per_kg", "vg_m3_per_kg",
        "uf_kJ_per_kg", "ug_kJ_per_kg",
        "hf_kJ_per_kg", "hfg_kJ_per_kg", "hg_kJ_per_kg",
        "sf_kJ_per_kg_K", "sg_kJ_per_kg_K",
        "s0_kJ_per_kg_K", "R_kJ_per_kg_K", "cp_kJ_per_kg_K", "k", "pr", "vr",
    )


def _should_hide_extra_key(key, mode):
    if key.startswith("_"):
        return True
    if mode == "english":
        return (
            key.endswith("_kJ_per_kg") or
            key.endswith("_kJ_per_kg_K") or
            key in ("T_C", "T_K", "pressure_bar", "v_m3_per_kg")
        )
    return (
        key.endswith("_Btu_per_lb") or
        key.endswith("_Btu_per_lb_R") or
        key.endswith("_Btu_per_lbR") or
        key.endswith("_ft3_per_lb") or
        key in ("T_F", "T_R", "pressure_psia", "pressure_lbf_per_in2")
    )


def result_dict_display_lines(result):
    if result is None:
        return ["No result found."]
    if _is_error(result):
        return ["Error:", str(result["error"])]

    mode = _result_unit_mode(result)
    preferred = _preferred_display_keys(result)
    preferred_set = frozenset(preferred)

    display_items = []
    for key in preferred:
        if key in result:
            display_items.append((result[key] is None, _display_line(key, result[key])))

    for key in result:
        if key not in preferred_set and not _should_hide_extra_key(key, mode):
            display_items.append((result[key] is None, _display_line(key, result[key])))

    lines = [line for is_unknown, line in display_items if not is_unknown]
    lines.extend([line for is_unknown, line in display_items if is_unknown])
    return lines


def display_result_dict(result, max_lines=MAX_LINES):
    lines = result_dict_display_lines(result)
    return display_message(lines, max_lines=max_lines)


def _history_unit_name(unit_system):
    return "Metric" if _unit_system_key(unit_system) == "metric" else "English"


def _history_fluid_name(fluid):
    text = str(fluid).strip()
    if not text:
        return text
    return text[:1].upper() + text[1:]


def _history_add(lines):
    HISTORY.insert(0, [str(line) for line in lines])


def _history_value_line(label, value, unit=""):
    if value is None:
        return None
    if unit:
        return label + " = " + _display_number(value) + " " + unit
    return label + " = " + _display_number(value)


def _lookup_input_unit(symbol, unit_system):
    if symbol == "T":
        return "C" if _unit_system_key(unit_system) == "metric" else "F"
    if symbol == "P":
        return "bar" if _unit_system_key(unit_system) == "metric" else "psia"
    if symbol in ("h", "u"):
        return "kJ/kg" if _unit_system_key(unit_system) == "metric" else "Btu/lbm"
    if symbol == "s":
        return "kJ/(kg*K)" if _unit_system_key(unit_system) == "metric" else "Btu/(lbm*R)"
    if symbol == "v":
        return "m^3/kg" if _unit_system_key(unit_system) == "metric" else "ft^3/lbm"
    return ""


def _history_record_lookup(title, fluid, unit_system, given, result):
    if result is None or _is_error(result):
        return

    lines = [
        title,
        _history_fluid_name(fluid) + ", " + _history_unit_name(unit_system),
    ]
    if "region" in result:
        lines.append("State: " + str(result["region"]))
    lines.extend(["", "Given:"])

    any_given = False
    for label, value, unit in given:
        item = _history_value_line(label, value, unit)
        if item is not None:
            lines.append(item)
            any_given = True
    if not any_given:
        lines.append("None")

    lines.extend(["", "Found:"])
    for line in result_dict_display_lines(result):
        lines.append(line)

    _history_add(lines)



def history_menu():
    if not HISTORY:
        return display_message(["History", "", "No history yet."])

    entry_index = 0
    page_index = 0
    while True:
        history_content_lines = MAX_LINES - 1
        entry_pages = split_pages(HISTORY[entry_index], max_lines=history_content_lines)
        if page_index < 0:
            page_index = 0
        if page_index >= len(entry_pages):
            page_index = len(entry_pages) - 1

        clear_screen()
        print(
            "Entry (" + str(entry_index + 1) + "/" + str(len(HISTORY)) + ") " +
            "Page (" + str(page_index + 1) + "/" + str(len(entry_pages)) + ")"
        )
        print_padded_page(entry_pages[page_index], history_content_lines)

        footer = []
        if page_index < len(entry_pages) - 1 or entry_index < len(HISTORY) - 1:
            footer.append(NEXT_PAGE_OPTION + ". Next")
        if page_index > 0 or entry_index > 0:
            footer.append(PREV_PAGE_OPTION + ". Prev")
        if entry_index < len(HISTORY) - 1:
            footer.append("e. Next entry")
        if entry_index > 0:
            footer.append("d. Prev entry")
        footer.append("b. Back   q. Quit")
        prompt = "Option (" + "   ".join(footer) + "): "

        choice = input(prompt).strip()
        nav = _handle_global_nav(choice)
        if nav == GO_BACK:
            return GO_BACK
        if choice.lower() == "e" and entry_index < len(HISTORY) - 1:
            entry_index += 1
            page_index = 0
            continue
        if choice.lower() == "d" and entry_index > 0:
            entry_index -= 1
            page_index = 0
            continue
        if choice == NEXT_PAGE_OPTION:
            if page_index < len(entry_pages) - 1:
                page_index += 1
                continue
            if entry_index < len(HISTORY) - 1:
                entry_index += 1
                page_index = 0
                continue
        if choice == PREV_PAGE_OPTION:
            if page_index > 0:
                page_index -= 1
                continue
            if entry_index > 0:
                entry_index -= 1
                page_index = len(split_pages(HISTORY[entry_index], max_lines=history_content_lines)) - 1
                continue
        if choice == "":
            if page_index < len(entry_pages) - 1:
                page_index += 1
                continue
            if entry_index < len(HISTORY) - 1:
                entry_index += 1
                page_index = 0
                continue
            return None

        print("Invalid option.")
        nav = wait_for_enter()
        if nav == GO_BACK:
            return GO_BACK


def prompt_fluid(fluids=None):
    if fluids is None:
        fluids = SUPPORTED_FLUIDS

    lines = ["Select Fluid", ""]
    for i, fluid in enumerate(fluids, start=1):
        lines.append(str(i) + ". " + fluid)

    choice = paged_choice(lines, [str(i) for i in range(1, len(fluids) + 1)])
    if choice == GO_BACK:
        return GO_BACK
    return fluids[int(choice) - 1].lower()


def prompt_unit_system():
    lines = [
        "Select Unit System",
        "",
        "1. SI / Metric",
        "2. English / Imperial",
    ]
    choice = paged_choice(lines, ["1", "2"])
    if choice == GO_BACK:
        return GO_BACK
    if choice == "1":
        return "SI"
    return "English"


def prompt_fluid_and_unit():
    fluid = prompt_fluid()
    if fluid == GO_BACK:
        return None, None, GO_BACK
    unit_system = prompt_unit_system()
    if unit_system == GO_BACK:
        return None, None, GO_BACK
    return fluid, unit_system, None


def _prompt_property_value():
    lines = [
        "Select Known Property",
        "",
        "1. h",
        "2. u",
        "3. s",
        "4. v",
    ]
    choice = paged_choice(lines, ["1", "2", "3", "4"])
    if choice == GO_BACK:
        return None, None, GO_BACK

    symbols = {"1": "h", "2": "u", "3": "s", "4": "v"}
    symbol = symbols[choice]
    value = safe_input_float("Enter " + symbol + ": ", allow_blank=False)
    if value == GO_BACK:
        return None, None, GO_BACK
    return symbol, value, None


def _prop_kwargs(symbol, value):
    out = {"h": None, "u": None, "s": None, "v": None}
    if symbol in out:
        out[symbol] = value
    return out



def _property_unit_label(symbol, unit_system):
    if _unit_system_key(unit_system) == "metric":
        if symbol in ("h", "u"):
            return "kJ/kg"
        if symbol == "s":
            return "kJ/(kg*K)"
        if symbol == "v":
            return "m^3/kg"
    else:
        if symbol in ("h", "u"):
            return "Btu/lbm"
        if symbol == "s":
            return "Btu/(lbm*R)"
        if symbol == "v":
            return "ft^3/lbm"
    return ""


def _prompt_property_value_with_units(unit_system):
    lines = [
        "Select Known Property",
        "",
        "1. h",
        "2. u",
        "3. s",
        "4. v",
    ]
    choice = paged_choice(lines, ["1", "2", "3", "4"])
    if choice == GO_BACK:
        return None, None, GO_BACK

    symbols = {"1": "h", "2": "u", "3": "s", "4": "v"}
    symbol = symbols[choice]
    unit_label = _property_unit_label(symbol, unit_system)
    value = safe_input_float("Enter " + symbol + " (" + unit_label + "): ", allow_blank=False)
    if value == GO_BACK:
        return None, None, GO_BACK
    return symbol, value, None


def _prompt_sat_state():
    lines = [
        "Saturated State?",
        "",
        "1. None / Auto",
        "2. Saturated liquid",
        "3. Saturated vapor",
        "4. Quality (x)",
    ]
    choice = paged_choice(lines, ["1", "2", "3", "4"])
    if choice == GO_BACK:
        return None, None, GO_BACK
    if choice == "2":
        return "saturated liquid", None, None
    if choice == "3":
        return "saturated vapor", None, None
    if choice == "4":
        quality = safe_input_float("Enter x (0 to 1): ", allow_blank=False)
        if quality == GO_BACK:
            return None, None, GO_BACK
        if quality < 0.0 or quality > 1.0:
            return None, None, _error_dict("Quality must be between 0 and 1.")
        return None, quality, None
    return None, None, None


def _quality_kwargs_from_sat(fluid, unit_system, temp=None, pressure=None, quality=None):
    if quality is None:
        return {"h": None, "u": None, "s": None, "v": None}

    row = None
    if temp is not None:
        row = gasLookUp(fluid, unit_system, temp=temp)
    elif pressure is not None:
        row = gasLookUp(fluid, unit_system, pressure=pressure)

    if row is None or _is_error(row):
        return row

    f_key, g_key = _sat_property_keys_for_row(row, "h")
    if f_key is None or g_key is None:
        return _error_dict("Could not resolve quality from this saturated state.")

    h_value = float(row[f_key]) + float(quality) * (float(row[g_key]) - float(row[f_key]))
    return {"h": h_value, "u": None, "s": None, "v": None}


def _ideal_change_pressure_unit(unit_system):
    return "bar" if _unit_system_key(unit_system) == "metric" else "psia"


def _ideal_change_volume_unit(unit_system):
    return "m^3" if _unit_system_key(unit_system) == "metric" else "ft^3"


def _ideal_change_mass_unit(unit_system):
    return "kg" if _unit_system_key(unit_system) == "metric" else "lbm"


def _ideal_change_temp_unit(unit_system):
    return "K" if _unit_system_key(unit_system) == "metric" else "R"


def _ideal_change_to_si(key, value, unit_system):
    if value is None:
        return None
    x = float(value)
    mode = _unit_system_key(unit_system)
    if key.startswith("P"):
        if mode == "metric":
            return x * 100.0
        return (x / PSIA_PER_BAR) * 100.0
    if key.startswith("V"):
        if mode == "metric":
            return x
        return x * 0.028316846592
    if key.startswith("m"):
        if mode == "metric":
            return x
        return x * 0.45359237
    if key.startswith("T"):
        if mode == "metric":
            return x
        return x * 5.0 / 9.0
    return x


def _ideal_change_from_si(key, value, unit_system):
    if value is None:
        return None
    x = float(value)
    mode = _unit_system_key(unit_system)
    if key.startswith("P"):
        if mode == "metric":
            return x / 100.0
        return (x / 100.0) * PSIA_PER_BAR
    if key.startswith("V"):
        if mode == "metric":
            return x
        return x / 0.028316846592
    if key.startswith("m"):
        if mode == "metric":
            return x
        return x / 0.45359237
    if key.startswith("T"):
        if mode == "metric":
            return x
        return x * 9.0 / 5.0
    return x


def _ideal_change_display_value(key, value, unit_system):
    if value is None:
        return key + " = u"
    if key.startswith("T"):
        t = float(value)
        if _unit_system_key(unit_system) == "metric":
            return key + " = " + _display_number(t - 273.15) + " C = " + _display_number(t) + " K"
        return key + " = " + _display_number(t - 459.67) + " F = " + _display_number(t) + " R"
    if key.startswith("P"):
        p = float(value)
        if _unit_system_key(unit_system) == "metric":
            return key + " = " + _display_number(p) + " bar = " + _display_number(p * 100.0) + " kPa"
        return key + " = " + _display_number(p) + " psia = " + _display_number(p / PSIA_PER_BAR) + " bar"
    if key.startswith("V"):
        return key + " = " + _display_number(value) + " " + _ideal_change_volume_unit(unit_system)
    if key.startswith("m"):
        return key + " = " + _display_number(value) + " " + _ideal_change_mass_unit(unit_system)
    return key + " = " + _display_number(value)


def _ideal_change_entropy_unit(unit_system):
    if _unit_system_key(unit_system) == "metric":
        return "kJ/(kg*K)"
    return "Btu/(lbm*R)"


def _ideal_change_gas_label(gas):
    key = _canonical_ideal_gas_key(gas)
    return IDEAL_GAS_LABELS.get(key, str(gas))


def _ideal_change_cp_coeffs(gas):
    key = _canonical_ideal_gas_key(gas)
    if key == "helium":
        return None
    corrected = {
        "air": (3.653, -1.337, 3.294, -1.913, 0.2763),
        "n2": (3.626, -1.878, 7.055, -6.764, 2.156),
        "o2": (3.675, -1.208, 2.324, -0.632, -0.226),
        "co2": (2.401, 8.735, -6.607, 2.002, 0.0),
        "co": (3.71, -1.619, 3.692, -2.032, 0.24),
        "h2o": (4.07, -1.108, 4.152, -2.964, 0.807),
        "h2": (3.057, 2.677, -5.810, 5.521, -1.812),
        "so2": (3.267, 5.324, 0.684, -5.281, 2.559),
        "ch4": (3.826, -3.979, 24.558, -22.733, 6.963),
        "c2h2": (1.410, 19.057, -24.501, 16.391, -4.135),
        "c2h4": (1.426, 11.383, -7.989, 16.254, -6.749),
    }
    if key in corrected:
        a, b, c, d, e = corrected[key]
        return (a, b * 1e-3, c * 1e-6, d * 1e-9, e * 1e-12)
    target_label = _ideal_change_gas_label(key).lower()
    try:
        rows = row_dicts("page_38_variation_of_cp_selected_ideal_gases", unit_system="metric")
    except:
        return None
    for row in rows:
        row_gas = _canonical_ideal_gas_key(row.get("gas", ""))
        if row_gas == key or str(row.get("gas", "")).strip().lower() == target_label:
            return (
                float(row["a"]),
                float(row["b_x10^-3"]) * 1e-3,
                float(row["c_x10^-6"]) * 1e-6,
                float(row["d_x10^-9"]) * 1e-9,
                float(row["e_x10^-12"]) * 1e-12,
            )
    return None


def _ideal_change_cp_over_t_integral(gas, t1, t2):
    r = _ideal_gas_R(gas)
    if r is None or t1 is None or t2 is None or t1 <= 0.0 or t2 <= 0.0:
        return None
    if _canonical_ideal_gas_key(gas) == "helium":
        return 2.5 * r * math.log(float(t2) / float(t1))

    coeffs = _ideal_change_cp_coeffs(gas)
    if coeffs is None:
        return None
    a, b, c, d, e = coeffs
    t1 = float(t1)
    t2 = float(t2)
    integral_over_r = (
        a * math.log(t2 / t1) +
        b * (t2 - t1) +
        0.5 * c * (t2 * t2 - t1 * t1) +
        (d / 3.0) * (t2 ** 3 - t1 ** 3) +
        0.25 * e * (t2 ** 4 - t1 ** 4)
    )
    return r * integral_over_r


def _ideal_change_delta_s_si(gas, t1, p1, t2, p2):
    if None in (t1, p1, t2, p2):
        return None
    if min(float(t1), float(t2), float(p1), float(p2)) <= 0.0:
        return None
    cp_part = _ideal_change_cp_over_t_integral(gas, float(t1), float(t2))
    r = _ideal_gas_R(gas)
    if cp_part is None or r is None:
        return None
    return cp_part - r * math.log(float(p2) / float(p1))


def _ideal_change_delta_s_display(value_si, unit_system):
    if value_si is None:
        return None
    if _unit_system_key(unit_system) == "metric":
        return float(value_si)
    return float(value_si) * BTU_PER_LBM_R_PER_KJ_PER_KG_K


def _ideal_change_delta_S_display(value_si, unit_system):
    if value_si is None:
        return None
    if _unit_system_key(unit_system) == "metric":
        return float(value_si)
    return float(value_si) * 0.9478171203133172


def _ideal_change_delta_S_unit(unit_system):
    if _unit_system_key(unit_system) == "metric":
        return "kJ/K"
    return "Btu/R"


def _ideal_change_mass_for_delta_S(values):
    m1 = values.get("m1")
    m2 = values.get("m2")
    if m1 is not None and m2 is not None:
        if _close_enough(m1, m2):
            return float(m1)
        return None
    if m1 is not None:
        return float(m1)
    if m2 is not None:
        return float(m2)
    return None


def _ideal_change_solve_state(values, state_num, r):
    keys = ["P" + state_num, "V" + state_num, "m" + state_num, "T" + state_num]
    missing = [key for key in keys if values.get(key) is None]
    if len(missing) != 1:
        return False
    p = values.get("P" + state_num)
    v = values.get("V" + state_num)
    m = values.get("m" + state_num)
    t = values.get("T" + state_num)
    miss = missing[0]
    try:
        if miss.startswith("P") and None not in (v, m, t) and v != 0.0:
            values[miss] = m * r * t / v
            return True
        if miss.startswith("V") and None not in (p, m, t) and p != 0.0:
            values[miss] = m * r * t / p
            return True
        if miss.startswith("m") and None not in (p, v, t) and r * t != 0.0:
            values[miss] = p * v / (r * t)
            return True
        if miss.startswith("T") and None not in (p, v, m) and m * r != 0.0:
            values[miss] = p * v / (m * r)
            return True
    except:
        return False
    return False


def _ideal_change_apply_constant(values, constant):
    changed = False
    if constant in ("V", "P", "T"):
        key1 = constant + "1"
        key2 = constant + "2"
        v1 = values.get(key1)
        v2 = values.get(key2)
        if v1 is not None and v2 is None:
            values[key2] = v1
            changed = True
        elif v2 is not None and v1 is None:
            values[key1] = v2
            changed = True
    return changed


def _ideal_change_solve_product_relation(values, left_keys, right_keys):
    all_keys = list(left_keys) + list(right_keys)
    missing = [key for key in all_keys if values.get(key) is None]
    if len(missing) != 1:
        return False
    missing_key = missing[0]
    left_known = 1.0
    right_known = 1.0
    try:
        for key in left_keys:
            if key != missing_key:
                left_known *= float(values[key])
        for key in right_keys:
            if key != missing_key:
                right_known *= float(values[key])
        if missing_key in left_keys and left_known != 0.0:
            values[missing_key] = right_known / left_known
            return True
        if missing_key in right_keys and right_known != 0.0:
            values[missing_key] = left_known / right_known
            return True
    except:
        return False
    return False


def _ideal_change_apply_simple_relation(values, constant):
    if constant == "V":
        return _ideal_change_solve_product_relation(
            values, ["P1", "m2", "T2"], ["P2", "m1", "T1"]
        )
    if constant == "P":
        return _ideal_change_solve_product_relation(
            values, ["V1", "m2", "T2"], ["V2", "m1", "T1"]
        )
    if constant == "T":
        return _ideal_change_solve_product_relation(
            values, ["P1", "V1", "m2"], ["P2", "V2", "m1"]
        )
    return False


def _ideal_change_solve_temperature_for_isentropic(gas, known_t, known_p, target_p):
    if None in (known_t, known_p, target_p):
        return None
    known_t = float(known_t)
    known_p = float(known_p)
    target_p = float(target_p)
    if min(known_t, known_p, target_p) <= 0.0:
        return None

    def f(temp):
        ds = _ideal_change_delta_s_si(gas, known_t, known_p, temp, target_p)
        if ds is None:
            return None
        return ds

    low = max(1.0, known_t * 0.2)
    high = max(known_t * 5.0, known_t + 500.0)
    f_low = f(low)
    f_high = f(high)
    tries = 0
    while f_low is not None and f_high is not None and f_low * f_high > 0.0 and tries < 12:
        low *= 0.5
        high *= 1.5
        f_low = f(low)
        f_high = f(high)
        tries += 1
    if f_low is None or f_high is None or f_low * f_high > 0.0:
        return None
    for _ in range(60):
        mid = 0.5 * (low + high)
        f_mid = f(mid)
        if f_mid is None:
            return None
        if abs(f_mid) < 1e-8:
            return mid
        if f_low * f_mid <= 0.0:
            high = mid
            f_high = f_mid
        else:
            low = mid
            f_low = f_mid
    return 0.5 * (low + high)


def _ideal_change_apply_isentropic(values, gas):
    changed = False
    t1 = values.get("T1")
    t2 = values.get("T2")
    p1 = values.get("P1")
    p2 = values.get("P2")
    if None not in (t1, p1, t2) and p2 is None:
        cp_part = _ideal_change_cp_over_t_integral(gas, t1, t2)
        r = _ideal_gas_R(gas)
        if cp_part is not None and r not in (None, 0):
            values["P2"] = float(p1) * math.exp(cp_part / r)
            changed = True
    if None not in (t2, p2, t1) and p1 is None:
        cp_part = _ideal_change_cp_over_t_integral(gas, t1, t2)
        r = _ideal_gas_R(gas)
        if cp_part is not None and r not in (None, 0):
            values["P1"] = float(p2) / math.exp(cp_part / r)
            changed = True
    if None not in (t1, p1, p2) and t2 is None:
        solved = _ideal_change_solve_temperature_for_isentropic(gas, t1, p1, p2)
        if solved is not None:
            values["T2"] = solved
            changed = True
    if None not in (t2, p2, p1) and t1 is None:
        solved = _ideal_change_solve_temperature_for_isentropic(gas, t2, p2, p1)
        if solved is not None:
            values["T1"] = solved
            changed = True
    return changed


def solve_ideal_gas_change(gas, unit_system, constant, isentropic, input_values):
    r = _ideal_gas_R(gas)
    if r is None:
        return _error_dict("Ideal-gas constant is not available.")

    values = {}
    for key in ("P1", "V1", "m1", "T1", "P2", "V2", "m2", "T2"):
        values[key] = _ideal_change_to_si(key, input_values.get(key), unit_system)

    errors = []
    missing = []

    for _ in range(12):
        changed = False
        if _ideal_change_apply_constant(values, constant):
            changed = True
        if _ideal_change_solve_state(values, "1", r):
            changed = True
        if _ideal_change_solve_state(values, "2", r):
            changed = True
        if constant in ("V", "P", "T") and _ideal_change_apply_simple_relation(values, constant):
            changed = True
        if isentropic and _ideal_change_apply_isentropic(values, gas):
            changed = True
        if not changed:
            break

    if isentropic:
        delta_s_si = 0.0
    else:
        delta_s_si = _ideal_change_delta_s_si(
            gas, values.get("T1"), values.get("P1"), values.get("T2"), values.get("P2")
        )
    delta_S_si = None
    mass_for_delta_S = _ideal_change_mass_for_delta_S(values)
    if delta_s_si is not None and mass_for_delta_S is not None:
        delta_S_si = mass_for_delta_S * delta_s_si

    if isentropic:
        check = _ideal_change_delta_s_si(
            gas, values.get("T1"), values.get("P1"), values.get("T2"), values.get("P2")
        )
        if check is not None and abs(check) > 1e-5:
            errors.append("Inputs are inconsistent with an isentropic ideal-gas process.")

    for state_num in ("1", "2"):
        keys = ["P" + state_num, "V" + state_num, "m" + state_num, "T" + state_num]
        known = [key for key in keys if values.get(key) is not None]
        if len(known) < 3:
            missing.append("State " + state_num + " needs any three of P, V, m, and T.")

    if not isentropic and delta_s_si is None:
        missing.append("Entropy change needs T1, P1, T2, and P2.")

    out_values = {}
    for key, value in values.items():
        out_values[key] = _ideal_change_from_si(key, value, unit_system)
    out_values["delta_s"] = _ideal_change_delta_s_display(delta_s_si, unit_system)
    out_values["delta_S"] = _ideal_change_delta_S_display(delta_S_si, unit_system)

    return {
        "values": out_values,
        "errors": errors,
        "missing": missing,
        "isentropic": isentropic,
        "constant": constant,
        "unit_system": unit_system,
        "gas": gas,
    }


def ideal_gas_change_result_lines(result):
    if result is None:
        return ["No result found."]
    if _is_error(result):
        return ["Error:", str(result["error"])]
    values = result["values"]
    unit_system = result["unit_system"]
    lines = [
        "Ideal-Gas Change",
        _history_fluid_name(_ideal_change_gas_label(result["gas"])),
        "Isentropic: " + ("Yes" if result["isentropic"] else "No"),
        "Constant: " + (result["constant"] if result["constant"] is not None else "None"),
        "",
        "Results:",
    ]
    result_items = []
    for key in ("P1", "V1", "m1", "T1", "P2", "V2", "m2", "T2"):
        result_items.append((
            values.get(key) is None,
            _ideal_change_display_value(key, values.get(key), unit_system)
        ))
    if values.get("delta_s") is not None:
        result_items.append((
            False,
            "delta s = " + _display_number(values["delta_s"]) + " " + _ideal_change_entropy_unit(unit_system)
        ))
    else:
        result_items.append((True, "delta s = u"))
    if values.get("delta_S") is not None:
        result_items.append((
            False,
            "delta S = " + _display_number(values["delta_S"]) + " " + _ideal_change_delta_S_unit(unit_system)
        ))
    else:
        result_items.append((True, "delta S = u"))
    lines.extend([line for is_unknown, line in result_items if not is_unknown])
    lines.extend([line for is_unknown, line in result_items if is_unknown])
    if result.get("errors"):
        lines.extend(["", "Check inputs:"])
        for message in result["errors"]:
            lines.append("- " + str(message))
    if result.get("missing"):
        lines.extend(["", "Missing info:"])
        for message in result["missing"]:
            lines.append("- " + str(message))
    return lines


def _history_record_ideal_change(gas, unit_system, input_values, result):
    if result is None or _is_error(result):
        return
    lines = [
        "Ideal-Gas Change",
        _history_fluid_name(_ideal_change_gas_label(gas)) + ", " + _history_unit_name(unit_system),
        "Isentropic: " + ("Yes" if result["isentropic"] else "No"),
        "Constant: " + (result["constant"] if result["constant"] is not None else "None"),
        "",
        "Given:",
    ]
    any_given = False
    for key in ("P1", "V1", "m1", "T1", "P2", "V2", "m2", "T2"):
        if input_values.get(key) is not None:
            lines.append(_ideal_change_display_value(key, input_values.get(key), unit_system))
            any_given = True
    if not any_given:
        lines.append("None")
    lines.extend(["", "Found:"])
    values = result["values"]
    any_found = False
    for key in ("P1", "V1", "m1", "T1", "P2", "V2", "m2", "T2"):
        if input_values.get(key) is None and values.get(key) is not None:
            lines.append(_ideal_change_display_value(key, values.get(key), unit_system))
            any_found = True
    if values.get("delta_s") is not None:
        lines.append("delta s = " + _display_number(values["delta_s"]) + " " + _ideal_change_entropy_unit(unit_system))
        any_found = True
    if values.get("delta_S") is not None:
        lines.append("delta S = " + _display_number(values["delta_S"]) + " " + _ideal_change_delta_S_unit(unit_system))
        any_found = True
    if not any_found:
        lines.append("No additional values solved.")
    _history_add(lines)


def _ideal_basic_uses_z(gas):
    key = _canonical_ideal_gas_key(gas)
    return key not in IDEAL_GAS_TABLE_NAMES and key != "helium"


def solve_ideal_gas_basic(gas, unit_system, input_values):
    r = _ideal_gas_R(gas)
    if r is None:
        return _error_dict("Ideal-gas constant is not available.")
    uses_z = _ideal_basic_uses_z(gas)

    values = {}
    for key in ("P", "V", "m", "T"):
        values[key] = _ideal_change_to_si(key, input_values.get(key), unit_system)
    if uses_z and "Z" in input_values:
        values["Z"] = _safe_float(input_values.get("Z"))
    else:
        values["Z"] = 1.0

    missing = [key for key in ("P", "V", "m", "T") if values.get(key) is None]
    errors = []
    check_keys = ("P", "V", "m", "T", "Z") if uses_z else ("P", "V", "m", "T")
    for key in check_keys:
        if values.get(key) is not None and float(values[key]) <= 0.0:
            errors.append(key + " must be positive for " + ("PV = mZRT." if uses_z else "PV = mRT."))
    if len(missing) == 1 and values.get("Z") is None:
        errors.append("Z is needed to solve " + missing[0] + " with PV = mZRT; enter Z or blank for Z = 1.")
    elif len(missing) != 1:
        if len(missing) == 0:
            if values.get("Z") is not None:
                lhs = float(values["P"]) * float(values["V"])
                rhs = float(values["m"]) * float(values["Z"]) * r * float(values["T"])
                if not _close_enough(lhs, rhs):
                    errors.append("Inputs are inconsistent with " + ("PV = mZRT." if uses_z else "PV = mRT."))
        else:
            errors.append("Enter exactly one unknown value as u.")
    elif not errors:
        unknown = missing[0]
        try:
            if unknown == "P" and values["V"] not in (None, 0):
                values["P"] = values["m"] * values["Z"] * r * values["T"] / values["V"]
            elif unknown == "V" and values["P"] not in (None, 0):
                values["V"] = values["m"] * values["Z"] * r * values["T"] / values["P"]
            elif unknown == "m" and values["Z"] * r * values["T"] != 0.0:
                values["m"] = values["P"] * values["V"] / (values["Z"] * r * values["T"])
            elif unknown == "T" and values["m"] * values["Z"] * r != 0.0:
                values["T"] = values["P"] * values["V"] / (values["m"] * values["Z"] * r)
            else:
                errors.append("Cannot solve because a divisor is zero.")
        except:
            errors.append("Could not solve " + ("PV = mZRT" if uses_z else "PV = mRT") + " from these inputs.")

    out_values = {}
    for key in ("P", "V", "m", "T"):
        out_values[key] = _ideal_change_from_si(key, values.get(key), unit_system)
    if uses_z:
        out_values["Z"] = values.get("Z")

    return {
        "values": out_values,
        "errors": errors,
        "unit_system": unit_system,
        "gas": gas,
        "uses_z": uses_z,
    }


def ideal_gas_basic_result_lines(result):
    if result is None:
        return ["No result found."]
    if _is_error(result):
        return ["Error:", str(result["error"])]
    values = result["values"]
    unit_system = result["unit_system"]
    uses_z = result.get("uses_z", False)
    lines = [
        "Ideal-Gas Basic Solver",
        _history_fluid_name(_ideal_change_gas_label(result["gas"])),
        "PV = mZRT" if uses_z else "PV = mRT",
        "",
        "Results:",
    ]
    result_items = []
    result_keys = ("m", "P", "V", "T", "Z") if uses_z else ("m", "P", "V", "T")
    for key in result_keys:
        result_items.append((
            values.get(key) is None,
            _ideal_change_display_value(key, values.get(key), unit_system)
        ))
    lines.extend([line for is_unknown, line in result_items if not is_unknown])
    lines.extend([line for is_unknown, line in result_items if is_unknown])
    if result.get("errors"):
        lines.extend(["", "Check inputs:"])
        for message in result["errors"]:
            lines.append("- " + str(message))
    return lines


def _history_record_ideal_basic(gas, unit_system, input_values, result):
    if result is None or _is_error(result):
        return
    uses_z = result.get("uses_z", False)
    lines = [
        "Ideal-Gas Basic Solver",
        _history_fluid_name(_ideal_change_gas_label(gas)) + ", " + _history_unit_name(unit_system),
        "PV = mZRT" if uses_z else "PV = mRT",
        "",
        "Given:",
    ]
    any_given = False
    result_keys = ("m", "P", "V", "T", "Z") if uses_z else ("m", "P", "V", "T")
    for key in result_keys:
        if input_values.get(key) is not None:
            lines.append(_ideal_change_display_value(key, input_values.get(key), unit_system))
            any_given = True
    if not any_given:
        lines.append("None")

    lines.extend(["", "Found:"])
    values = result["values"]
    any_found = False
    for key in result_keys:
        if input_values.get(key) is None and values.get(key) is not None:
            lines.append(_ideal_change_display_value(key, values.get(key), unit_system))
            any_found = True
    if not any_found:
        lines.append("No additional values solved.")
    if result.get("errors"):
        lines.extend(["", "Check inputs:"])
        for message in result["errors"]:
            lines.append("- " + str(message))
    _history_add(lines)


def _ideal_specific_heat_unit(unit_system):
    if _unit_system_key(unit_system) == "metric":
        return "kJ/(kg*K)"
    return "Btu/(lbm*R)"


def _ideal_specific_heat_display(value_si, unit_system):
    if value_si is None:
        return None
    if _unit_system_key(unit_system) == "metric":
        return float(value_si)
    return float(value_si) * BTU_PER_LBM_R_PER_KJ_PER_KG_K


def _ideal_specific_heat_from_page37(gas, temp_k):
    key = _canonical_ideal_gas_key(gas)
    prefixes = {
        "air": "air",
        "n2": "n2",
        "o2": "o2",
        "co2": "co2",
        "co": "co",
        "h2": "h2",
    }
    prefix = prefixes.get(key)
    if prefix is None:
        return None
    try:
        rows = row_dicts("page_37_ideal_gas_specific_heats_common_gases", unit_system="metric")
    except:
        return None
    row = _lookup_1d(rows, temp_k, "T_K", "ideal_gas_specific_heat")
    if row is None:
        return None
    cp_key = prefix + "_cp_kJ_per_kg_K"
    cv_key = prefix + "_cv_kJ_per_kg_K"
    if cp_key not in row or cv_key not in row:
        return None
    return {
        "cp": float(row[cp_key]),
        "cv": float(row[cv_key]),
        "source": "Page 37 specific-heat table",
    }


def _ideal_specific_heat_from_cp_poly(gas, temp_k):
    key = _canonical_ideal_gas_key(gas)
    r = _ideal_gas_R(key)
    if r is None:
        return None
    if key == "helium":
        cp = 2.5 * r
        return {"cp": cp, "cv": cp - r, "source": "Monatomic ideal-gas relation"}
    if temp_k < 300.0 or temp_k > 1000.0:
        return None
    coeffs = _ideal_change_cp_coeffs(key)
    if coeffs is None:
        return None
    a, b, c, d, e = coeffs
    t = float(temp_k)
    cp_over_r = a + b * t + c * t * t + d * t ** 3 + e * t ** 4
    cp = r * cp_over_r
    return {"cp": cp, "cv": cp - r, "source": "Page 38 variable-cp(T) polynomial"}


def _ideal_specific_heat_from_table_slope(gas, temp_k):
    rows = _ideal_gas_table_rows_si(gas)
    usable = [
        row for row in rows
        if "T_K" in row and "h_kJ_per_kg" in row and "u_kJ_per_kg" in row
    ]
    if len(usable) < 2:
        return None
    usable.sort(key=lambda row: row["T_K"])
    if temp_k < usable[0]["T_K"] or temp_k > usable[-1]["T_K"]:
        return None

    idx = _bisect_left_key(usable, "T_K", temp_k)
    if idx <= 0:
        low = usable[0]
        high = usable[1]
    elif idx >= len(usable):
        low = usable[-2]
        high = usable[-1]
    elif usable[idx]["T_K"] == temp_k:
        low = usable[idx - 1]
        high = usable[idx + 1] if idx + 1 < len(usable) else usable[idx]
        if high is usable[idx]:
            low = usable[idx - 1]
    else:
        low = usable[idx - 1]
        high = usable[idx]
    dt = float(high["T_K"]) - float(low["T_K"])
    if dt == 0.0:
        return None
    cp = (float(high["h_kJ_per_kg"]) - float(low["h_kJ_per_kg"])) / dt
    cv_slope = (float(high["u_kJ_per_kg"]) - float(low["u_kJ_per_kg"])) / dt
    return {
        "cp": cp,
        "cv_slope": cv_slope,
        "cv": cp - _ideal_gas_R(gas),
        "source": "Ideal-gas h/u table slope",
    }


def solve_ideal_gas_specific_heats(gas, unit_system, temp):
    temp_value = _safe_float(temp)
    if temp_value is None:
        return _error_dict("Temperature is required.")
    temp_k = _to_kelvin(temp_value, unit_system)
    if temp_k <= 0.0:
        return _error_dict("Absolute temperature must be positive.")
    r = _ideal_gas_R(gas)
    if r is None:
        return _error_dict("Ideal-gas constant is not available.")

    notes = []
    method = (
        _ideal_specific_heat_from_page37(gas, temp_k) or
        _ideal_specific_heat_from_cp_poly(gas, temp_k) or
        _ideal_specific_heat_from_table_slope(gas, temp_k)
    )
    if method is None:
        return {
            "values": {
                "T": _ideal_change_from_si("T", temp_k, unit_system),
                "R": _ideal_specific_heat_display(r, unit_system),
                "cp": None,
                "cv": None,
                "k": None,
            },
            "errors": ["cp, cv, and k need page 37, page 38, or ideal-gas h/u table data for this gas at the entered temperature."],
            "notes": ["A-1 only supplies molecular weight and critical properties; it is enough for R, not specific heats."],
            "unit_system": unit_system,
            "gas": gas,
            "source": "A-1 molecular weight",
        }

    cp = method.get("cp")
    cv = method.get("cv")
    if cp is None or cv is None or cv <= 0.0:
        return _error_dict("Specific heat data are not physically usable at this temperature.")
    k_value = cp / cv

    if not _close_enough(cp - cv, r, tol=2e-3):
        notes.append("Sanity check: cp - cv differs from R beyond table-rounding tolerance.")
    if method.get("cv_slope") is not None and not _close_enough(method["cv_slope"], cv, tol=2e-2):
        notes.append("Finite-difference cv was adjusted to cp - R for ideal-gas consistency.")

    return {
        "values": {
            "T": _ideal_change_from_si("T", temp_k, unit_system),
            "R": _ideal_specific_heat_display(r, unit_system),
            "cp": _ideal_specific_heat_display(cp, unit_system),
            "cv": _ideal_specific_heat_display(cv, unit_system),
            "k": k_value,
        },
        "errors": [],
        "notes": notes,
        "unit_system": unit_system,
        "gas": gas,
        "source": method.get("source", "specific-heat data"),
    }


def ideal_gas_specific_heat_result_lines(result):
    if result is None:
        return ["No result found."]
    if _is_error(result):
        return ["Error:", str(result["error"])]
    values = result["values"]
    unit_system = result["unit_system"]
    heat_unit = _ideal_specific_heat_unit(unit_system)
    lines = [
        "Ideal-Gas Specific Heats",
        _history_fluid_name(_ideal_change_gas_label(result["gas"])),
        "Source: " + str(result.get("source", "specific-heat data")),
        "",
        "Results:",
        _ideal_change_display_value("T", values.get("T"), unit_system),
    ]
    if values.get("R") is not None:
        lines.append("R = " + _display_number(values["R"]) + " " + heat_unit)
    else:
        lines.append("R = u")
    if values.get("cp") is not None:
        lines.append("cp = " + _display_number(values["cp"]) + " " + heat_unit)
    else:
        lines.append("cp = u")
    if values.get("cv") is not None:
        lines.append("cv = " + _display_number(values["cv"]) + " " + heat_unit)
    else:
        lines.append("cv = u")
    if values.get("k") is not None:
        lines.append("k = " + _display_number(values["k"]))
    else:
        lines.append("k = u")
    if result.get("errors"):
        lines.extend(["", "Missing info:"])
        for message in result["errors"]:
            lines.append("- " + str(message))
    if result.get("notes"):
        lines.extend(["", "Notes:"])
        for message in result["notes"]:
            lines.append("- " + str(message))
    return lines


def _history_record_ideal_specific_heats(gas, unit_system, temp, result):
    if result is None or _is_error(result):
        return
    heat_unit = _ideal_specific_heat_unit(unit_system)
    lines = [
        "Ideal-Gas Specific Heats",
        _history_fluid_name(_ideal_change_gas_label(gas)) + ", " + _history_unit_name(unit_system),
        "Source: " + str(result.get("source", "specific-heat data")),
        "",
        "Given:",
        _ideal_change_display_value("T", temp, unit_system),
        "",
        "Found:",
    ]
    values = result["values"]
    if values.get("R") is not None:
        lines.append("R = " + _display_number(values["R"]) + " " + heat_unit)
    if values.get("cp") is not None:
        lines.append("cp = " + _display_number(values["cp"]) + " " + heat_unit)
    if values.get("cv") is not None:
        lines.append("cv = " + _display_number(values["cv"]) + " " + heat_unit)
    if values.get("k") is not None:
        lines.append("k = " + _display_number(values["k"]))
    if result.get("errors"):
        lines.extend(["", "Missing info:"])
        for message in result["errors"]:
            lines.append("- " + str(message))
    _history_add(lines)


def ideal_gas_specific_heats_menu(gas, unit_system):
    t_unit = _ideal_change_temp_unit(unit_system)
    temp = safe_input_float("Enter T (" + t_unit + "): ", allow_blank=False)
    if temp == GO_BACK:
        return GO_BACK
    result = solve_ideal_gas_specific_heats(gas, unit_system, temp)
    _history_record_ideal_specific_heats(gas, unit_system, temp, result)
    return display_message(ideal_gas_specific_heat_result_lines(result))


def ideal_gas_basic_solver_menu(gas, unit_system):
    p_unit = _ideal_change_pressure_unit(unit_system)
    v_unit = _ideal_change_volume_unit(unit_system)
    m_unit = _ideal_change_mass_unit(unit_system)
    t_unit = _ideal_change_temp_unit(unit_system)
    prompt_specs = [
        ("m", "Enter m (" + m_unit + ", u if unknown): "),
        ("P", "Enter P (" + p_unit + ", u if unknown): "),
        ("V", "Enter V (" + v_unit + ", u if unknown): "),
        ("T", "Enter T (" + t_unit + ", u if unknown): "),
    ]
    values = {}
    for key, prompt in prompt_specs:
        value = safe_input_unknown_float(prompt)
        if value == GO_BACK:
            return GO_BACK
        values[key] = value
    if _ideal_basic_uses_z(gas):
        z_value = safe_input_optional_unknown_float("Enter Z (blank = 1, u if unknown): ", blank_value=1.0)
        if z_value == GO_BACK:
            return GO_BACK
        values["Z"] = z_value
    result = solve_ideal_gas_basic(gas, unit_system, values)
    _history_record_ideal_basic(gas, unit_system, values, result)
    return display_message(ideal_gas_basic_result_lines(result))


def ideal_gas_changing_values_menu(gas, unit_system):
    isentropic = _prompt_yes_no("Is the process isentropic?")
    if isentropic == GO_BACK:
        return GO_BACK
    lines = [
        "What's Constant?",
        "",
        "1. V",
        "2. P",
        "3. T",
        "4. None",
    ]
    choice = paged_choice(lines, ["1", "2", "3", "4"])
    if choice == GO_BACK:
        return GO_BACK
    constant_map = {"1": "V", "2": "P", "3": "T", "4": None}
    constant = constant_map[choice]

    p_unit = _ideal_change_pressure_unit(unit_system)
    v_unit = _ideal_change_volume_unit(unit_system)
    m_unit = _ideal_change_mass_unit(unit_system)
    t_unit = _ideal_change_temp_unit(unit_system)

    vars_to_prompt = ["P", "V", "m", "T"] if constant is None else [v for v in ("P", "V", "m", "T") if v != constant]
    unit_map = {"P": p_unit, "V": v_unit, "m": m_unit, "T": t_unit}
    values = {}
    for state_num in ("1", "2"):
        for var in vars_to_prompt:
            key = var + state_num
            value = safe_input_unknown_float("Enter " + key + " (" + unit_map[var] + ", u if unknown): ")
            if value == GO_BACK:
                return GO_BACK
            values[key] = value
    for key in ("P1", "V1", "m1", "T1", "P2", "V2", "m2", "T2"):
        values.setdefault(key, None)

    result = solve_ideal_gas_change(gas, unit_system, constant, isentropic, values)
    _history_record_ideal_change(gas, unit_system, values, result)
    return display_message(ideal_gas_change_result_lines(result))


def real_fluid_lookup_menu():
    fluid, unit_system, nav = prompt_fluid_and_unit()
    if nav == GO_BACK:
        return GO_BACK

    temp_units = "C" if unit_system == "SI" else "F"
    pressure_units = "bar" if unit_system == "SI" else "psia"

    lines = [
        "Real-Fluid Lookup",
        "",
        "1. Given T",
        "2. Given P",
        "3. Given T and P",
        "4. Given T and h/u/s/v",
        "5. Given P and h/u/s/v",
    ]
    choice = paged_choice(lines, ["1", "2", "3", "4", "5"])
    if choice == GO_BACK:
        return GO_BACK

    temp = None
    pressure = None
    kwargs = {"h": None, "u": None, "s": None, "v": None}
    quality_input = None

    if choice in ("1", "3", "4"):
        temp = safe_input_float("Enter T (" + temp_units + "): ", allow_blank=False)
        if temp == GO_BACK:
            return GO_BACK

    if choice in ("2", "3", "5"):
        pressure = safe_input_float("Enter P (" + pressure_units + "): ", allow_blank=False)
        if pressure == GO_BACK:
            return GO_BACK

    if choice in ("4", "5"):
        symbol, value, nav = _prompt_property_value()
        if nav == GO_BACK:
            return GO_BACK
        kwargs = _prop_kwargs(symbol, value)

    sat_state = None
    if choice in ("1", "2", "3"):
        sat_state, quality, nav = _prompt_sat_state()
        if nav == GO_BACK:
            return GO_BACK
        if _is_error(nav):
            return display_result_dict(nav)
        if quality is not None:
            quality_input = quality
            q_kwargs = _quality_kwargs_from_sat(
                fluid, unit_system, temp=temp, pressure=pressure, quality=quality
            )
            if _is_error(q_kwargs):
                return display_result_dict(q_kwargs)
            if q_kwargs is not None:
                kwargs = q_kwargs

    result = gasLookUp(
        fluid, unit_system,
        temp=temp, pressure=pressure,
        h=kwargs["h"], u=kwargs["u"], s=kwargs["s"], v=kwargs["v"],
        sat_state=sat_state
    )
    given = []
    if temp is not None:
        given.append(("T", temp, _lookup_input_unit("T", unit_system)))
    if pressure is not None:
        given.append(("P", pressure, _lookup_input_unit("P", unit_system)))
    if sat_state is not None:
        given.append(("sat state", sat_state, ""))
    if quality_input is not None:
        given.append(("x", quality_input, ""))
    elif choice in ("4", "5"):
        for symbol in ("h", "u", "s", "v"):
            if kwargs[symbol] is not None:
                given.append((symbol, kwargs[symbol], _lookup_input_unit(symbol, unit_system)))
    _history_record_lookup("Real Fluid Lookup", fluid, unit_system, given, result)
    return display_result_dict(result)



def ideal_gas_lookup_menu():
    gas = prompt_fluid(get_ideal_gas_options())
    if gas == GO_BACK:
        return GO_BACK

    unit_system = prompt_unit_system()
    if unit_system == GO_BACK:
        return GO_BACK

    temp_units = "K" if unit_system == "SI" else "R"
    pressure_units = "bar" if unit_system == "SI" else "psia"

    lines = [
        "Ideal-Gas Lookup",
        "",
        "1. Given T and P",
        "2. Given T and h/u/s/v",
        "3. Given P and h/u/s/v",
        "4. Changing values",
        "5. Basic solver",
        "6. Specific heats at T",
    ]
    choice = paged_choice(lines, ["1", "2", "3", "4", "5", "6"])
    if choice == GO_BACK:
        return GO_BACK
    if choice == "4":
        return ideal_gas_changing_values_menu(gas, unit_system)
    if choice == "5":
        return ideal_gas_basic_solver_menu(gas, unit_system)
    if choice == "6":
        return ideal_gas_specific_heats_menu(gas, unit_system)

    temp = None
    pressure = None
    kwargs = {"h": None, "u": None, "s": None, "v": None}

    if choice in ("1", "2"):
        temp = safe_input_float("Enter T (" + temp_units + "): ", allow_blank=False)
        if temp == GO_BACK:
            return GO_BACK

    if choice in ("1", "3"):
        pressure = safe_input_float("Enter P (" + pressure_units + "): ", allow_blank=False)
        if pressure == GO_BACK:
            return GO_BACK

    if choice in ("2", "3"):
        symbol, value, nav = _prompt_property_value_with_units(unit_system)
        if nav == GO_BACK:
            return GO_BACK
        kwargs = _prop_kwargs(symbol, value)

    result = idealGasLookUp(
        gas, unit_system,
        temp=temp, pressure=pressure,
        h=kwargs["h"], u=kwargs["u"], s=kwargs["s"], v=kwargs["v"]
    )
    given = []
    if temp is not None:
        given.append(("T", temp, "K" if _unit_system_key(unit_system) == "metric" else "R"))
    if pressure is not None:
        given.append(("P", pressure, _lookup_input_unit("P", unit_system)))
    for symbol in ("h", "u", "s", "v"):
        if kwargs[symbol] is not None:
            given.append((symbol, kwargs[symbol], _lookup_input_unit(symbol, unit_system)))
    _history_record_lookup("Ideal Gas Lookup", gas, unit_system, given, result)
    return display_result_dict(result)



# =========================================================
# UNIT CONVERSION SECTION
# =========================================================

_UNIT_CATEGORIES = [
    ("Temperature", ["C", "F", "K", "R"]),
    ("Pressure", ["Pa", "kPa", "MPa", "bar", "psia", "atm"]),
    ("Energy", ["J", "kJ", "Btu", "ft*lbf"]),
    ("Specific energy", ["kJ/kg", "J/kg", "Btu/lbm", "ft*lbf/lbm"]),
    ("Entropy", ["kJ/(kg*K)", "J/(kg*K)", "Btu/(lbm*R)"]),
    ("Volume", ["m^3", "L", "ft^3", "in^3", "gal"]),
    ("Specific volume", ["m^3/kg", "ft^3/lbm"]),
    ("Mass", ["kg", "g", "lbm", "slug"]),
    ("Power", ["W", "kW", "hp", "Btu/hr", "Btu/s"]),
]

_PRESSURE_TO_PA = {
    "Pa": 1.0,
    "kPa": 1000.0,
    "MPa": 1000000.0,
    "bar": 100000.0,
    "psia": 6894.757293168,
    "atm": 101325.0,
}

_ENERGY_TO_J = {
    "J": 1.0,
    "kJ": 1000.0,
    "Btu": 1055.05585262,
    "ft*lbf": 1.3558179483314,
}

_SPECIFIC_ENERGY_TO_J_PER_KG = {
    "kJ/kg": 1000.0,
    "J/kg": 1.0,
    "Btu/lbm": 2326.0,
    "ft*lbf/lbm": 2.98906692,
}

_ENTROPY_TO_J_PER_KG_K = {
    "kJ/(kg*K)": 1000.0,
    "J/(kg*K)": 1.0,
    "Btu/(lbm*R)": 4186.8,
}

_VOLUME_TO_M3 = {
    "m^3": 1.0,
    "L": 0.001,
    "ft^3": 0.028316846592,
    "in^3": 0.000016387064,
    "gal": 0.003785411784,
}

_SPECIFIC_VOLUME_TO_M3_PER_KG = {
    "m^3/kg": 1.0,
    "ft^3/lbm": 0.0624279606,
}

_MASS_TO_KG = {
    "kg": 1.0,
    "g": 0.001,
    "lbm": 0.45359237,
    "slug": 14.59390294,
}

_POWER_TO_W = {
    "W": 1.0,
    "kW": 1000.0,
    "hp": 745.699871582,
    "Btu/hr": 0.293071070172,
    "Btu/s": 1055.05585262,
}


def _temp_to_k(value, unit):
    x = float(value)
    if unit == "K":
        return x
    if unit == "C":
        return x + 273.15
    if unit == "F":
        return (x + 459.67) * 5.0 / 9.0
    if unit == "R":
        return x * 5.0 / 9.0
    return x


def _temp_from_k(value_k, unit):
    k = float(value_k)
    if unit == "K":
        return k
    if unit == "C":
        return k - 273.15
    if unit == "F":
        return k * 9.0 / 5.0 - 459.67
    if unit == "R":
        return k * 9.0 / 5.0
    return k


def _convert_by_factor(value, from_unit, to_unit, factor_dict):
    base = float(value) * factor_dict[from_unit]
    return base / factor_dict[to_unit]


def convert_units(value, category, from_unit, to_unit):
    if category == "Temperature":
        return _temp_from_k(_temp_to_k(value, from_unit), to_unit)
    if category == "Pressure":
        return _convert_by_factor(value, from_unit, to_unit, _PRESSURE_TO_PA)
    if category == "Energy":
        return _convert_by_factor(value, from_unit, to_unit, _ENERGY_TO_J)
    if category == "Specific energy":
        return _convert_by_factor(value, from_unit, to_unit, _SPECIFIC_ENERGY_TO_J_PER_KG)
    if category == "Entropy":
        return _convert_by_factor(value, from_unit, to_unit, _ENTROPY_TO_J_PER_KG_K)
    if category == "Volume":
        return _convert_by_factor(value, from_unit, to_unit, _VOLUME_TO_M3)
    if category == "Specific volume":
        return _convert_by_factor(value, from_unit, to_unit, _SPECIFIC_VOLUME_TO_M3_PER_KG)
    if category == "Mass":
        return _convert_by_factor(value, from_unit, to_unit, _MASS_TO_KG)
    if category == "Power":
        return _convert_by_factor(value, from_unit, to_unit, _POWER_TO_W)
    return None


def _prompt_unit_from_list(title, units):
    lines = [title, ""]
    valid = []
    for i, unit in enumerate(units, start=1):
        opt = str(i)
        valid.append(opt)
        lines.append(opt + ". " + unit)
    choice = paged_choice(lines, valid)
    if choice == GO_BACK:
        return GO_BACK
    return units[int(choice) - 1]


def unit_conversion_menu():
    lines = ["Unit Conversion", ""]
    valid = []
    for i, item in enumerate(_UNIT_CATEGORIES, start=1):
        opt = str(i)
        valid.append(opt)
        lines.append(opt + ". " + item[0])

    choice = paged_choice(lines, valid)
    if choice == GO_BACK:
        return GO_BACK

    category, units = _UNIT_CATEGORIES[int(choice) - 1]

    from_unit = _prompt_unit_from_list("Convert From", units)
    if from_unit == GO_BACK:
        return GO_BACK

    to_unit = _prompt_unit_from_list("Convert To", units)
    if to_unit == GO_BACK:
        return GO_BACK

    value = safe_input_float("Enter value (" + from_unit + "): ", allow_blank=False)
    if value == GO_BACK:
        return GO_BACK

    result = convert_units(value, category, from_unit, to_unit)
    if result is None:
        return display_message(["Conversion failed."])

    answer_line = (
        _display_number(value) + " " + from_unit +
        " = " +
        _display_number(result) + " " + to_unit
    )
    lines = [
        "Unit Conversion",
        "",
        answer_line,
    ]
    return display_message(lines)
'''
_CORE_LOADED = False
GO_BACK = "__GO_BACK__"
QUIT_CANCELLED = "__QUIT_CANCELLED__"
MAX_LINES = 8
NEXT_PAGE_OPTION = "9"
PREV_PAGE_OPTION = "0"
BACK_OPTION = "8"

def _load_core():
    global _CORE_LOADED
    if not _CORE_LOADED:
        exec(_CORE, globals())
        _CORE_LOADED = True

def clear_screen():
    print(" ")
    print(" ")

def print_padded_page(page_lines, max_lines):
    count = 0
    for line in page_lines:
        print(line)
        count += 1
    while count < max_lines:
        print(" ")
        count += 1

def split_pages(lines, max_lines=MAX_LINES):
    pages = []
    current = []
    for line in lines:
        current.append(str(line))
        if len(current) >= max_lines:
            pages.append(current)
            current = []
    if current:
        pages.append(current)
    if not pages:
        pages = [[]]
    return pages

def quit_app():
    clear_screen()
    print_padded_page(["Quit Thermo?", "", "1. Yes", "2. No"], MAX_LINES)
    choice = input("Option: ").strip().lower()
    if choice in ("1", "y", "yes", "q"):
        raise SystemExit
    return None

def _handle_global_nav(value):
    v = str(value).strip().lower()
    if v == "q":
        quit_app()
        return QUIT_CANCELLED
    if v == "b":
        return GO_BACK
    return None

def paged_choice(lines, valid_options):
    pages = split_pages(lines, MAX_LINES)
    page_index = 0
    while True:
        clear_screen()
        print_padded_page(pages[page_index], MAX_LINES)
        footer = []
        if len(pages) > 1 and page_index < len(pages) - 1:
            footer.append(NEXT_PAGE_OPTION + ". Next")
        if len(pages) > 1 and page_index > 0:
            footer.append(PREV_PAGE_OPTION + ". Prev")
        footer.append("b. Back   q. Quit")
        print("   ".join(footer))
        choice = input("Option: ").strip()
        nav = _handle_global_nav(choice)
        if nav == GO_BACK:
            return GO_BACK
        if nav == QUIT_CANCELLED:
            continue
        if page_index < len(pages) - 1 and choice == NEXT_PAGE_OPTION:
            page_index += 1
            continue
        if page_index > 0 and choice == PREV_PAGE_OPTION:
            page_index -= 1
            continue
        if choice in valid_options:
            return choice

def run_app():
    dispatch = {'1': 'real_fluid_lookup_menu', '2': 'ideal_gas_lookup_menu', '5': 'unit_conversion_menu', '6': 'history_menu', '7': 'quit'}
    lines = ['Thermo Lookup', '', '1. Real Fluid lookup', '2. Ideal Gas Lookup', '5. Unit Converter', '6. History', '7. Quit']
    while True:
        choice = paged_choice(lines, ['1', '2', '5', '6', '7'])
        if choice == GO_BACK:
            quit_app()
            continue
        target = dispatch.get(choice)
        if target == "quit":
            quit_app()
            continue
        if target:
            _load_core()
            globals()[target]()

def main():
    run_app()

main()
