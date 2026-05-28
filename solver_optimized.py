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
# STEADY-STATE TURBINE SOLVER
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


def _turbine_temp_unit(unit_system, ideal_gas):
    if ideal_gas:
        return "K" if _unit_system_key(unit_system) == "metric" else "R"
    return "C" if _unit_system_key(unit_system) == "metric" else "F"


def _turbine_pressure_unit(unit_system):
    return "bar" if _unit_system_key(unit_system) == "metric" else "psia"


def _turbine_mdot_unit(unit_system):
    return "kg/s" if _unit_system_key(unit_system) == "metric" else "lbm/s"


def _turbine_power_unit(unit_system):
    return "kW" if _unit_system_key(unit_system) == "metric" else "Btu/s"


def _turbine_entropy_unit(unit_system):
    if _unit_system_key(unit_system) == "metric":
        return "kJ/(kg*K)"
    return "Btu/(lbm*R)"


def _turbine_entropy_rate_unit(unit_system):
    if _unit_system_key(unit_system) == "metric":
        return "kW/K"
    return "Btu/(s*R)"


def _dead_state_temp_unit(unit_system):
    return "K" if _unit_system_key(unit_system) == "metric" else "R"


def _exergy_rate_unit(unit_system):
    return _turbine_power_unit(unit_system)


def _exergy_total_unit(unit_system):
    return "kJ" if _unit_system_key(unit_system) == "metric" else "Btu"


def _exergy_specific_unit(unit_system):
    return "kJ/kg" if _unit_system_key(unit_system) == "metric" else "Btu/lbm"


def _format_dead_state_temperature(value, unit_system):
    if value is None:
        return "T0 = u"
    t0 = float(value)
    if _unit_system_key(unit_system) == "metric":
        return "T0 = " + _display_number(t0 - 273.15) + " C = " + _display_number(t0) + " K"
    return "T0 = " + _display_number(t0 - 459.67) + " F = " + _display_number(t0) + " R"


def _solve_exergy_destruction(values):
    if values.get("ExD") is not None:
        return False
    t0 = _safe_float(values.get("T0"))
    sigma = _safe_float(values.get("sigma"))
    if t0 is None or sigma is None:
        return False
    values["ExD"] = t0 * sigma
    return True


def _check_t0_value(values, errors):
    t0 = _safe_float(values.get("T0"))
    if t0 is not None and t0 <= 0.0:
        errors.append("T0 must be an absolute temperature greater than 0.")


def _append_exergy_missing(values, solve_for, missing):
    if solve_for not in (None, "auto", "ExD"):
        return
    if values.get("ExD") is None:
        missing.append("Exergy destruction needs T0 and sigma.")


def _turbine_temp_key(unit_system, ideal_gas):
    if ideal_gas:
        return _ideal_gas_temp_key(unit_system)
    return get_temp_key(unit_system)


def _turbine_pressure_key(unit_system):
    return _ideal_gas_pressure_key(unit_system)


def _state_h(row, unit_system):
    if row is None or _is_error(row):
        return None
    keys = ("h_kJ_per_kg",) if _unit_system_key(unit_system) == "metric" else ("h_Btu_per_lb", "h_kJ_per_kg")
    for key in keys:
        if key in row:
            return _safe_float(row[key])
    return None


def _state_u(row, unit_system):
    if row is None or _is_error(row):
        return None
    keys = ("u_kJ_per_kg",) if _unit_system_key(unit_system) == "metric" else ("u_Btu_per_lb", "u_kJ_per_kg")
    for key in keys:
        if key in row:
            return _safe_float(row[key])
    return None


def _state_s(row, unit_system):
    if row is None or _is_error(row):
        return None
    if _unit_system_key(unit_system) == "metric":
        keys = ("s_kJ_per_kg_K",)
    else:
        keys = ("s_Btu_per_lb_R", "s_Btu_per_lbR", "s_kJ_per_kg_K")
    for key in keys:
        if key in row:
            return _safe_float(row[key])
    return None


def _state_v(row, unit_system):
    if row is None or _is_error(row):
        return None
    keys = ("v_m3_per_kg",) if _unit_system_key(unit_system) == "metric" else ("v_ft3_per_lb", "v_m3_per_kg")
    for key in keys:
        if key in row:
            return _safe_float(row[key])
    return None


def _quality_from_row(row):
    if row is None or _is_error(row):
        return None
    if "quality" in row:
        return _safe_float(row["quality"])
    region = str(row.get("region", "")).lower()
    if region == "saturated_liquid":
        return 0.0
    if region == "saturated_vapor":
        return 1.0
    return None


def _state_value(row, key):
    if row is None or _is_error(row):
        return None
    return _safe_float(row.get(key))


def _real_fluid_quality_state(fluid, unit_system, temp=None, pressure=None, quality=None):
    q = _safe_float(quality)
    if q is None:
        return None
    if q < 0.0 or q > 1.0:
        return _error_dict("Quality must be between 0 and 1.")

    temp_key = get_temp_key(unit_system)

    if pressure is not None:
        sat_row = gasLookUp(fluid, unit_system, pressure=pressure)
        if _is_error(sat_row):
            return sat_row
        if temp is not None and temp_key in sat_row:
            tol = 1e-4 * max(1.0, abs(float(temp)))
            if abs(float(sat_row[temp_key]) - float(temp)) > tol:
                return _error_dict("Quality requires a saturated state; T and P are not on the saturation line.")
    elif temp is not None:
        sat_row = gasLookUp(fluid, unit_system, temp=temp)
        if _is_error(sat_row):
            return sat_row
    else:
        return None

    f_key, g_key = _sat_property_keys_for_row(sat_row, "h")
    if f_key is None or g_key is None:
        return _error_dict("Could not resolve saturated quality from this state.")

    h_target = float(sat_row[f_key]) + q * (float(sat_row[g_key]) - float(sat_row[f_key]))
    return _sat_mixture_from_row(sat_row, "h", h_target)


def _ideal_gas_partial_temp_state(fluid, unit_system, temp):
    rows = _ideal_gas_table_rows_si(fluid)
    if not rows:
        return _error_dict("Caloric ideal-gas data are not available for this A-1 gas.")
    temp_k = _to_kelvin(temp, unit_system)
    interp = _interp_ideal_rows_by_temperature(rows, temp_k)
    if interp is None:
        return _error_dict("Temperature is outside the ideal-gas table range.")

    row = {
        "region": "ideal_gas_partial",
        "T_K": temp_k,
        "T_C": temp_k - 273.15,
        "T_R": temp_k * 9.0 / 5.0,
        "T_F": (temp_k - 273.15) * 9.0 / 5.0 + 32.0,
        "h_kJ_per_kg": interp["h_kJ_per_kg"],
        "u_kJ_per_kg": interp["u_kJ_per_kg"],
        "s0_kJ_per_kg_K": interp["s0_kJ_per_kg_K"],
        "ideal_gas": True,
    }
    return _add_ideal_gas_display_units(row, unit_system)


def _real_fluid_pressure_property_with_sat_boundary(fluid, unit_system, pressure, prop_symbol, prop_value):
    row = gasLookUp(fluid, unit_system, pressure=pressure, **_prop_kwargs(prop_symbol, prop_value))
    if row is not None and not _is_error(row):
        return row

    data = get_all_gas_data(fluid, unit_system)
    sat_p_rows = data.get("saturated_pressure", [])
    if not sat_p_rows:
        return row

    p_key = find_property_keys(sat_p_rows[0])["p"]
    temp_key = get_temp_key(unit_system)
    sat_row = _lookup_1d(sat_p_rows, pressure, p_key, "saturated_pressure")
    if sat_row is None:
        return row

    f_key, g_key = _sat_property_keys_for_row(sat_row, prop_symbol)
    if f_key is None or g_key is None:
        return row

    target = float(prop_value)
    yf = float(sat_row[f_key])
    yg = float(sat_row[g_key])

    if target >= yg:
        boundary = _sat_mixture_from_row(sat_row, prop_symbol, yg, sat_state="saturated vapor")
        candidates = _interpolate_candidates_at_fixed_axis(
            data.get("superheated", []), p_key, float(pressure), temp_key, "superheated"
        )
        if boundary is not None:
            candidates.append(boundary)
        prop_key = find_property_keys(boundary if boundary is not None else candidates[0])[prop_symbol] if candidates else None
        if prop_key is not None:
            out = _interpolate_from_candidates_by_property(candidates, prop_key, target, "superheated")
            if out is not None:
                return out

    if target <= yf:
        boundary = _sat_mixture_from_row(sat_row, prop_symbol, yf, sat_state="saturated liquid")
        candidates = _interpolate_candidates_at_fixed_axis(
            data.get("compressed", []), p_key, float(pressure), temp_key, "compressed"
        )
        if boundary is not None:
            candidates.append(boundary)
        prop_key = find_property_keys(boundary if boundary is not None else candidates[0])[prop_symbol] if candidates else None
        if prop_key is not None:
            out = _interpolate_from_candidates_by_property(candidates, prop_key, target, "compressed")
            if out is not None:
                return out

    return row


def _resolve_turbine_state(fluid, unit_system, ideal_gas, temp=None, pressure=None, quality=None, h=None, s=None):
    temp = _safe_float(temp)
    pressure = _safe_float(pressure)
    quality = _safe_float(quality)
    h = _safe_float(h)
    s = _safe_float(s)

    if ideal_gas:
        if quality is not None:
            return _error_dict("Quality is not defined for ideal gases.")
        if temp is not None and pressure is not None and h is not None:
            return idealGasLookUp(fluid, unit_system, temp=temp, pressure=pressure, h=h)
        if temp is not None and pressure is not None and s is not None:
            return idealGasLookUp(fluid, unit_system, temp=temp, pressure=pressure, s=s)
        if temp is not None and pressure is not None:
            return idealGasLookUp(fluid, unit_system, temp=temp, pressure=pressure)
        if h is not None and pressure is not None:
            return idealGasLookUp(fluid, unit_system, pressure=pressure, h=h)
        if s is not None and pressure is not None:
            return idealGasLookUp(fluid, unit_system, pressure=pressure, s=s)
        if s is not None and temp is not None:
            return idealGasLookUp(fluid, unit_system, temp=temp, s=s)
        if h is not None and temp is not None:
            row = _ideal_gas_partial_temp_state(fluid, unit_system, temp)
            actual_h = _state_h(row, unit_system)
            if actual_h is not None and not _close_enough(actual_h, h):
                return _error_dict("Inputs are inconsistent for ideal-gas enthalpy.")
            return row
        if temp is not None:
            return _ideal_gas_partial_temp_state(fluid, unit_system, temp)
        return None

    if quality is not None:
        return _real_fluid_quality_state(fluid, unit_system, temp=temp, pressure=pressure, quality=quality)
    if temp is not None and pressure is not None:
        return gasLookUp(fluid, unit_system, temp=temp, pressure=pressure)
    if h is not None and pressure is not None:
        return _real_fluid_pressure_property_with_sat_boundary(fluid, unit_system, pressure, "h", h)
    if h is not None and temp is not None:
        return gasLookUp(fluid, unit_system, temp=temp, h=h)
    if s is not None and pressure is not None:
        return _real_fluid_pressure_property_with_sat_boundary(fluid, unit_system, pressure, "s", s)
    if s is not None and temp is not None:
        return gasLookUp(fluid, unit_system, temp=temp, s=s)
    return None


def _resolve_piston_state(fluid, unit_system, ideal_gas, temp=None, pressure=None, quality=None, u=None, s=None, v=None):
    temp = _safe_float(temp)
    pressure = _safe_float(pressure)
    quality = _safe_float(quality)
    u = _safe_float(u)
    s = _safe_float(s)
    v = _safe_float(v)

    if ideal_gas:
        if quality is not None:
            return _error_dict("Quality is not defined for ideal gases.")
        if temp is not None and pressure is not None:
            row = idealGasLookUp(fluid, unit_system, temp=temp, pressure=pressure)
            if _is_error(row):
                return row
            checks = (
                ("u", _state_u(row, unit_system), u),
                ("s", _state_s(row, unit_system), s),
                ("v", _state_v(row, unit_system), v),
            )
            for name, actual, expected in checks:
                if expected is not None and actual is not None and not _close_enough(actual, expected):
                    return _error_dict("Inputs are inconsistent for ideal-gas " + name + ".")
            return row
        if pressure is not None and u is not None:
            return idealGasLookUp(fluid, unit_system, pressure=pressure, u=u)
        if pressure is not None and s is not None:
            return idealGasLookUp(fluid, unit_system, pressure=pressure, s=s)
        if pressure is not None and v is not None:
            return idealGasLookUp(fluid, unit_system, pressure=pressure, v=v)
        if temp is not None and s is not None:
            return idealGasLookUp(fluid, unit_system, temp=temp, s=s)
        if temp is not None and v is not None:
            return idealGasLookUp(fluid, unit_system, temp=temp, v=v)
        if temp is not None and u is not None:
            row = _ideal_gas_partial_temp_state(fluid, unit_system, temp)
            actual_u = _state_u(row, unit_system)
            if actual_u is not None and not _close_enough(actual_u, u):
                return _error_dict("Inputs are inconsistent for ideal-gas internal energy.")
            return row
        if temp is not None:
            return _ideal_gas_partial_temp_state(fluid, unit_system, temp)
        return None

    if quality is not None:
        return _real_fluid_quality_state(fluid, unit_system, temp=temp, pressure=pressure, quality=quality)
    if temp is not None and pressure is not None:
        return gasLookUp(fluid, unit_system, temp=temp, pressure=pressure)
    if u is not None and pressure is not None:
        return _real_fluid_pressure_property_with_sat_boundary(fluid, unit_system, pressure, "u", u)
    if u is not None and temp is not None:
        return gasLookUp(fluid, unit_system, temp=temp, u=u)
    if s is not None and pressure is not None:
        return _real_fluid_pressure_property_with_sat_boundary(fluid, unit_system, pressure, "s", s)
    if s is not None and temp is not None:
        return gasLookUp(fluid, unit_system, temp=temp, s=s)
    if v is not None and pressure is not None:
        return _real_fluid_pressure_property_with_sat_boundary(fluid, unit_system, pressure, "v", v)
    if v is not None and temp is not None:
        return gasLookUp(fluid, unit_system, temp=temp, v=v)
    return None


def _update_turbine_values_from_state(values, state_num, row, unit_system, ideal_gas):
    if row is None or _is_error(row):
        return False

    changed = False
    t_key = "T" + state_num
    p_key = "p" + state_num
    x_key = "x" + state_num

    temp_value = _state_value(row, _turbine_temp_key(unit_system, ideal_gas))
    if values.get(t_key) is None and temp_value is not None:
        values[t_key] = temp_value
        changed = True

    pressure_value = _state_value(row, _turbine_pressure_key(unit_system))
    if values.get(p_key) is None and pressure_value is not None:
        values[p_key] = pressure_value
        changed = True

    quality = _quality_from_row(row)
    if values.get(x_key) is None and quality is not None:
        values[x_key] = quality
        changed = True

    return changed


def _normalize_efficiency(value, notes):
    eta = _safe_float(value)
    if eta is None:
        return None
    if eta > 1.0 and eta <= 100.0:
        notes.append("Efficiency entered above 1 was interpreted as percent.")
        eta = eta / 100.0
    return eta


def _resolve_turbine_states(fluid, unit_system, ideal_gas, values, h_targets, s_targets):
    states = {"1": None, "2": None}
    errors = []

    for state_num in ("1", "2"):
        row = _resolve_turbine_state(
            fluid, unit_system, ideal_gas,
            temp=values.get("T" + state_num),
            pressure=values.get("p" + state_num),
            quality=values.get("x" + state_num),
            h=h_targets.get(state_num),
            s=s_targets.get(state_num),
        )
        if _is_error(row):
            errors.append(row)
            row = None
        states[state_num] = row
        _update_turbine_values_from_state(values, state_num, row, unit_system, ideal_gas)

    return states, errors


def _turbine_solve_for_options(ideal_gas, isentropic, adiabatic):
    options = [
        ("auto", "All possible"),
        ("T1", "T1"),
        ("p1", "P1"),
    ]
    if not ideal_gas:
        options.append(("x1", "x1"))
    options.extend([
        ("T2", "T2"),
        ("p2", "P2"),
    ])
    if not ideal_gas:
        options.append(("x2", "x2"))
    options.extend([
        ("mdot", "mdot"),
        ("W", "W"),
    ])
    if not isentropic:
        options.append(("efficiency", "efficiency"))
    if not adiabatic and not isentropic:
        options.append(("Q", "Q"))
    if not isentropic:
        options.extend([
            ("delta_s", "delta s"),
            ("Sdot", "Sdot"),
            ("sigma", "sigma"),
            ("ExD", "Exergy destruction"),
        ])
    return options


def _solve_for_needs_efficiency(solve_for):
    return solve_for in (None, "auto", "efficiency")


def _solve_for_needs_energy_balance(solve_for):
    return solve_for in (None, "auto", "mdot", "W", "Q", "T1", "T2", "p1", "p2", "x1", "x2")


def _solve_for_needs_entropy_rate(solve_for):
    return solve_for in ("Sdot", "sigma")


def _append_turbine_error(errors, message):
    text = str(message)
    if text == "No state found from temp plus property.":
        return
    if text not in errors:
        errors.append(text)


def _turbine_state_known(row, unit_system):
    return _state_h(row, unit_system) is not None


def _missing_state_info(state_num, ideal_gas):
    if ideal_gas:
        return (
            "State " + state_num +
            " needs enough data for h" + state_num +
            ": enter T" + state_num +
            ", or make it solvable from p" + state_num +
            " plus efficiency, delta s, or the energy balance."
        )
    return (
        "State " + state_num +
        " needs enough data for h" + state_num +
        ": use T" + state_num + "+p" + state_num +
        ", T" + state_num + "+x" + state_num +
        ", or p" + state_num + "+x" + state_num + "."
    )


def _close_enough(a, b, tol=1e-5):
    if a is None or b is None:
        return True
    scale = max(1.0, abs(float(a)), abs(float(b)))
    return abs(float(a) - float(b)) <= tol * scale


def _solve_entropy_rate_values(values, adiabatic, isentropic):
    changed = False

    if isentropic:
        if values.get("Sdot") is None:
            values["Sdot"] = 0.0
            changed = True
        if values.get("sigma") is None:
            values["sigma"] = 0.0
            changed = True
        return changed

    for _ in range(3):
        loop_changed = False
        mdot = _safe_float(values.get("mdot"))
        delta_s = _safe_float(values.get("delta_s"))
        sdot = _safe_float(values.get("Sdot"))
        sigma = _safe_float(values.get("sigma"))

        if values.get("Sdot") is None and mdot is not None and delta_s is not None:
            values["Sdot"] = mdot * delta_s
            loop_changed = True
        elif values.get("delta_s") is None and sdot is not None and mdot not in (None, 0):
            values["delta_s"] = sdot / mdot
            loop_changed = True
        elif values.get("mdot") is None and sdot is not None and delta_s not in (None, 0):
            values["mdot"] = sdot / delta_s
            loop_changed = True

        if adiabatic:
            sdot = _safe_float(values.get("Sdot"))
            sigma = _safe_float(values.get("sigma"))
            if values.get("sigma") is None and sdot is not None:
                values["sigma"] = sdot
                loop_changed = True
            elif values.get("Sdot") is None and sigma is not None:
                values["Sdot"] = sigma
                loop_changed = True

        if not loop_changed:
            break
        changed = True

    return changed


def _check_entropy_rate_values(values, adiabatic, errors):
    mdot = _safe_float(values.get("mdot"))
    delta_s = _safe_float(values.get("delta_s"))
    sdot = _safe_float(values.get("Sdot"))
    sigma = _safe_float(values.get("sigma"))

    if mdot is not None and delta_s is not None and sdot is not None:
        expected = mdot * delta_s
        if not _close_enough(sdot, expected):
            _append_turbine_error(errors, "Sdot must equal mdot * delta s.")

    if adiabatic and sdot is not None and sigma is not None:
        if not _close_enough(sigma, sdot):
            _append_turbine_error(errors, "For an adiabatic steady-flow device, sigma must equal Sdot.")


def _append_entropy_rate_missing(values, solve_for, adiabatic, missing):
    if not _solve_for_needs_entropy_rate(solve_for):
        return

    if solve_for == "Sdot" and values.get("Sdot") is None:
        missing.append("Sdot needs mdot and delta s, or an input value.")

    if solve_for == "sigma" and values.get("sigma") is None:
        if adiabatic:
            missing.append("Sigma needs mdot and delta s, Sdot, or an input value.")
        else:
            missing.append("Sigma needs an input value unless the device is adiabatic.")


def solve_turbine(fluid, unit_system, ideal_gas, isentropic, adiabatic, values, solve_for="auto"):
    values = values.copy()
    notes = []
    errors = []
    missing = []
    solve_for = "auto" if solve_for is None else str(solve_for)

    values["efficiency"] = _normalize_efficiency(values.get("efficiency"), notes)

    if values.get("efficiency") is not None:
        eta = float(values["efficiency"])
        if eta < 0.0 or eta > 1.0:
            errors.append("Efficiency must be between 0 and 1, or 0 and 100 percent.")

    if values.get("mdot") is not None and float(values["mdot"]) < 0.0:
        errors.append("Mass flow rate must be positive.")
    _check_t0_value(values, errors)

    if isentropic:
        adiabatic = True
        if values.get("delta_s") is not None and not _close_enough(values.get("delta_s"), 0.0):
            errors.append("Isentropic turbine states require delta s = 0.")
        values["delta_s"] = 0.0
        if values.get("Sdot") is not None and not _close_enough(values.get("Sdot"), 0.0):
            errors.append("Isentropic turbine states require Sdot = 0.")
        values["Sdot"] = 0.0
        if values.get("sigma") is not None and not _close_enough(values.get("sigma"), 0.0):
            errors.append("Isentropic turbine states require sigma = 0.")
        values["sigma"] = 0.0
        if values.get("Q") is not None and not _close_enough(values.get("Q"), 0.0):
            errors.append("Isentropic turbine states are treated as adiabatic, so Q must be 0.")
        values["Q"] = 0.0
        if values.get("efficiency") is None:
            values["efficiency"] = 1.0
        elif not _close_enough(values.get("efficiency"), 1.0):
            errors.append("An isentropic turbine has efficiency = 1.")
        values["ExD"] = 0.0

    if adiabatic:
        if values.get("Q") is not None and not _close_enough(values.get("Q"), 0.0):
            errors.append("Adiabatic turbine states require Q = 0.")
        values["Q"] = 0.0

    if ideal_gas:
        values["x1"] = None
        values["x2"] = None
    else:
        values.setdefault("x1", None)
        values.setdefault("x2", None)
    values.setdefault("Sdot", None)
    values.setdefault("sigma", None)
    values.setdefault("T0", None)
    values.setdefault("ExD", None)

    h_targets = {"1": None, "2": None}
    s_targets = {"1": None, "2": None}
    states = {"1": None, "2": None}
    state2s = None

    for _ in range(6):
        changed = False
        states, state_errors = _resolve_turbine_states(
            fluid, unit_system, ideal_gas, values, h_targets, s_targets
        )
        for err in state_errors:
            _append_turbine_error(errors, err["error"])

        h1 = _state_h(states["1"], unit_system)
        h2 = _state_h(states["2"], unit_system)
        s1 = _state_s(states["1"], unit_system)
        s2 = _state_s(states["2"], unit_system)

        if values.get("delta_s") is None and s1 is not None and s2 is not None:
            values["delta_s"] = s2 - s1
            changed = True

        if values.get("delta_s") is not None:
            ds = float(values["delta_s"])
            if s1 is not None and s_targets["2"] is None:
                s_targets["2"] = s1 + ds
                changed = True
            if s2 is not None and s_targets["1"] is None:
                s_targets["1"] = s2 - ds
                changed = True

        if _solve_entropy_rate_values(values, adiabatic, isentropic):
            changed = True
        if _solve_exergy_destruction(values):
            changed = True

        if s1 is not None and values.get("p2") is not None:
            state2s = _resolve_turbine_state(
                fluid, unit_system, ideal_gas,
                pressure=values.get("p2"), s=s1
            )
            if _is_error(state2s):
                state2s = None
            h2s = _state_h(state2s, unit_system)
            if h1 is not None and h2s is not None:
                eta = values.get("efficiency")
                denom = h1 - h2s
                if isentropic or (eta is not None and _close_enough(eta, 1.0)):
                    if h_targets["2"] is None:
                        h_targets["2"] = h2s
                        changed = True
                    if not _turbine_state_known(states["2"], unit_system):
                        states["2"] = state2s
                        _update_turbine_values_from_state(values, "2", state2s, unit_system, ideal_gas)
                        changed = True
                elif eta is not None and h_targets["2"] is None:
                    h_targets["2"] = h1 - float(eta) * denom
                    changed = True
                elif eta is None and h2 is not None and abs(denom) > 1e-12:
                    values["efficiency"] = (h1 - h2) / denom
                    changed = True

        h1 = _state_h(states["1"], unit_system)
        h2 = _state_h(states["2"], unit_system)
        mdot = values.get("mdot")
        work = values.get("W")
        heat = values.get("Q")

        if h1 is not None and h2 is not None:
            dh = h1 - h2
            if work is None and mdot is not None and heat is not None:
                values["W"] = float(mdot) * dh + float(heat)
                changed = True
            elif heat is None and mdot is not None and work is not None:
                values["Q"] = float(work) - float(mdot) * dh
                changed = True
            elif mdot is None and work is not None and heat is not None and abs(dh) > 1e-12:
                values["mdot"] = (float(work) - float(heat)) / dh
                changed = True
        elif h1 is not None and h2 is None and mdot is not None and work is not None and heat is not None:
            if float(mdot) != 0.0 and h_targets["2"] is None:
                h_targets["2"] = h1 - (float(work) - float(heat)) / float(mdot)
                changed = True
        elif h2 is not None and h1 is None and mdot is not None and work is not None and heat is not None:
            if float(mdot) != 0.0 and h_targets["1"] is None:
                h_targets["1"] = h2 + (float(work) - float(heat)) / float(mdot)
                changed = True

        if not changed:
            break

    states, state_errors = _resolve_turbine_states(
        fluid, unit_system, ideal_gas, values, h_targets, s_targets
    )
    for err in state_errors:
        _append_turbine_error(errors, err["error"])

    h1 = _state_h(states["1"], unit_system)
    h2 = _state_h(states["2"], unit_system)
    s1 = _state_s(states["1"], unit_system)
    s2 = _state_s(states["2"], unit_system)

    if values.get("delta_s") is None and s1 is not None and s2 is not None:
        values["delta_s"] = s2 - s1
    _solve_entropy_rate_values(values, adiabatic, isentropic)
    _solve_exergy_destruction(values)
    _check_entropy_rate_values(values, adiabatic, errors)

    if s1 is not None and values.get("delta_s") is not None and s2 is not None:
        expected_s2 = s1 + float(values["delta_s"])
        if not _close_enough(s2, expected_s2):
            errors.append("State entropies do not match the supplied delta s.")

    if h_targets["1"] is not None and h1 is not None and not _close_enough(h1, h_targets["1"]):
        errors.append("State 1 does not match the enthalpy required by the turbine balance.")
    if h_targets["2"] is not None and h2 is not None and not _close_enough(h2, h_targets["2"]):
        errors.append("State 2 does not match the enthalpy required by the turbine balance.")

    if h_targets["1"] is not None and values.get("T1") is not None and h1 is None:
        errors.append("No state 1 matches the solved h1 at the given T1.")
    if h_targets["2"] is not None and values.get("T2") is not None and h2 is None:
        errors.append("No state 2 matches the solved h2 at the given T2.")

    state1_has_failed_target = h_targets["1"] is not None and values.get("T1") is not None
    state2_has_failed_target = h_targets["2"] is not None and values.get("T2") is not None

    if not state1_has_failed_target and not _turbine_state_known(states["1"], unit_system) and solve_for in ("auto", "T1", "p1", "x1", "p2", "mdot", "W", "Q", "efficiency", "delta_s", "Sdot", "sigma"):
        missing.append(_missing_state_info("1", ideal_gas))
    if not state2_has_failed_target and not _turbine_state_known(states["2"], unit_system) and solve_for in ("auto", "T2", "p2", "x2", "mdot", "W", "Q", "efficiency", "delta_s", "Sdot", "sigma"):
        missing.append(_missing_state_info("2", ideal_gas))

    if _solve_for_needs_energy_balance(solve_for) and (values.get("W") is None or values.get("mdot") is None or values.get("Q") is None):
        if h1 is None or h2 is None:
            missing.append("Energy balance also needs both state enthalpies.")
        else:
            missing.append("Energy balance needs any two of mdot, W, and Q.")

    if values.get("efficiency") is None and not isentropic and _solve_for_needs_efficiency(solve_for):
        if s1 is None or values.get("p2") is None:
            if s1 is None:
                if ideal_gas:
                    missing.append("Efficiency needs p1 with T1 to determine state 1 entropy.")
                else:
                    missing.append("Efficiency needs state 1 entropy from T1+p1, T1+x1, or p1+x1.")
            if values.get("p2") is None:
                missing.append("Efficiency needs p2 to find the isentropic outlet state.")
        elif h2 is None:
            missing.append("Efficiency needs the actual outlet state or an efficiency input.")

    _append_entropy_rate_missing(values, solve_for, adiabatic, missing)
    if not isentropic:
        _append_exergy_missing(values, solve_for, missing)

    if ideal_gas:
        values["x1"] = None
        values["x2"] = None

    return {
        "values": values,
        "states": states,
        "state2s": state2s,
        "errors": errors,
        "missing": missing,
        "notes": notes,
        "ideal_gas": ideal_gas,
        "isentropic": isentropic,
        "adiabatic": adiabatic,
        "unit_system": unit_system,
        "solve_for": solve_for,
    }


def solve_compressor(fluid, unit_system, ideal_gas, isentropic, adiabatic, values, solve_for="auto"):
    values = values.copy()
    notes = []
    errors = []
    missing = []
    solve_for = "auto" if solve_for is None else str(solve_for)

    values["efficiency"] = _normalize_efficiency(values.get("efficiency"), notes)

    if values.get("efficiency") is not None:
        eta = float(values["efficiency"])
        if eta <= 0.0 or eta > 1.0:
            errors.append("Compressor efficiency must be greater than 0 and no more than 1, or 0 and 100 percent.")

    if values.get("mdot") is not None and float(values["mdot"]) < 0.0:
        errors.append("Mass flow rate must be positive.")
    _check_t0_value(values, errors)

    if isentropic:
        adiabatic = True
        if values.get("delta_s") is not None and not _close_enough(values.get("delta_s"), 0.0):
            errors.append("Isentropic compressor states require delta s = 0.")
        values["delta_s"] = 0.0
        if values.get("Sdot") is not None and not _close_enough(values.get("Sdot"), 0.0):
            errors.append("Isentropic compressor states require Sdot = 0.")
        values["Sdot"] = 0.0
        if values.get("sigma") is not None and not _close_enough(values.get("sigma"), 0.0):
            errors.append("Isentropic compressor states require sigma = 0.")
        values["sigma"] = 0.0
        if values.get("Q") is not None and not _close_enough(values.get("Q"), 0.0):
            errors.append("Isentropic compressor states are treated as adiabatic, so Q must be 0.")
        values["Q"] = 0.0
        if values.get("efficiency") is None:
            values["efficiency"] = 1.0
        elif not _close_enough(values.get("efficiency"), 1.0):
            errors.append("An isentropic compressor has efficiency = 1.")
        values["ExD"] = 0.0

    if adiabatic:
        if values.get("Q") is not None and not _close_enough(values.get("Q"), 0.0):
            errors.append("Adiabatic compressor states require Q = 0.")
        values["Q"] = 0.0

    if ideal_gas:
        values["x1"] = None
        values["x2"] = None
    else:
        values.setdefault("x1", None)
        values.setdefault("x2", None)
    values.setdefault("Sdot", None)
    values.setdefault("sigma", None)
    values.setdefault("T0", None)
    values.setdefault("ExD", None)

    h_targets = {"1": None, "2": None}
    s_targets = {"1": None, "2": None}
    states = {"1": None, "2": None}
    state2s = None

    for _ in range(6):
        changed = False
        states, state_errors = _resolve_turbine_states(
            fluid, unit_system, ideal_gas, values, h_targets, s_targets
        )
        for err in state_errors:
            _append_turbine_error(errors, err["error"])

        h1 = _state_h(states["1"], unit_system)
        h2 = _state_h(states["2"], unit_system)
        s1 = _state_s(states["1"], unit_system)
        s2 = _state_s(states["2"], unit_system)

        if values.get("delta_s") is None and s1 is not None and s2 is not None:
            values["delta_s"] = s2 - s1
            changed = True

        if values.get("delta_s") is not None:
            ds = float(values["delta_s"])
            if s1 is not None and s_targets["2"] is None:
                s_targets["2"] = s1 + ds
                changed = True
            if s2 is not None and s_targets["1"] is None:
                s_targets["1"] = s2 - ds
                changed = True

        if _solve_entropy_rate_values(values, adiabatic, isentropic):
            changed = True
        if _solve_exergy_destruction(values):
            changed = True

        if s1 is not None and values.get("p2") is not None:
            state2s = _resolve_turbine_state(
                fluid, unit_system, ideal_gas,
                pressure=values.get("p2"), s=s1
            )
            if _is_error(state2s):
                state2s = None
            h2s = _state_h(state2s, unit_system)
            if h1 is not None and h2s is not None:
                eta = values.get("efficiency")
                ideal_dh = h2s - h1
                if isentropic or (eta is not None and _close_enough(eta, 1.0)):
                    if h_targets["2"] is None:
                        h_targets["2"] = h2s
                        changed = True
                    if not _turbine_state_known(states["2"], unit_system):
                        states["2"] = state2s
                        _update_turbine_values_from_state(values, "2", state2s, unit_system, ideal_gas)
                        changed = True
                elif eta is not None and float(eta) > 0.0 and h_targets["2"] is None:
                    h_targets["2"] = h1 + ideal_dh / float(eta)
                    changed = True
                elif eta is None and h2 is not None:
                    actual_dh = h2 - h1
                    if abs(actual_dh) > 1e-12:
                        values["efficiency"] = ideal_dh / actual_dh
                        changed = True

        h1 = _state_h(states["1"], unit_system)
        h2 = _state_h(states["2"], unit_system)
        mdot = values.get("mdot")
        work = values.get("W")
        heat = values.get("Q")

        if h1 is not None and h2 is not None:
            dh = h2 - h1
            if work is None and mdot is not None and heat is not None:
                values["W"] = float(mdot) * dh - float(heat)
                changed = True
            elif heat is None and mdot is not None and work is not None:
                values["Q"] = float(mdot) * dh - float(work)
                changed = True
            elif mdot is None and work is not None and heat is not None and abs(dh) > 1e-12:
                values["mdot"] = (float(work) + float(heat)) / dh
                changed = True
        elif h1 is not None and h2 is None and mdot is not None and work is not None and heat is not None:
            if float(mdot) != 0.0 and h_targets["2"] is None:
                h_targets["2"] = h1 + (float(work) + float(heat)) / float(mdot)
                changed = True
        elif h2 is not None and h1 is None and mdot is not None and work is not None and heat is not None:
            if float(mdot) != 0.0 and h_targets["1"] is None:
                h_targets["1"] = h2 - (float(work) + float(heat)) / float(mdot)
                changed = True

        if not changed:
            break

    states, state_errors = _resolve_turbine_states(
        fluid, unit_system, ideal_gas, values, h_targets, s_targets
    )
    for err in state_errors:
        _append_turbine_error(errors, err["error"])

    h1 = _state_h(states["1"], unit_system)
    h2 = _state_h(states["2"], unit_system)
    s1 = _state_s(states["1"], unit_system)
    s2 = _state_s(states["2"], unit_system)

    if values.get("delta_s") is None and s1 is not None and s2 is not None:
        values["delta_s"] = s2 - s1
    _solve_entropy_rate_values(values, adiabatic, isentropic)
    _solve_exergy_destruction(values)
    _check_entropy_rate_values(values, adiabatic, errors)

    if s1 is not None and values.get("delta_s") is not None and s2 is not None:
        expected_s2 = s1 + float(values["delta_s"])
        if not _close_enough(s2, expected_s2):
            errors.append("State entropies do not match the supplied delta s.")

    if h_targets["1"] is not None and h1 is not None and not _close_enough(h1, h_targets["1"]):
        errors.append("State 1 does not match the enthalpy required by the compressor balance.")
    if h_targets["2"] is not None and h2 is not None and not _close_enough(h2, h_targets["2"]):
        errors.append("State 2 does not match the enthalpy required by the compressor balance.")

    if h_targets["1"] is not None and values.get("T1") is not None and h1 is None:
        errors.append("No state 1 matches the solved h1 at the given T1.")
    if h_targets["2"] is not None and values.get("T2") is not None and h2 is None:
        errors.append("No state 2 matches the solved h2 at the given T2.")

    state1_has_failed_target = h_targets["1"] is not None and values.get("T1") is not None
    state2_has_failed_target = h_targets["2"] is not None and values.get("T2") is not None

    if not state1_has_failed_target and not _turbine_state_known(states["1"], unit_system) and solve_for in ("auto", "T1", "p1", "x1", "p2", "mdot", "W", "Q", "efficiency", "delta_s", "Sdot", "sigma"):
        missing.append(_missing_state_info("1", ideal_gas))
    if not state2_has_failed_target and not _turbine_state_known(states["2"], unit_system) and solve_for in ("auto", "T2", "p2", "x2", "mdot", "W", "Q", "efficiency", "delta_s", "Sdot", "sigma"):
        missing.append(_missing_state_info("2", ideal_gas))

    if _solve_for_needs_energy_balance(solve_for) and (values.get("W") is None or values.get("mdot") is None or values.get("Q") is None):
        if h1 is None or h2 is None:
            missing.append("Energy balance also needs both state enthalpies.")
        else:
            missing.append("Energy balance needs any two of mdot, W, and Q.")

    if values.get("efficiency") is None and not isentropic and _solve_for_needs_efficiency(solve_for):
        if s1 is None or values.get("p2") is None:
            if s1 is None:
                if ideal_gas:
                    missing.append("Efficiency needs p1 with T1 to determine state 1 entropy.")
                else:
                    missing.append("Efficiency needs state 1 entropy from T1+p1, T1+x1, or p1+x1.")
            if values.get("p2") is None:
                missing.append("Efficiency needs p2 to find the isentropic outlet state.")
        elif h2 is None:
            missing.append("Efficiency needs the actual outlet state or an efficiency input.")

    _append_entropy_rate_missing(values, solve_for, adiabatic, missing)
    if not isentropic:
        _append_exergy_missing(values, solve_for, missing)

    if ideal_gas:
        values["x1"] = None
        values["x2"] = None

    return {
        "values": values,
        "states": states,
        "state2s": state2s,
        "errors": errors,
        "missing": missing,
        "notes": notes,
        "ideal_gas": ideal_gas,
        "isentropic": isentropic,
        "adiabatic": adiabatic,
        "unit_system": unit_system,
        "solve_for": solve_for,
    }


def _piston_volume_unit(unit_system):
    return "m^3" if _unit_system_key(unit_system) == "metric" else "ft^3"


def _piston_area_unit(unit_system):
    return "m^2" if _unit_system_key(unit_system) == "metric" else "ft^2"


def _piston_mass_unit(unit_system):
    return "kg" if _unit_system_key(unit_system) == "metric" else "lbm"


def _piston_energy_unit(unit_system):
    return "kJ" if _unit_system_key(unit_system) == "metric" else "Btu"


def _piston_entropy_total_unit(unit_system):
    return "kJ/K" if _unit_system_key(unit_system) == "metric" else "Btu/R"


def _piston_pressure_work_factor(unit_system):
    if _unit_system_key(unit_system) == "metric":
        return 100.0
    return 144.0 / 778.169262


def _piston_boundary_pressure(values):
    p1 = _safe_float(values.get("p1"))
    p2 = _safe_float(values.get("p2"))
    if p1 is not None and p2 is not None:
        return 0.5 * (p1 + p2)
    if p1 is not None:
        return p1
    if p2 is not None:
        return p2
    return None


def _piston_solve_for_options(ideal_gas, isentropic, adiabatic):
    options = [
        ("auto", "All possible"),
        ("T1", "T1"),
        ("p1", "P1"),
    ]
    if not ideal_gas:
        options.append(("x1", "x1"))
    options.extend([
        ("V1", "V1"),
        ("T2", "T2"),
        ("p2", "P2"),
    ])
    if not ideal_gas:
        options.append(("x2", "x2"))
    options.extend([
        ("V2", "V2"),
        ("A", "A"),
        ("m", "m"),
        ("W", "W"),
    ])
    if not adiabatic and not isentropic:
        options.append(("Q", "Q"))
    if not isentropic:
        options.extend([
            ("delta_s", "delta s"),
            ("Sdot", "Sdot"),
            ("sigma", "sigma"),
            ("ExD", "Exergy destruction"),
        ])
    return options


def _resolve_piston_states(fluid, unit_system, ideal_gas, values, u_targets, s_targets, v_targets):
    states = {"1": None, "2": None}
    errors = []
    for state_num in ("1", "2"):
        row = _resolve_piston_state(
            fluid, unit_system, ideal_gas,
            temp=values.get("T" + state_num),
            pressure=values.get("p" + state_num),
            quality=values.get("x" + state_num),
            u=u_targets.get(state_num),
            s=s_targets.get(state_num),
            v=v_targets.get(state_num),
        )
        if _is_error(row):
            errors.append(row)
            row = None
        states[state_num] = row
        _update_turbine_values_from_state(values, state_num, row, unit_system, ideal_gas)
    return states, errors


def _solve_piston_volume_values(values, states, v_targets):
    changed = False
    mass = _safe_float(values.get("m"))
    for state_num in ("1", "2"):
        total_key = "V" + state_num
        total_volume = _safe_float(values.get(total_key))
        specific_volume = _state_v(states.get(state_num), values.get("_unit_system", "SI"))
        if specific_volume is not None:
            if values.get(total_key) is None and mass is not None:
                values[total_key] = mass * specific_volume
                total_volume = values[total_key]
                changed = True
            elif values.get("m") is None and total_volume is not None and specific_volume != 0.0:
                values["m"] = total_volume / specific_volume
                mass = values["m"]
                changed = True
        if v_targets.get(state_num) is None and total_volume is not None and mass not in (None, 0):
            v_targets[state_num] = total_volume / mass
            changed = True
    return changed


def _solve_piston_boundary_work(values, unit_system, notes):
    changed = False
    pressure = _piston_boundary_pressure(values)
    V1 = _safe_float(values.get("V1"))
    V2 = _safe_float(values.get("V2"))
    W = _safe_float(values.get("W"))
    if pressure is None or pressure == 0.0:
        return False
    factor = _piston_pressure_work_factor(unit_system)
    if W is None and V1 is not None and V2 is not None:
        values["W"] = factor * pressure * (V2 - V1)
        changed = True
    elif V2 is None and W is not None and V1 is not None:
        values["V2"] = V1 + W / (factor * pressure)
        changed = True
    elif V1 is None and W is not None and V2 is not None:
        values["V1"] = V2 - W / (factor * pressure)
        changed = True
    p1 = _safe_float(values.get("p1"))
    p2 = _safe_float(values.get("p2"))
    if p1 is not None and p2 is not None and not _close_enough(p1, p2):
        note = "Boundary work used average pressure, assuming a linear quasi-equilibrium P-V path."
        if note not in notes:
            notes.append(note)
    return changed


def _solve_piston_entropy_values(values, adiabatic, isentropic):
    changed = False
    if isentropic:
        for key in ("Sdot", "sigma"):
            if values.get(key) is None:
                values[key] = 0.0
                changed = True
        return changed

    for _ in range(3):
        loop_changed = False
        mass = _safe_float(values.get("m"))
        delta_s = _safe_float(values.get("delta_s"))
        sdot = _safe_float(values.get("Sdot"))
        sigma = _safe_float(values.get("sigma"))

        if values.get("Sdot") is None and mass is not None and delta_s is not None:
            values["Sdot"] = mass * delta_s
            loop_changed = True
        elif values.get("delta_s") is None and sdot is not None and mass not in (None, 0):
            values["delta_s"] = sdot / mass
            loop_changed = True
        elif values.get("m") is None and sdot is not None and delta_s not in (None, 0):
            values["m"] = sdot / delta_s
            loop_changed = True

        if adiabatic:
            sdot = _safe_float(values.get("Sdot"))
            sigma = _safe_float(values.get("sigma"))
            if values.get("sigma") is None and sdot is not None:
                values["sigma"] = sdot
                loop_changed = True
            elif values.get("Sdot") is None and sigma is not None:
                values["Sdot"] = sigma
                loop_changed = True

        if not loop_changed:
            break
        changed = True
    return changed


def _check_piston_entropy_values(values, adiabatic, errors):
    mass = _safe_float(values.get("m"))
    delta_s = _safe_float(values.get("delta_s"))
    sdot = _safe_float(values.get("Sdot"))
    sigma = _safe_float(values.get("sigma"))
    if mass is not None and delta_s is not None and sdot is not None:
        expected = mass * delta_s
        if not _close_enough(sdot, expected):
            _append_turbine_error(errors, "Sdot must equal m * delta s for the piston process.")
    if adiabatic and sdot is not None and sigma is not None and not _close_enough(sigma, sdot):
        _append_turbine_error(errors, "For an adiabatic closed-system piston, sigma must equal Sdot.")


def _solve_piston_energy_balance(values, states, u_targets):
    changed = False
    u1 = _state_u(states.get("1"), values.get("_unit_system", "SI"))
    u2 = _state_u(states.get("2"), values.get("_unit_system", "SI"))
    mass = _safe_float(values.get("m"))
    work = _safe_float(values.get("W"))
    heat = _safe_float(values.get("Q"))

    if u1 is not None and u2 is not None:
        du = u2 - u1
        if values.get("W") is None and mass is not None and heat is not None:
            values["W"] = heat - mass * du
            changed = True
        elif values.get("Q") is None and mass is not None and work is not None:
            values["Q"] = mass * du + work
            changed = True
        elif values.get("m") is None and work is not None and heat is not None and abs(du) > 1e-12:
            values["m"] = (heat - work) / du
            changed = True
    elif u1 is not None and u2 is None and mass not in (None, 0) and work is not None and heat is not None:
        if u_targets.get("2") is None:
            u_targets["2"] = u1 + (heat - work) / mass
            changed = True
    elif u2 is not None and u1 is None and mass not in (None, 0) and work is not None and heat is not None:
        if u_targets.get("1") is None:
            u_targets["1"] = u2 - (heat - work) / mass
            changed = True
    return changed


def _piston_state_known(row, unit_system):
    return _state_u(row, unit_system) is not None


def _missing_piston_state_info(state_num, ideal_gas):
    if ideal_gas:
        return (
            "State " + state_num +
            " needs enough data for u" + state_num +
            ": use T" + state_num +
            ", or p" + state_num + "+v" + state_num +
            ", p" + state_num + "+s" + state_num +
            ", or the piston energy balance."
        )
    return (
        "State " + state_num +
        " needs enough data for u" + state_num +
        ": use T" + state_num + "+p" + state_num +
        ", T" + state_num + "+x" + state_num +
        ", p" + state_num + "+x" + state_num +
        ", p" + state_num + "+v" + state_num +
        ", or T" + state_num + "+v" + state_num + "."
    )


def _solve_for_needs_piston_energy(solve_for):
    return solve_for in (None, "auto", "m", "W", "Q", "T1", "T2", "p1", "p2", "x1", "x2", "V1", "V2")


def _append_piston_entropy_missing(values, solve_for, adiabatic, missing):
    if solve_for == "Sdot" and values.get("Sdot") is None:
        missing.append("Sdot needs m and delta s, or an input value.")
    if solve_for == "sigma" and values.get("sigma") is None:
        if adiabatic:
            missing.append("Sigma needs m and delta s, Sdot, or an input value.")
        else:
            missing.append("Sigma needs an input value unless the piston process is adiabatic.")


def solve_piston(fluid, unit_system, ideal_gas, isentropic, adiabatic, values, solve_for="auto"):
    values = values.copy()
    values["_unit_system"] = unit_system
    notes = []
    errors = []
    missing = []
    solve_for = "auto" if solve_for is None else str(solve_for)

    if values.get("m") is not None and float(values["m"]) < 0.0:
        errors.append("Mass must be positive.")
    if values.get("A") is not None and float(values["A"]) < 0.0:
        errors.append("Piston area must be positive.")
    _check_t0_value(values, errors)

    if isentropic:
        adiabatic = True
        if values.get("delta_s") is not None and not _close_enough(values.get("delta_s"), 0.0):
            errors.append("Isentropic piston states require delta s = 0.")
        values["delta_s"] = 0.0
        if values.get("Sdot") is not None and not _close_enough(values.get("Sdot"), 0.0):
            errors.append("Isentropic piston states require Sdot = 0.")
        values["Sdot"] = 0.0
        if values.get("sigma") is not None and not _close_enough(values.get("sigma"), 0.0):
            errors.append("Isentropic piston states require sigma = 0.")
        values["sigma"] = 0.0
        if values.get("Q") is not None and not _close_enough(values.get("Q"), 0.0):
            errors.append("Isentropic piston states are treated as adiabatic, so Q must be 0.")
        values["Q"] = 0.0
        values["ExD"] = 0.0

    if adiabatic:
        if values.get("Q") is not None and not _close_enough(values.get("Q"), 0.0):
            errors.append("Adiabatic piston states require Q = 0.")
        values["Q"] = 0.0

    if ideal_gas:
        values["x1"] = None
        values["x2"] = None
    else:
        values.setdefault("x1", None)
        values.setdefault("x2", None)
    for key in ("V1", "V2", "A", "m", "W", "Q", "delta_s", "Sdot", "sigma"):
        values.setdefault(key, None)
    values.setdefault("T0", None)
    values.setdefault("ExD", None)

    u_targets = {"1": None, "2": None}
    s_targets = {"1": None, "2": None}
    v_targets = {"1": None, "2": None}
    states = {"1": None, "2": None}

    for _ in range(8):
        changed = False
        if _solve_piston_volume_values(values, states, v_targets):
            changed = True
        states, state_errors = _resolve_piston_states(
            fluid, unit_system, ideal_gas, values, u_targets, s_targets, v_targets
        )
        for err in state_errors:
            _append_turbine_error(errors, err["error"])
        if _solve_piston_volume_values(values, states, v_targets):
            changed = True

        s1 = _state_s(states["1"], unit_system)
        s2 = _state_s(states["2"], unit_system)
        if values.get("delta_s") is None and s1 is not None and s2 is not None:
            values["delta_s"] = s2 - s1
            changed = True
        if values.get("delta_s") is not None:
            ds = float(values["delta_s"])
            if s1 is not None and s_targets["2"] is None:
                s_targets["2"] = s1 + ds
                changed = True
            if s2 is not None and s_targets["1"] is None:
                s_targets["1"] = s2 - ds
                changed = True

        if _solve_piston_entropy_values(values, adiabatic, isentropic):
            changed = True
        if _solve_exergy_destruction(values):
            changed = True
        if _solve_piston_boundary_work(values, unit_system, notes):
            changed = True
        if _solve_piston_energy_balance(values, states, u_targets):
            changed = True
        if not changed:
            break

    states, state_errors = _resolve_piston_states(
        fluid, unit_system, ideal_gas, values, u_targets, s_targets, v_targets
    )
    for err in state_errors:
        _append_turbine_error(errors, err["error"])
    _solve_piston_volume_values(values, states, v_targets)

    u1 = _state_u(states["1"], unit_system)
    u2 = _state_u(states["2"], unit_system)
    s1 = _state_s(states["1"], unit_system)
    s2 = _state_s(states["2"], unit_system)
    if values.get("delta_s") is None and s1 is not None and s2 is not None:
        values["delta_s"] = s2 - s1
    _solve_piston_entropy_values(values, adiabatic, isentropic)
    _solve_exergy_destruction(values)
    _check_piston_entropy_values(values, adiabatic, errors)

    if s1 is not None and values.get("delta_s") is not None and s2 is not None:
        expected_s2 = s1 + float(values["delta_s"])
        if not _close_enough(s2, expected_s2):
            errors.append("State entropies do not match the supplied delta s.")
    if u_targets["1"] is not None and u1 is not None and not _close_enough(u1, u_targets["1"]):
        errors.append("State 1 does not match the internal energy required by the piston balance.")
    if u_targets["2"] is not None and u2 is not None and not _close_enough(u2, u_targets["2"]):
        errors.append("State 2 does not match the internal energy required by the piston balance.")

    needed = ("auto", "T1", "p1", "x1", "V1", "T2", "p2", "x2", "V2", "m", "W", "Q", "delta_s", "Sdot", "sigma")
    if not _piston_state_known(states["1"], unit_system) and solve_for in needed:
        missing.append(_missing_piston_state_info("1", ideal_gas))
    if not _piston_state_known(states["2"], unit_system) and solve_for in needed:
        missing.append(_missing_piston_state_info("2", ideal_gas))
    if _solve_for_needs_piston_energy(solve_for) and (values.get("W") is None or values.get("m") is None or values.get("Q") is None):
        if u1 is None or u2 is None:
            missing.append("Piston energy balance also needs both state internal energies.")
        else:
            missing.append("Piston energy balance needs any two of m, W, and Q.")
    if solve_for in ("auto", "V1", "V2", "m") and (values.get("V1") is None or values.get("V2") is None or values.get("m") is None):
        missing.append("Total volumes need mass and state specific volumes, or a total-volume input.")
    if solve_for == "A" and values.get("A") is None:
        missing.append("Piston area needs an input; displacement is not currently an input.")
    _append_piston_entropy_missing(values, solve_for, adiabatic, missing)
    if not isentropic:
        _append_exergy_missing(values, solve_for, missing)

    if ideal_gas:
        values["x1"] = None
        values["x2"] = None
    values.pop("_unit_system", None)
    return {
        "values": values,
        "states": states,
        "errors": errors,
        "missing": missing,
        "notes": notes,
        "ideal_gas": ideal_gas,
        "isentropic": isentropic,
        "adiabatic": adiabatic,
        "unit_system": unit_system,
        "solve_for": solve_for,
    }


def _format_turbine_value(key, value, unit_system, ideal_gas, states):
    unit = ""
    label = key

    if key == "T0":
        return _format_dead_state_temperature(value, unit_system)

    if key in ("T1", "T2"):
        if value is None:
            return key + " = u"
        t = float(value)
        if _unit_system_key(unit_system) == "metric":
            if ideal_gas:
                return key + " = " + _display_number(t - 273.15) + " C = " + _display_number(t) + " K"
            return key + " = " + _display_number(t) + " C = " + _display_number(t + 273.15) + " K"
        if ideal_gas:
            return key + " = " + _display_number(t - 459.67) + " F = " + _display_number(t) + " R"
        return key + " = " + _display_number(t) + " F = " + _display_number(t + 459.67) + " R"

    if key in ("p1", "p2"):
        label = "P" + key[1:]
        if value is None:
            return label + " = u"
        p = float(value)
        if _unit_system_key(unit_system) == "metric":
            return label + " = " + _display_number(p) + " bar = " + _display_number(p * 100.0) + " kPa"
        return label + " = " + _display_number(p) + " psia = " + _display_number(p / PSIA_PER_BAR) + " bar"

    if key in ("T1", "T2"):
        unit = _turbine_temp_unit(unit_system, ideal_gas)
    elif key in ("p1", "p2"):
        label = "P" + key[1:]
        unit = _turbine_pressure_unit(unit_system)
    elif key == "mdot":
        label = "mdot"
        unit = _turbine_mdot_unit(unit_system)
    elif key in ("W", "Q"):
        unit = _turbine_power_unit(unit_system)
    elif key == "delta_s":
        label = "delta s"
        unit = _turbine_entropy_unit(unit_system)
    elif key == "Sdot":
        label = "Sdot"
        unit = _turbine_entropy_rate_unit(unit_system)
    elif key == "sigma":
        label = "sigma"
        unit = _turbine_entropy_rate_unit(unit_system)
    elif key == "ExD":
        label = "Exergy destruction"
        unit = _exergy_rate_unit(unit_system)

    if key in ("x1", "x2"):
        state_num = key[1:]
        state = states.get(state_num)
        region = "" if state is None else str(state.get("region", "")).lower()
        if ideal_gas or region in ("superheated", "compressed", "ideal_gas", "ideal_gas_partial"):
            value_text = "n/a"
        elif value is None:
            value_text = "u"
        else:
            value_text = _display_number(value)
    else:
        value_text = "u" if value is None else _display_number(value)

    if unit and value_text not in ("u", "n/a"):
        return label + " = " + value_text + " " + unit
    return label + " = " + value_text


def _ordered_known_then_unknown(keys, is_unknown):
    known = []
    unknown = []
    for key in keys:
        if is_unknown(key):
            unknown.append(key)
        else:
            known.append(key)
    return known + unknown


def _turbine_result_value_is_unknown(key, values, states, ideal_gas):
    if key in ("x1", "x2"):
        if ideal_gas:
            return False
        state_num = key[1:]
        state = states.get(state_num)
        region = "" if state is None else str(state.get("region", "")).lower()
        if region in ("superheated", "compressed", "ideal_gas", "ideal_gas_partial"):
            return False
    return values.get(key) is None


def turbine_result_lines(result, title="Turbine Solver"):
    values = result["values"]
    states = result["states"]
    ideal_gas = result["ideal_gas"]
    unit_system = result["unit_system"]

    lines = [
        title,
        "",
        "Results",
    ]
    result_keys = ["T1", "T2", "p1", "p2"]
    if not ideal_gas:
        result_keys.extend(["x1", "x2"])
    result_keys.extend(["mdot", "W", "efficiency", "Q", "delta_s", "Sdot", "sigma"])
    if result.get("isentropic"):
        result_keys.append("ExD")
    else:
        result_keys.extend(["T0", "ExD"])
    result_keys = _ordered_known_then_unknown(
        result_keys,
        lambda key: _turbine_result_value_is_unknown(key, values, states, ideal_gas)
    )
    for key in result_keys:
        lines.append(_format_turbine_value(key, values.get(key), unit_system, ideal_gas, states))

    if result["errors"]:
        lines.append("")
        lines.append("Check inputs")
        for message in result["errors"]:
            lines.append("- " + str(message))

    if result["missing"]:
        lines.append("")
        lines.append("Missing info")
        seen = []
        for message in result["missing"]:
            if message not in seen:
                seen.append(message)
                lines.append("- " + message)

    if result["notes"]:
        lines.append("")
        lines.append("Notes")
        for message in result["notes"]:
            lines.append("- " + message)

    return lines


def _format_piston_value(key, value, unit_system, ideal_gas, states):
    if key in ("T1", "T2", "p1", "p2", "x1", "x2"):
        return _format_turbine_value(key, value, unit_system, ideal_gas, states)
    if key == "T0":
        return _format_dead_state_temperature(value, unit_system)
    label = key
    unit = ""
    if key == "V1" or key == "V2":
        unit = _piston_volume_unit(unit_system)
    elif key == "A":
        unit = _piston_area_unit(unit_system)
    elif key == "m":
        unit = _piston_mass_unit(unit_system)
    elif key in ("W", "Q"):
        unit = _piston_energy_unit(unit_system)
    elif key == "efficiency":
        return "efficiency = n/a"
    elif key == "delta_s":
        label = "delta s"
        unit = _turbine_entropy_unit(unit_system)
    elif key in ("Sdot", "sigma"):
        unit = _piston_entropy_total_unit(unit_system)
    elif key == "ExD":
        label = "Exergy destruction"
        unit = _exergy_total_unit(unit_system)

    value_text = "u" if value is None else _display_number(value)
    if unit and value_text != "u":
        return label + " = " + value_text + " " + unit
    return label + " = " + value_text


def _piston_result_value_is_unknown(key, values, states, ideal_gas):
    if key == "efficiency":
        return False
    return _turbine_result_value_is_unknown(key, values, states, ideal_gas) if key in ("T1", "T2", "p1", "p2", "x1", "x2") else values.get(key) is None


def piston_result_lines(result):
    values = result["values"]
    states = result["states"]
    ideal_gas = result["ideal_gas"]
    unit_system = result["unit_system"]
    lines = [
        "Piston Solver",
        "",
        "Results",
    ]
    result_keys = ["T1", "p1"]
    if not ideal_gas:
        result_keys.append("x1")
    result_keys.append("V1")
    result_keys.extend(["T2", "p2"])
    if not ideal_gas:
        result_keys.append("x2")
    result_keys.extend(["V2", "A", "m", "W", "efficiency", "Q", "delta_s", "Sdot", "sigma"])
    if result.get("isentropic"):
        result_keys.append("ExD")
    else:
        result_keys.extend(["T0", "ExD"])
    result_keys = _ordered_known_then_unknown(
        result_keys,
        lambda key: _piston_result_value_is_unknown(key, values, states, ideal_gas)
    )
    for key in result_keys:
        lines.append(_format_piston_value(key, values.get(key), unit_system, ideal_gas, states))

    if result["errors"]:
        lines.append("")
        lines.append("Check inputs")
        for message in result["errors"]:
            lines.append("- " + str(message))

    if result["missing"]:
        lines.append("")
        lines.append("Missing info")
        seen = []
        for message in result["missing"]:
            if message not in seen:
                seen.append(message)
                lines.append("- " + message)

    if result["notes"]:
        lines.append("")
        lines.append("Notes")
        for message in result["notes"]:
            lines.append("- " + message)

    return lines


def _nozzle_velocity_unit(unit_system):
    return "m/s" if _unit_system_key(unit_system) == "metric" else "ft/s"


def _nozzle_ke_from_velocity(velocity, unit_system):
    v = _safe_float(velocity)
    if v is None:
        return None
    if _unit_system_key(unit_system) == "metric":
        return v * v / 2000.0
    return v * v / (2.0 * 32.174 * 778.169262)


def _nozzle_velocity_from_ke(ke, unit_system):
    ke = _safe_float(ke)
    if ke is None or ke < 0.0:
        return None
    if _unit_system_key(unit_system) == "metric":
        return (ke * 2000.0) ** 0.5
    return (ke * 2.0 * 32.174 * 778.169262) ** 0.5


def _nozzle_solve_for_options(ideal_gas, isentropic):
    options = [
        ("auto", "All possible"),
        ("T1", "T1"),
        ("p1", "P1"),
    ]
    if not ideal_gas:
        options.append(("x1", "x1"))
    options.append(("V1", "V1"))
    options.extend([
        ("T2", "T2"),
        ("p2", "P2"),
    ])
    if not ideal_gas:
        options.append(("x2", "x2"))
    options.extend([
        ("V2", "V2"),
        ("mdot", "mdot"),
    ])
    if not isentropic:
        options.extend([
            ("delta_s", "delta s"),
            ("Sdot", "Sdot"),
            ("sigma", "sigma"),
            ("ExD", "Exergy destruction"),
        ])
    return options


def _prompt_nozzle_solve_for(ideal_gas, isentropic):
    options = _nozzle_solve_for_options(ideal_gas, isentropic)
    lines = ["Solve For", ""]
    valid = []
    for i, (_, label) in enumerate(options, start=1):
        opt = str(i)
        valid.append(opt)
        lines.append(opt + ". " + label)
    choice = paged_choice(lines, valid)
    if choice == GO_BACK:
        return GO_BACK
    return options[int(choice) - 1][0]


def _solve_for_needs_nozzle_energy(solve_for):
    return solve_for in (None, "auto", "T1", "p1", "x1", "V1", "T2", "p2", "x2", "V2")


def _solve_nozzle_energy_balance(values, states, h_targets, unit_system, errors):
    changed = False
    h1 = _state_h(states.get("1"), unit_system)
    h2 = _state_h(states.get("2"), unit_system)
    v1 = _safe_float(values.get("V1"))
    v2 = _safe_float(values.get("V2"))
    ke1 = _nozzle_ke_from_velocity(v1, unit_system)
    ke2 = _nozzle_ke_from_velocity(v2, unit_system)

    if h1 is not None and h2 is not None and ke1 is not None and ke2 is not None:
        if not _close_enough(h1 + ke1, h2 + ke2, tol=1e-4):
            _append_turbine_error(errors, "Nozzle energy balance requires h1 + V1^2/2 = h2 + V2^2/2.")
        return False

    if h1 is not None and h2 is not None and ke1 is not None and values.get("V2") is None:
        needed_ke2 = h1 + ke1 - h2
        if needed_ke2 < -1e-9:
            _append_turbine_error(errors, "Nozzle energy balance gives a negative V2^2.")
        else:
            values["V2"] = _nozzle_velocity_from_ke(max(0.0, needed_ke2), unit_system)
            changed = True
    elif h1 is not None and h2 is not None and ke2 is not None and values.get("V1") is None:
        needed_ke1 = h2 + ke2 - h1
        if needed_ke1 < -1e-9:
            _append_turbine_error(errors, "Nozzle energy balance gives a negative V1^2.")
        else:
            values["V1"] = _nozzle_velocity_from_ke(max(0.0, needed_ke1), unit_system)
            changed = True
    elif h1 is not None and ke1 is not None and ke2 is not None and h2 is None:
        if h_targets.get("2") is None:
            h_targets["2"] = h1 + ke1 - ke2
            changed = True
    elif h2 is not None and ke1 is not None and ke2 is not None and h1 is None:
        if h_targets.get("1") is None:
            h_targets["1"] = h2 + ke2 - ke1
            changed = True

    return changed


def _missing_nozzle_state_info(state_num, ideal_gas):
    if ideal_gas:
        return (
            "State " + state_num +
            " needs enough data for h" + state_num +
            ": enter T" + state_num +
            ", or make it solvable from p" + state_num +
            " plus delta s or the nozzle energy balance."
        )
    return (
        "State " + state_num +
        " needs enough data for h" + state_num +
        ": use T" + state_num + "+p" + state_num +
        ", T" + state_num + "+x" + state_num +
        ", p" + state_num + "+x" + state_num +
        ", or p/T plus the nozzle energy balance."
    )


def solve_nozzle(fluid, unit_system, ideal_gas, isentropic, values, solve_for="auto"):
    values = values.copy()
    notes = []
    errors = []
    missing = []
    adiabatic = True
    solve_for = "auto" if solve_for is None else str(solve_for)

    if values.get("mdot") is not None and float(values["mdot"]) < 0.0:
        errors.append("Mass flow rate must be positive.")
    for key in ("V1", "V2"):
        if values.get(key) is not None and float(values[key]) < 0.0:
            errors.append(key + " must be non-negative.")
    _check_t0_value(values, errors)

    if isentropic:
        if values.get("delta_s") is not None and not _close_enough(values.get("delta_s"), 0.0):
            errors.append("Isentropic nozzle states require delta s = 0.")
        values["delta_s"] = 0.0
        if values.get("Sdot") is not None and not _close_enough(values.get("Sdot"), 0.0):
            errors.append("Isentropic nozzle states require Sdot = 0.")
        values["Sdot"] = 0.0
        if values.get("sigma") is not None and not _close_enough(values.get("sigma"), 0.0):
            errors.append("Isentropic nozzle states require sigma = 0.")
        values["sigma"] = 0.0
        values["ExD"] = 0.0

    if ideal_gas:
        values["x1"] = None
        values["x2"] = None
    else:
        values.setdefault("x1", None)
        values.setdefault("x2", None)
    for key in ("V1", "V2", "mdot", "delta_s", "Sdot", "sigma"):
        values.setdefault(key, None)
    values.setdefault("T0", None)
    values.setdefault("ExD", None)

    h_targets = {"1": None, "2": None}
    s_targets = {"1": None, "2": None}
    states = {"1": None, "2": None}

    for _ in range(8):
        changed = False
        states, state_errors = _resolve_turbine_states(
            fluid, unit_system, ideal_gas, values, h_targets, s_targets
        )
        for err in state_errors:
            _append_turbine_error(errors, err["error"])

        s1 = _state_s(states["1"], unit_system)
        s2 = _state_s(states["2"], unit_system)
        if values.get("delta_s") is None and s1 is not None and s2 is not None:
            values["delta_s"] = s2 - s1
            changed = True
        if values.get("delta_s") is not None:
            ds = float(values["delta_s"])
            if s1 is not None and s_targets["2"] is None:
                s_targets["2"] = s1 + ds
                changed = True
            if s2 is not None and s_targets["1"] is None:
                s_targets["1"] = s2 - ds
                changed = True

        if _solve_entropy_rate_values(values, adiabatic, isentropic):
            changed = True
        if _solve_exergy_destruction(values):
            changed = True
        if _solve_nozzle_energy_balance(values, states, h_targets, unit_system, errors):
            changed = True
        if not changed:
            break

    states, state_errors = _resolve_turbine_states(
        fluid, unit_system, ideal_gas, values, h_targets, s_targets
    )
    for err in state_errors:
        _append_turbine_error(errors, err["error"])
    _solve_nozzle_energy_balance(values, states, h_targets, unit_system, errors)

    h1 = _state_h(states["1"], unit_system)
    h2 = _state_h(states["2"], unit_system)
    s1 = _state_s(states["1"], unit_system)
    s2 = _state_s(states["2"], unit_system)
    if values.get("delta_s") is None and s1 is not None and s2 is not None:
        values["delta_s"] = s2 - s1
    _solve_entropy_rate_values(values, adiabatic, isentropic)
    _solve_exergy_destruction(values)
    _check_entropy_rate_values(values, adiabatic, errors)

    if s1 is not None and values.get("delta_s") is not None and s2 is not None:
        expected_s2 = s1 + float(values["delta_s"])
        if not _close_enough(s2, expected_s2):
            errors.append("State entropies do not match the supplied delta s.")
    if h_targets["1"] is not None and h1 is not None and not _close_enough(h1, h_targets["1"]):
        errors.append("State 1 does not match the enthalpy required by the nozzle balance.")
    if h_targets["2"] is not None and h2 is not None and not _close_enough(h2, h_targets["2"]):
        errors.append("State 2 does not match the enthalpy required by the nozzle balance.")
    if h_targets["1"] is not None and values.get("T1") is not None and h1 is None:
        errors.append("No state 1 matches the solved h1 at the given T1.")
    if h_targets["2"] is not None and values.get("T2") is not None and h2 is None:
        errors.append("No state 2 matches the solved h2 at the given T2.")

    needed = ("auto", "T1", "p1", "x1", "V1", "T2", "p2", "x2", "V2", "delta_s", "Sdot", "sigma")
    if not _turbine_state_known(states["1"], unit_system) and solve_for in needed:
        missing.append(_missing_nozzle_state_info("1", ideal_gas))
    if not _turbine_state_known(states["2"], unit_system) and solve_for in needed:
        missing.append(_missing_nozzle_state_info("2", ideal_gas))

    if _solve_for_needs_nozzle_energy(solve_for):
        ke1 = _nozzle_ke_from_velocity(values.get("V1"), unit_system)
        ke2 = _nozzle_ke_from_velocity(values.get("V2"), unit_system)
        if h1 is None or h2 is None or ke1 is None or ke2 is None:
            missing.append("Nozzle energy balance needs h1, h2, V1, and V2 with one unknown.")

    if solve_for == "mdot" and values.get("mdot") is None:
        missing.append("mdot needs Sdot and delta s, or an input value.")
    if solve_for == "delta_s" and values.get("delta_s") is None:
        missing.append("delta s needs both state entropies, or an input value.")
    _append_entropy_rate_missing(values, solve_for, adiabatic, missing)
    if not isentropic:
        _append_exergy_missing(values, solve_for, missing)

    if ideal_gas:
        values["x1"] = None
        values["x2"] = None

    return {
        "values": values,
        "states": states,
        "errors": errors,
        "missing": missing,
        "notes": notes,
        "ideal_gas": ideal_gas,
        "isentropic": isentropic,
        "adiabatic": adiabatic,
        "unit_system": unit_system,
        "solve_for": solve_for,
    }


def _format_nozzle_value(key, value, unit_system, ideal_gas, states):
    if key in ("T1", "T2", "p1", "p2", "x1", "x2", "mdot", "delta_s", "Sdot", "sigma"):
        return _format_turbine_value(key, value, unit_system, ideal_gas, states)
    if key in ("T0", "ExD"):
        return _format_turbine_value(key, value, unit_system, ideal_gas, states)
    if key in ("V1", "V2"):
        value_text = "u" if value is None else _display_number(value)
        if value_text == "u":
            return key + " = u"
        return key + " = " + value_text + " " + _nozzle_velocity_unit(unit_system)
    return key + " = " + ("u" if value is None else _display_number(value))


def _nozzle_result_value_is_unknown(key, values, states, ideal_gas):
    if key in ("T1", "T2", "p1", "p2", "x1", "x2"):
        return _turbine_result_value_is_unknown(key, values, states, ideal_gas)
    return values.get(key) is None


def nozzle_result_lines(result):
    values = result["values"]
    states = result["states"]
    ideal_gas = result["ideal_gas"]
    unit_system = result["unit_system"]
    lines = [
        "Nozzle Solver",
        "",
        "Results",
    ]
    result_keys = ["T1", "p1"]
    if not ideal_gas:
        result_keys.append("x1")
    result_keys.append("V1")
    result_keys.extend(["T2", "p2"])
    if not ideal_gas:
        result_keys.append("x2")
    result_keys.extend(["V2", "mdot", "delta_s", "Sdot", "sigma"])
    if result.get("isentropic"):
        result_keys.append("ExD")
    else:
        result_keys.extend(["T0", "ExD"])
    result_keys = _ordered_known_then_unknown(
        result_keys,
        lambda key: _nozzle_result_value_is_unknown(key, values, states, ideal_gas)
    )
    for key in result_keys:
        lines.append(_format_nozzle_value(key, values.get(key), unit_system, ideal_gas, states))

    if result["errors"]:
        lines.append("")
        lines.append("Check inputs")
        for message in result["errors"]:
            lines.append("- " + str(message))

    if result["missing"]:
        lines.append("")
        lines.append("Missing info")
        seen = []
        for message in result["missing"]:
            if message not in seen:
                seen.append(message)
                lines.append("- " + message)

    if result["notes"]:
        lines.append("")
        lines.append("Notes")
        for message in result["notes"]:
            lines.append("- " + message)

    return lines


def _history_record_nozzle(fluid, unit_system, ideal_gas, isentropic, input_values, result):
    if result is None:
        return
    values = result.get("values", {})
    states = result.get("states", {})
    process = "Isentropic" if isentropic else "Adiabatic"
    model = "Ideal Gas" if ideal_gas else "Non Ideal Gas"
    lines = [
        "Nozzle Solver",
        process + ", " + _history_fluid_name(fluid) + ", " + _history_unit_name(unit_system) + ", " + model,
        "",
        "Given:",
    ]

    result_keys = ["T1", "p1"]
    if not ideal_gas:
        result_keys.append("x1")
    result_keys.append("V1")
    result_keys.extend(["T2", "p2"])
    if not ideal_gas:
        result_keys.append("x2")
    result_keys.extend(["V2", "mdot", "delta_s", "Sdot", "sigma"])
    if result.get("isentropic"):
        result_keys.append("ExD")
    else:
        result_keys.extend(["T0", "ExD"])

    any_given = False
    for key in result_keys:
        if key in input_values and input_values.get(key) is not None:
            lines.append(_format_nozzle_value(key, input_values.get(key), unit_system, ideal_gas, states))
            any_given = True
    if not any_given:
        lines.append("None")

    lines.extend(["", "Found:"])
    any_found = False
    for key in result_keys:
        if key not in input_values or input_values.get(key) is None:
            value = values.get(key)
            if value is not None:
                lines.append(_format_nozzle_value(key, value, unit_system, ideal_gas, states))
                any_found = True
    if not any_found:
        lines.append("No additional values solved.")

    if result.get("errors"):
        lines.extend(["", "Check inputs:"])
        for message in result["errors"]:
            lines.append("- " + str(message))
    if result.get("missing"):
        lines.extend(["", "Missing info:"])
        for message in result["missing"]:
            lines.append("- " + str(message))
    _history_add(lines)


def _expansion_valve_state_info(state_num):
    return (
        "State " + state_num +
        " needs enough data for h" + state_num +
        ": use T" + state_num + "+p" + state_num +
        ", T" + state_num + "+x" + state_num +
        ", p" + state_num + "+x" + state_num +
        ", or provide T/P so h1 = h2 can locate the state."
    )


def solve_expansion_valve(fluid, unit_system, values):
    values = values.copy()
    errors = []
    missing = []
    notes = [
        "Expansion valve assumes throttling: h1 = h2.",
        "Exergy destruction is per unit mass because mdot is not an input.",
    ]
    ideal_gas = False

    for key in ("T1", "p1", "x1", "T2", "p2", "x2", "T0", "delta_s", "sigma", "ExD"):
        values.setdefault(key, None)
    _check_t0_value(values, errors)

    h_targets = {"1": None, "2": None}
    s_targets = {"1": None, "2": None}
    states = {"1": None, "2": None}

    for _ in range(8):
        changed = False
        states, state_errors = _resolve_turbine_states(
            fluid, unit_system, ideal_gas, values, h_targets, s_targets
        )
        for err in state_errors:
            _append_turbine_error(errors, err["error"])

        h1 = _state_h(states["1"], unit_system)
        h2 = _state_h(states["2"], unit_system)
        if h1 is not None and h_targets["2"] is None:
            h_targets["2"] = h1
            changed = True
        if h2 is not None and h_targets["1"] is None:
            h_targets["1"] = h2
            changed = True
        if not changed:
            break

    states, state_errors = _resolve_turbine_states(
        fluid, unit_system, ideal_gas, values, h_targets, s_targets
    )
    for err in state_errors:
        _append_turbine_error(errors, err["error"])
    _solve_specific_exergy_destruction(values, states, unit_system)

    h1 = _state_h(states["1"], unit_system)
    h2 = _state_h(states["2"], unit_system)
    if h1 is not None and h2 is not None and not _close_enough(h1, h2, tol=1e-4):
        errors.append("Expansion valve throttling requires h1 = h2.")
    if h_targets["1"] is not None and h1 is not None and not _close_enough(h1, h_targets["1"], tol=1e-4):
        errors.append("State 1 does not match the enthalpy required by h1 = h2.")
    if h_targets["2"] is not None and h2 is not None and not _close_enough(h2, h_targets["2"], tol=1e-4):
        errors.append("State 2 does not match the enthalpy required by h1 = h2.")
    if h_targets["1"] is not None and values.get("T1") is not None and h1 is None:
        errors.append("No state 1 matches the solved h1 at the given T1.")
    if h_targets["2"] is not None and values.get("T2") is not None and h2 is None:
        errors.append("No state 2 matches the solved h2 at the given T2.")

    if h1 is None and h2 is None:
        missing.append("Expansion valve needs enough data to determine at least one state enthalpy.")
    if h1 is None:
        missing.append(_expansion_valve_state_info("1"))
    if h2 is None:
        missing.append(_expansion_valve_state_info("2"))
    if values.get("ExD") is None:
        missing.append("Exergy destruction needs T0 and both state entropies.")

    return {
        "values": values,
        "states": states,
        "errors": errors,
        "missing": missing,
        "notes": notes,
        "ideal_gas": ideal_gas,
        "isentropic": False,
        "adiabatic": True,
        "unit_system": unit_system,
    }


def _state_result_lines(title, row):
    lines = [title]
    if row is None:
        lines.append("unavailable")
        return lines
    lines.extend(result_dict_display_lines(row))
    return lines


def expansion_valve_result_lines(result):
    values = result["values"]
    unit_system = result["unit_system"]
    lines = [
        "Expansion Valve Solver",
        "",
        "Results",
    ]
    states = result["states"]
    lines.extend(_state_result_lines("State 1", states.get("1")))
    lines.append("")
    lines.extend(_state_result_lines("State 2", states.get("2")))
    lines.append("")
    extra_keys = ["T0", "delta_s", "ExD"]
    extra_keys = _ordered_known_then_unknown(extra_keys, lambda key: values.get(key) is None)
    for key in extra_keys:
        lines.append(_format_initially_evacuated_value(key, values.get(key), unit_system, False, states))

    if result["errors"]:
        lines.append("")
        lines.append("Check inputs")
        for message in result["errors"]:
            lines.append("- " + str(message))

    if result["missing"]:
        lines.append("")
        lines.append("Missing info")
        seen = []
        for message in result["missing"]:
            if message not in seen:
                seen.append(message)
                lines.append("- " + message)

    if result["notes"]:
        lines.append("")
        lines.append("Notes")
        for message in result["notes"]:
            lines.append("- " + message)

    return lines


def _history_record_expansion_valve(fluid, unit_system, input_values, result):
    if result is None:
        return
    states = result.get("states", {})
    lines = [
        "Expansion Valve Solver",
        "Adiabatic throttling, " + _history_fluid_name(fluid) + ", " + _history_unit_name(unit_system) + ", Non Ideal Gas",
        "",
        "Given:",
    ]

    result_keys = ["T1", "p1", "x1", "T2", "p2", "x2", "T0"]
    any_given = False
    for key in result_keys:
        if key in input_values and input_values.get(key) is not None:
            lines.append(_format_turbine_value(key, input_values.get(key), unit_system, False, states))
            any_given = True
    if not any_given:
        lines.append("None")

    lines.extend(["", "Found:", "State 1:"])
    row1 = states.get("1")
    if row1 is None:
        lines.append("unavailable")
    else:
        lines.extend(result_dict_display_lines(row1))
    lines.extend(["", "State 2:"])
    row2 = states.get("2")
    if row2 is None:
        lines.append("unavailable")
    else:
        lines.extend(result_dict_display_lines(row2))
    lines.extend(["", "Exergy:"])
    for key in ("delta_s", "ExD"):
        if result.get("values", {}).get(key) is not None:
            lines.append(_format_initially_evacuated_value(key, result["values"][key], unit_system, False, states))

    if result.get("errors"):
        lines.extend(["", "Check inputs:"])
        for message in result["errors"]:
            lines.append("- " + str(message))
    if result.get("missing"):
        lines.extend(["", "Missing info:"])
        for message in result["missing"]:
            lines.append("- " + str(message))
    _history_add(lines)


def _specific_energy_unit(unit_system):
    return "kJ/kg" if _unit_system_key(unit_system) == "metric" else "Btu/lbm"


def safe_input_positive_int(prompt):
    while True:
        raw = input(prompt).strip()
        nav = _handle_global_nav(raw)
        if nav == GO_BACK:
            return GO_BACK
        if nav == QUIT_CANCELLED:
            continue

        try:
            value = int(raw)
        except:
            print("Enter a positive whole number.")
            continue

        if value <= 0:
            print("Enter a positive whole number.")
            continue
        return value


def _format_labeled_temperature(label, value, unit_system, ideal_gas):
    if value is None:
        return label + " = u"
    t = float(value)
    if _unit_system_key(unit_system) == "metric":
        if ideal_gas:
            return label + " = " + _display_number(t - 273.15) + " C = " + _display_number(t) + " K"
        return label + " = " + _display_number(t) + " C = " + _display_number(t + 273.15) + " K"
    if ideal_gas:
        return label + " = " + _display_number(t - 459.67) + " F = " + _display_number(t) + " R"
    return label + " = " + _display_number(t) + " F = " + _display_number(t + 459.67) + " R"


def _format_labeled_pressure(label, value, unit_system):
    if value is None:
        return label + " = u"
    p = float(value)
    if _unit_system_key(unit_system) == "metric":
        return label + " = " + _display_number(p) + " bar = " + _display_number(p * 100.0) + " kPa"
    return label + " = " + _display_number(p) + " psia = " + _display_number(p / PSIA_PER_BAR) + " bar"


def _format_specific_energy(label, value, unit_system):
    value_text = "u" if value is None else _display_number(value)
    if value_text == "u":
        return label + " = u"
    return label + " = " + value_text + " " + _specific_energy_unit(unit_system)


def _format_specific_exergy(label, value, unit_system):
    value_text = "u" if value is None else _display_number(value)
    if value_text == "u":
        return label + " = u"
    return label + " = " + value_text + " " + _exergy_specific_unit(unit_system)


def _specific_entropy_generation(states, unit_system):
    s1 = _state_s(states.get("1"), unit_system)
    s2 = _state_s(states.get("2"), unit_system)
    if s1 is None or s2 is None:
        return None
    return s2 - s1


def _solve_specific_exergy_destruction(values, states, unit_system):
    changed = False
    sigma = _specific_entropy_generation(states, unit_system)
    if values.get("delta_s") is None and sigma is not None:
        values["delta_s"] = sigma
        changed = True
    if values.get("sigma") is None and sigma is not None:
        values["sigma"] = sigma
        changed = True
    if values.get("ExD") is None:
        t0 = _safe_float(values.get("T0"))
        sigma_value = _safe_float(values.get("sigma"))
        if t0 is not None and sigma_value is not None:
            values["ExD"] = t0 * sigma_value
            changed = True
    return changed


def _format_initially_evacuated_value(key, value, unit_system, ideal_gas, states):
    if key in ("T1", "T2", "p1", "p2", "x1", "x2"):
        return _format_turbine_value(key, value, unit_system, ideal_gas, states)
    if key == "T0":
        return _format_dead_state_temperature(value, unit_system)
    if key == "h1":
        return _format_specific_energy("h1", value, unit_system)
    if key == "u2":
        return _format_specific_energy("u2", value, unit_system)
    if key == "delta_s":
        return _format_specific_exergy("delta s", value, unit_system).replace(_exergy_specific_unit(unit_system), _turbine_entropy_unit(unit_system))
    if key == "ExD":
        return _format_specific_exergy("Exergy destruction", value, unit_system)
    return key + " = " + ("u" if value is None else _display_number(value))


def _resolve_initially_evacuated_states(fluid, unit_system, ideal_gas, values, h_targets, u_targets):
    states = {"1": None, "2": None}
    errors = []

    row1 = _resolve_turbine_state(
        fluid, unit_system, ideal_gas,
        temp=values.get("T1"),
        pressure=values.get("p1"),
        quality=values.get("x1"),
        h=h_targets.get("1"),
    )
    if _is_error(row1):
        errors.append(row1)
        row1 = None
    states["1"] = row1
    _update_turbine_values_from_state(values, "1", row1, unit_system, ideal_gas)

    row2 = _resolve_piston_state(
        fluid, unit_system, ideal_gas,
        temp=values.get("T2"),
        pressure=values.get("p2"),
        quality=values.get("x2"),
        u=u_targets.get("2"),
    )
    if _is_error(row2):
        errors.append(row2)
        row2 = None
    states["2"] = row2
    _update_turbine_values_from_state(values, "2", row2, unit_system, ideal_gas)

    return states, errors


def solve_initially_evacuated(fluid, unit_system, ideal_gas, values):
    values = values.copy()
    errors = []
    missing = []
    notes = [
        "Initially evacuated tank fill assumes adiabatic filling: h1 = u2.",
        "Exergy destruction is per unit mass of final tank contents.",
    ]

    if ideal_gas:
        values["x1"] = None
        values["x2"] = None
    else:
        values.setdefault("x1", None)
        values.setdefault("x2", None)
    for key in ("T1", "p1", "T2", "p2", "T0", "delta_s", "sigma", "ExD"):
        values.setdefault(key, None)
    _check_t0_value(values, errors)

    h_targets = {"1": None}
    u_targets = {"2": None}
    states = {"1": None, "2": None}

    for _ in range(8):
        changed = False
        states, state_errors = _resolve_initially_evacuated_states(
            fluid, unit_system, ideal_gas, values, h_targets, u_targets
        )
        for err in state_errors:
            _append_turbine_error(errors, err["error"])

        h1 = _state_h(states["1"], unit_system)
        u2 = _state_u(states["2"], unit_system)
        if h1 is not None and u_targets["2"] is None:
            u_targets["2"] = h1
            changed = True
        if u2 is not None and h_targets["1"] is None:
            h_targets["1"] = u2
            changed = True
        if not changed:
            break

    states, state_errors = _resolve_initially_evacuated_states(
        fluid, unit_system, ideal_gas, values, h_targets, u_targets
    )
    for err in state_errors:
        _append_turbine_error(errors, err["error"])
    _solve_specific_exergy_destruction(values, states, unit_system)

    h1 = _state_h(states["1"], unit_system)
    u2 = _state_u(states["2"], unit_system)
    if h1 is not None and u2 is not None and not _close_enough(h1, u2, tol=1e-4):
        errors.append("Initially evacuated tank relation requires h1 = u2.")
    if h_targets["1"] is not None and h1 is not None and not _close_enough(h1, h_targets["1"], tol=1e-4):
        errors.append("State 1 does not match the enthalpy required by h1 = u2.")
    if u_targets["2"] is not None and u2 is not None and not _close_enough(u2, u_targets["2"], tol=1e-4):
        errors.append("State 2 does not match the internal energy required by h1 = u2.")
    if h_targets["1"] is not None and values.get("T1") is not None and h1 is None:
        errors.append("No state 1 matches the solved h1 at the given T1.")
    if u_targets["2"] is not None and values.get("T2") is not None and u2 is None:
        errors.append("No state 2 matches the solved u2 at the given T2.")

    if h1 is None and u2 is None:
        missing.append("Initially evacuated relation needs h1 or u2 from at least one known state.")
    if h1 is None:
        missing.append(_missing_state_info("1", ideal_gas))
    if u2 is None:
        missing.append(_missing_piston_state_info("2", ideal_gas))
    if values.get("ExD") is None:
        missing.append("Exergy destruction needs T0 and both state entropies.")

    if ideal_gas:
        values["x1"] = None
        values["x2"] = None

    return {
        "values": values,
        "states": states,
        "errors": errors,
        "missing": missing,
        "notes": notes,
        "ideal_gas": ideal_gas,
        "unit_system": unit_system,
    }


def initially_evacuated_result_lines(result):
    values = result["values"]
    states = result["states"]
    ideal_gas = result["ideal_gas"]
    unit_system = result["unit_system"]
    h1 = _state_h(states.get("1"), unit_system)
    u2 = _state_u(states.get("2"), unit_system)

    lines = [
        "Initially Evacuated",
        "",
        "Results",
        "State 1 inlet",
    ]
    state1_keys = ["T1", "p1"]
    if not ideal_gas:
        state1_keys.append("x1")
    state1_keys.append("h1")
    state1_values = values.copy()
    state1_values["h1"] = h1
    state1_keys = _ordered_known_then_unknown(
        state1_keys,
        lambda key: state1_values.get(key) is None
    )
    for key in state1_keys:
        lines.append(_format_initially_evacuated_value(key, state1_values.get(key), unit_system, ideal_gas, states))

    lines.append("")
    lines.append("State 2 final tank")
    state2_keys = ["T2", "p2"]
    if not ideal_gas:
        state2_keys.append("x2")
    state2_keys.append("u2")
    state2_values = values.copy()
    state2_values["u2"] = u2
    state2_keys = _ordered_known_then_unknown(
        state2_keys,
        lambda key: state2_values.get(key) is None
    )
    for key in state2_keys:
        lines.append(_format_initially_evacuated_value(key, state2_values.get(key), unit_system, ideal_gas, states))
    lines.append("")
    lines.append("Exergy")
    exergy_keys = ["T0", "delta_s", "ExD"]
    exergy_keys = _ordered_known_then_unknown(exergy_keys, lambda key: values.get(key) is None)
    for key in exergy_keys:
        lines.append(_format_initially_evacuated_value(key, values.get(key), unit_system, ideal_gas, states))

    if result["errors"]:
        lines.append("")
        lines.append("Check inputs")
        for message in result["errors"]:
            lines.append("- " + str(message))

    if result["missing"]:
        lines.append("")
        lines.append("Missing info")
        seen = []
        for message in result["missing"]:
            if message not in seen:
                seen.append(message)
                lines.append("- " + message)

    if result["notes"]:
        lines.append("")
        lines.append("Notes")
        for message in result["notes"]:
            lines.append("- " + message)

    return lines


def _history_record_initially_evacuated(fluid, unit_system, ideal_gas, input_values, result):
    if result is None:
        return
    values = result.get("values", {})
    states = result.get("states", {})
    model = "Ideal Gas" if ideal_gas else "Non Ideal Gas"
    lines = [
        "Initially Evacuated",
        "Adiabatic fill, " + _history_fluid_name(fluid) + ", " + _history_unit_name(unit_system) + ", " + model,
        "",
        "Given:",
    ]
    result_keys = ["T1", "p1"]
    if not ideal_gas:
        result_keys.append("x1")
    result_keys.extend(["T2", "p2"])
    if not ideal_gas:
        result_keys.append("x2")
    result_keys.append("T0")

    any_given = False
    for key in result_keys:
        if key in input_values and input_values.get(key) is not None:
            lines.append(_format_turbine_value(key, input_values.get(key), unit_system, ideal_gas, states))
            any_given = True
    if not any_given:
        lines.append("None")

    lines.extend(["", "Found:"])
    found_values = values.copy()
    found_values["h1"] = _state_h(states.get("1"), unit_system)
    found_values["u2"] = _state_u(states.get("2"), unit_system)
    found_values["delta_s"] = values.get("delta_s")
    found_values["ExD"] = values.get("ExD")
    for key in ("T1", "p1", "x1", "h1", "T2", "p2", "x2", "u2", "delta_s", "ExD"):
        if ideal_gas and key in ("x1", "x2"):
            continue
        if key in input_values and input_values.get(key) is not None and key not in ("h1", "u2"):
            continue
        value = found_values.get(key)
        if value is not None:
            lines.append(_format_initially_evacuated_value(key, value, unit_system, ideal_gas, states))

    if result.get("errors"):
        lines.extend(["", "Check inputs:"])
        for message in result["errors"]:
            lines.append("- " + str(message))
    if result.get("missing"):
        lines.extend(["", "Missing info:"])
        for message in result["missing"]:
            lines.append("- " + str(message))
    _history_add(lines)


def _copy_mixing_streams(streams):
    return {
        "in": [stream.copy() for stream in streams.get("in", [])],
        "out": [stream.copy() for stream in streams.get("out", [])],
    }


def _mixing_stream_suffix(side, index):
    return str(index) + ("In" if side == "in" else "Out")


def _mixing_stream_title(side, index):
    return ("Inlet " if side == "in" else "Outlet ") + str(index)


def _update_mixing_stream_from_state(stream, row, unit_system, ideal_gas):
    if row is None or _is_error(row):
        return False

    changed = False
    temp_value = _state_value(row, _turbine_temp_key(unit_system, ideal_gas))
    if stream.get("T") is None and temp_value is not None:
        stream["T"] = temp_value
        changed = True

    pressure_value = _state_value(row, _turbine_pressure_key(unit_system))
    if stream.get("p") is None and pressure_value is not None:
        stream["p"] = pressure_value
        changed = True

    quality = _quality_from_row(row)
    if stream.get("x") is None and quality is not None:
        stream["x"] = quality
        changed = True

    return changed


def _resolve_mixing_states(fluid, unit_system, ideal_gas, streams, h_targets):
    states = {"in": [], "out": []}
    errors = []

    for side in ("in", "out"):
        for i, stream in enumerate(streams[side]):
            row = _resolve_turbine_state(
                fluid, unit_system, ideal_gas,
                temp=stream.get("T"),
                pressure=stream.get("p"),
                quality=stream.get("x"),
                h=h_targets[side][i],
            )
            if _is_error(row):
                errors.append(row)
                row = None
            states[side].append(row)
            _update_mixing_stream_from_state(stream, row, unit_system, ideal_gas)

    return states, errors


def _mixing_h(row, unit_system):
    return _state_h(row, unit_system)


def _mixing_s(row, unit_system):
    return _state_s(row, unit_system)


def _solve_mixing_mass_balance(streams, errors):
    changed = False
    sums = {"in": 0.0, "out": 0.0}
    unknowns = []

    for side in ("in", "out"):
        for i, stream in enumerate(streams[side]):
            mdot = _safe_float(stream.get("mdot"))
            if mdot is None:
                unknowns.append((side, i))
            else:
                if mdot < 0.0:
                    _append_turbine_error(errors, _mixing_stream_title(side, i + 1) + " mdot must be positive.")
                sums[side] += mdot

    if len(unknowns) == 1:
        side, i = unknowns[0]
        value = sums["out"] - sums["in"] if side == "in" else sums["in"] - sums["out"]
        if value < -1e-9:
            _append_turbine_error(errors, "Mass balance gives a negative mass flow rate.")
        else:
            streams[side][i]["mdot"] = max(0.0, value)
            changed = True
    elif len(unknowns) == 0 and not _close_enough(sums["in"], sums["out"], tol=1e-4):
        _append_turbine_error(errors, "Mixing chamber mass balance requires total mdot in = total mdot out.")

    return changed


def _solve_mixing_energy_balance(streams, states, h_targets, unit_system, errors):
    known_total = 0.0
    unknown_mdot = []
    unknown_h = []
    unresolved = []

    for side in ("in", "out"):
        sign = 1.0 if side == "in" else -1.0
        for i, stream in enumerate(streams[side]):
            mdot = _safe_float(stream.get("mdot"))
            h = _mixing_h(states[side][i], unit_system)
            if mdot is not None and h is not None:
                known_total += sign * mdot * h
            elif mdot is None and h is not None:
                unknown_mdot.append((side, i, sign, h))
            elif mdot is not None and h is None:
                unknown_h.append((side, i, sign, mdot))
            else:
                unresolved.append((side, i))

    if not unresolved and len(unknown_mdot) == 1 and not unknown_h:
        side, i, sign, h = unknown_mdot[0]
        coeff = sign * h
        if abs(coeff) > 1e-12:
            value = -known_total / coeff
            if value < -1e-9:
                _append_turbine_error(errors, "Energy balance gives a negative mass flow rate.")
            else:
                streams[side][i]["mdot"] = max(0.0, value)
                return True

    if not unresolved and len(unknown_h) == 1 and not unknown_mdot:
        side, i, sign, mdot = unknown_h[0]
        coeff = sign * mdot
        if abs(coeff) > 1e-12 and h_targets[side][i] is None:
            h_targets[side][i] = -known_total / coeff
            return True

    if not unresolved and not unknown_mdot and not unknown_h:
        if not _close_enough(known_total, 0.0, tol=1e-4):
            _append_turbine_error(errors, "Mixing chamber energy balance requires sum(mdot*h) in = sum(mdot*h) out.")

    return False


def _solve_mixing_entropy_values(streams, states, unit_system, values, errors):
    total = 0.0
    for side in ("in", "out"):
        sign = -1.0 if side == "in" else 1.0
        for i, stream in enumerate(streams[side]):
            mdot = _safe_float(stream.get("mdot"))
            s = _mixing_s(states[side][i], unit_system)
            if mdot is None or s is None:
                return False
            total += sign * mdot * s

    changed = False
    if values.get("Sdot") is None:
        values["Sdot"] = total
        changed = True
    if values.get("sigma") is None:
        values["sigma"] = total
        changed = True
    if values.get("sigma") is not None and float(values["sigma"]) < -1e-8:
        _append_turbine_error(errors, "Adiabatic mixing chamber sigma should not be negative.")
    return changed


def _mixing_state_missing_line(side, index, ideal_gas):
    label = _mixing_stream_title(side, index)
    if ideal_gas:
        return label + " needs enough data for h: enter T, or use p plus the energy balance."
    return label + " needs enough data for h: use T+P, T+x, P+x, or P/T plus the energy balance."


def _mixing_has_unresolved_energy(streams, states, unit_system):
    unknown_count = 0
    for side in ("in", "out"):
        for i, stream in enumerate(streams[side]):
            mdot = _safe_float(stream.get("mdot"))
            h = _mixing_h(states[side][i], unit_system)
            if mdot is None or h is None:
                unknown_count += 1
    return unknown_count > 0


def solve_mixing_chamber(fluid, unit_system, ideal_gas, streams, values=None):
    streams = _copy_mixing_streams(streams)
    errors = []
    missing = []
    values = {} if values is None else values.copy()
    for key in ("T0", "Sdot", "sigma", "ExD"):
        values.setdefault(key, None)
    notes = [
        "Mixing chamber assumes steady, adiabatic flow with no shaft work.",
        "Mass balance: total mdot in = total mdot out.",
        "Energy balance: sum(mdot*h) in = sum(mdot*h) out.",
    ]
    _check_t0_value(values, errors)

    if ideal_gas:
        for side in ("in", "out"):
            for stream in streams[side]:
                stream["x"] = None

    h_targets = {
        "in": [None for _ in streams["in"]],
        "out": [None for _ in streams["out"]],
    }
    states = {"in": [], "out": []}

    for _ in range(10):
        changed = False
        states, state_errors = _resolve_mixing_states(
            fluid, unit_system, ideal_gas, streams, h_targets
        )
        for err in state_errors:
            _append_turbine_error(errors, err["error"])

        if _solve_mixing_mass_balance(streams, errors):
            changed = True
        if _solve_mixing_energy_balance(streams, states, h_targets, unit_system, errors):
            changed = True
        if _solve_mixing_entropy_values(streams, states, unit_system, values, errors):
            changed = True
        if _solve_exergy_destruction(values):
            changed = True

        if not changed:
            break

    states, state_errors = _resolve_mixing_states(
        fluid, unit_system, ideal_gas, streams, h_targets
    )
    for err in state_errors:
        _append_turbine_error(errors, err["error"])
    _solve_mixing_mass_balance(streams, errors)
    _solve_mixing_energy_balance(streams, states, h_targets, unit_system, errors)
    _solve_mixing_entropy_values(streams, states, unit_system, values, errors)
    _solve_exergy_destruction(values)

    mdot_unknowns = 0
    for side in ("in", "out"):
        for i, stream in enumerate(streams[side]):
            h = _mixing_h(states[side][i], unit_system)
            if h is None:
                missing.append(_mixing_state_missing_line(side, i + 1, ideal_gas))
            if _safe_float(stream.get("mdot")) is None:
                mdot_unknowns += 1
    if mdot_unknowns:
        missing.append("Mass balance can solve one unknown mdot; provide the remaining mass flow rates.")
    if _mixing_has_unresolved_energy(streams, states, unit_system):
        missing.append("Energy balance needs all stream enthalpies and mass flow rates with at most one unknown.")
    if values.get("ExD") is None:
        missing.append("Exergy destruction needs T0 and sigma.")

    return {
        "streams": streams,
        "states": states,
        "values": values,
        "errors": errors,
        "missing": missing,
        "notes": notes,
        "ideal_gas": ideal_gas,
        "unit_system": unit_system,
    }


def _mixing_stream_value_is_unknown(field, stream, row, unit_system, ideal_gas):
    if field == "x":
        if ideal_gas:
            return False
        region = "" if row is None else str(row.get("region", "")).lower()
        if region in ("superheated", "compressed", "ideal_gas", "ideal_gas_partial"):
            return False
        return stream.get("x") is None
    if field == "h":
        return _mixing_h(row, unit_system) is None
    return stream.get(field) is None


def _format_mixing_stream_value(field, stream, row, unit_system, ideal_gas):
    suffix = _mixing_stream_suffix(stream["side"], stream["index"])
    if field == "T":
        return _format_labeled_temperature("T" + suffix, stream.get("T"), unit_system, ideal_gas)
    if field == "p":
        return _format_labeled_pressure("P" + suffix, stream.get("p"), unit_system)
    if field == "x":
        region = "" if row is None else str(row.get("region", "")).lower()
        if ideal_gas or region in ("superheated", "compressed", "ideal_gas", "ideal_gas_partial"):
            value_text = "n/a"
        elif stream.get("x") is None:
            value_text = "u"
        else:
            value_text = _display_number(stream.get("x"))
        return "x" + suffix + " = " + value_text
    if field == "mdot":
        value = stream.get("mdot")
        value_text = "u" if value is None else _display_number(value)
        if value_text == "u":
            return "mdot" + suffix + " = u"
        return "mdot" + suffix + " = " + value_text + " " + _turbine_mdot_unit(unit_system)
    if field == "h":
        return _format_specific_energy("h" + suffix, _mixing_h(row, unit_system), unit_system)
    return field + suffix + " = " + ("u" if stream.get(field) is None else _display_number(stream.get(field)))


def _mixing_stream_result_lines(stream, row, unit_system, ideal_gas):
    fields = ["T", "p"]
    if not ideal_gas:
        fields.append("x")
    fields.extend(["mdot", "h"])
    fields = _ordered_known_then_unknown(
        fields,
        lambda field: _mixing_stream_value_is_unknown(field, stream, row, unit_system, ideal_gas)
    )
    lines = [_mixing_stream_title(stream["side"], stream["index"])]
    for field in fields:
        lines.append(_format_mixing_stream_value(field, stream, row, unit_system, ideal_gas))
    return lines


def mixing_chamber_result_lines(result):
    streams = result["streams"]
    states = result["states"]
    ideal_gas = result["ideal_gas"]
    unit_system = result["unit_system"]
    values = result["values"]
    lines = [
        "Mixing Chamber Solver",
        "",
        "Results",
        "Inputs",
    ]
    for i, stream in enumerate(streams["in"]):
        lines.extend(_mixing_stream_result_lines(stream, states["in"][i], unit_system, ideal_gas))
    lines.append("")
    lines.append("Outputs")
    for i, stream in enumerate(streams["out"]):
        lines.extend(_mixing_stream_result_lines(stream, states["out"][i], unit_system, ideal_gas))

    entropy_keys = ["T0", "Sdot", "sigma", "ExD"]
    entropy_keys = _ordered_known_then_unknown(
        entropy_keys,
        lambda key: values.get(key) is None
    )
    lines.append("")
    for key in entropy_keys:
        lines.append(_format_turbine_value(key, values.get(key), unit_system, ideal_gas, {"1": None, "2": None}))

    if result["errors"]:
        lines.append("")
        lines.append("Check inputs")
        for message in result["errors"]:
            lines.append("- " + str(message))

    if result["missing"]:
        lines.append("")
        lines.append("Missing info")
        seen = []
        for message in result["missing"]:
            if message not in seen:
                seen.append(message)
                lines.append("- " + message)

    if result["notes"]:
        lines.append("")
        lines.append("Notes")
        for message in result["notes"]:
            lines.append("- " + message)

    return lines


def _history_record_mixing_chamber(fluid, unit_system, ideal_gas, input_streams, input_values, result):
    if result is None:
        return
    streams = result.get("streams", {})
    states = result.get("states", {})
    model = "Ideal Gas" if ideal_gas else "Non Ideal Gas"
    lines = [
        "Mixing Chamber Solver",
        "Adiabatic, " + _history_fluid_name(fluid) + ", " + _history_unit_name(unit_system) + ", " + model,
        "",
        "Given:",
    ]

    any_given = False
    for side in ("in", "out"):
        for i, input_stream in enumerate(input_streams[side]):
            stream = input_stream.copy()
            stream["side"] = side
            stream["index"] = i + 1
            row = states.get(side, [None] * len(input_streams[side]))[i] if i < len(states.get(side, [])) else None
            for field in ("T", "p", "x", "mdot"):
                if ideal_gas and field == "x":
                    continue
                if input_stream.get(field) is not None:
                    lines.append(_format_mixing_stream_value(field, stream, row, unit_system, ideal_gas))
                    any_given = True
    if not any_given:
        if input_values.get("T0") is not None:
            lines.append(_format_turbine_value("T0", input_values.get("T0"), unit_system, ideal_gas, {"1": None, "2": None}))
            any_given = True
    elif input_values.get("T0") is not None:
        lines.append(_format_turbine_value("T0", input_values.get("T0"), unit_system, ideal_gas, {"1": None, "2": None}))
    if not any_given:
        lines.append("None")

    lines.extend(["", "Found:"])
    any_found = False
    for side in ("in", "out"):
        for i, stream in enumerate(streams.get(side, [])):
            row = states.get(side, [None] * len(streams.get(side, [])))[i] if i < len(states.get(side, [])) else None
            input_stream = input_streams[side][i]
            for field in ("T", "p", "x", "mdot", "h"):
                if ideal_gas and field == "x":
                    continue
                if field != "h" and input_stream.get(field) is not None:
                    continue
                if not _mixing_stream_value_is_unknown(field, stream, row, unit_system, ideal_gas):
                    lines.append(_format_mixing_stream_value(field, stream, row, unit_system, ideal_gas))
                    any_found = True
    for key in ("T0", "Sdot", "sigma", "ExD"):
        if result.get("values", {}).get(key) is not None:
            lines.append(_format_turbine_value(key, result["values"][key], unit_system, ideal_gas, {"1": None, "2": None}))
            any_found = True
    if not any_found:
        lines.append("No additional values solved.")

    if result.get("errors"):
        lines.extend(["", "Check inputs:"])
        for message in result["errors"]:
            lines.append("- " + str(message))
    if result.get("missing"):
        lines.extend(["", "Missing info:"])
        for message in result["missing"]:
            lines.append("- " + str(message))
    _history_add(lines)


def _prompt_turbine_solve_for(ideal_gas, isentropic, adiabatic):
    options = _turbine_solve_for_options(ideal_gas, isentropic, adiabatic)
    lines = ["Solve For", ""]
    valid = []
    for i, (_, label) in enumerate(options, start=1):
        opt = str(i)
        valid.append(opt)
        lines.append(opt + ". " + label)

    choice = paged_choice(lines, valid)
    if choice == GO_BACK:
        return GO_BACK
    return options[int(choice) - 1][0]


def turbine_solver_menu():
    isentropic = _prompt_yes_no("Is the turbine isentropic?")
    if isentropic == GO_BACK:
        return GO_BACK

    adiabatic = False
    if not isentropic:
        adiabatic = _prompt_yes_no("Is the turbine adiabatic?")
        if adiabatic == GO_BACK:
            return GO_BACK

    ideal_gas = _prompt_yes_no("Use ideal-gas model?")
    if ideal_gas == GO_BACK:
        return GO_BACK

    if ideal_gas:
        fluid = prompt_fluid(get_ideal_gas_options())
    else:
        fluid = prompt_fluid(SUPPORTED_FLUIDS)
    if fluid == GO_BACK:
        return GO_BACK

    unit_system = prompt_unit_system()
    if unit_system == GO_BACK:
        return GO_BACK

    solve_for = _prompt_turbine_solve_for(ideal_gas, isentropic, adiabatic)
    if solve_for == GO_BACK:
        return GO_BACK

    temp_unit = _turbine_temp_unit(unit_system, ideal_gas)
    pressure_unit = _turbine_pressure_unit(unit_system)
    mdot_unit = _turbine_mdot_unit(unit_system)
    power_unit = _turbine_power_unit(unit_system)
    entropy_unit = _turbine_entropy_unit(unit_system)
    entropy_rate_unit = _turbine_entropy_rate_unit(unit_system)
    t0_unit = _dead_state_temp_unit(unit_system)

    prompt_specs = [
        ("T1", "Enter T1 (" + temp_unit + ", u if unknown): "),
        ("p1", "Enter P1 (" + pressure_unit + ", u if unknown): "),
    ]
    if not ideal_gas:
        prompt_specs.append(("x1", "Enter x1 (quality, u if unknown): "))
    prompt_specs.extend([
        ("T2", "Enter T2 (" + temp_unit + ", u if unknown): "),
        ("p2", "Enter P2 (" + pressure_unit + ", u if unknown): "),
    ])
    if not ideal_gas:
        prompt_specs.append(("x2", "Enter x2 (quality, u if unknown): "))
    prompt_specs.extend([
        ("mdot", "Enter mdot (" + mdot_unit + ", u if unknown): "),
        ("W", "Enter W out (" + power_unit + ", u if unknown): "),
    ])
    if not isentropic:
        prompt_specs.append(("efficiency", "Enter efficiency (0-1 or %, u if unknown): "))
    if not adiabatic and not isentropic:
        prompt_specs.append(("Q", "Enter Q in (" + power_unit + ", u if unknown): "))
    if not isentropic:
        prompt_specs.append(("delta_s", "Enter delta s (" + entropy_unit + ", u if unknown): "))
        prompt_specs.append(("Sdot", "Enter Sdot (" + entropy_rate_unit + ", u if unknown): "))
        prompt_specs.append(("sigma", "Enter sigma (" + entropy_rate_unit + ", u if unknown): "))
        prompt_specs.append(("T0", "Enter T0 (" + t0_unit + ", u if unknown): "))

    values = {}
    for key, prompt in prompt_specs:
        value = safe_input_unknown_float(prompt)
        if value == GO_BACK:
            return GO_BACK
        values[key] = value
    input_values = values.copy()
    if ideal_gas:
        values["x1"] = None
        values["x2"] = None
    if adiabatic or isentropic:
        values["Q"] = 0.0
    else:
        values.setdefault("Q", None)
    if isentropic:
        values["delta_s"] = 0.0
        values["Sdot"] = 0.0
        values["sigma"] = 0.0
    else:
        values.setdefault("delta_s", None)
        values.setdefault("Sdot", None)
        values.setdefault("sigma", None)
        values.setdefault("T0", None)
        values.setdefault("ExD", None)

    result = solve_turbine(
        fluid, unit_system, ideal_gas,
        isentropic, adiabatic, values, solve_for=solve_for
    )
    _history_record_steady(
        "Turbine Solver", fluid, unit_system, ideal_gas,
        isentropic, adiabatic, input_values, result
    )
    return display_message(turbine_result_lines(result))


def compressor_solver_menu():
    isentropic = _prompt_yes_no("Is the compressor isentropic?")
    if isentropic == GO_BACK:
        return GO_BACK

    adiabatic = False
    if not isentropic:
        adiabatic = _prompt_yes_no("Is the compressor adiabatic?")
        if adiabatic == GO_BACK:
            return GO_BACK

    ideal_gas = _prompt_yes_no("Use ideal-gas model?")
    if ideal_gas == GO_BACK:
        return GO_BACK

    if ideal_gas:
        fluid = prompt_fluid(get_ideal_gas_options())
    else:
        fluid = prompt_fluid(SUPPORTED_FLUIDS)
    if fluid == GO_BACK:
        return GO_BACK

    unit_system = prompt_unit_system()
    if unit_system == GO_BACK:
        return GO_BACK

    solve_for = _prompt_turbine_solve_for(ideal_gas, isentropic, adiabatic)
    if solve_for == GO_BACK:
        return GO_BACK

    temp_unit = _turbine_temp_unit(unit_system, ideal_gas)
    pressure_unit = _turbine_pressure_unit(unit_system)
    mdot_unit = _turbine_mdot_unit(unit_system)
    power_unit = _turbine_power_unit(unit_system)
    entropy_unit = _turbine_entropy_unit(unit_system)
    entropy_rate_unit = _turbine_entropy_rate_unit(unit_system)
    t0_unit = _dead_state_temp_unit(unit_system)

    prompt_specs = [
        ("T1", "Enter T1 (" + temp_unit + ", u if unknown): "),
        ("p1", "Enter P1 (" + pressure_unit + ", u if unknown): "),
    ]
    if not ideal_gas:
        prompt_specs.append(("x1", "Enter x1 (quality, u if unknown): "))
    prompt_specs.extend([
        ("T2", "Enter T2 (" + temp_unit + ", u if unknown): "),
        ("p2", "Enter P2 (" + pressure_unit + ", u if unknown): "),
    ])
    if not ideal_gas:
        prompt_specs.append(("x2", "Enter x2 (quality, u if unknown): "))
    prompt_specs.extend([
        ("mdot", "Enter mdot (" + mdot_unit + ", u if unknown): "),
        ("W", "Enter W in (" + power_unit + ", u if unknown): "),
    ])
    if not isentropic:
        prompt_specs.append(("efficiency", "Enter efficiency (0-1 or %, u if unknown): "))
    if not adiabatic and not isentropic:
        prompt_specs.append(("Q", "Enter Q in (" + power_unit + ", u if unknown): "))
    if not isentropic:
        prompt_specs.append(("delta_s", "Enter delta s (" + entropy_unit + ", u if unknown): "))
        prompt_specs.append(("Sdot", "Enter Sdot (" + entropy_rate_unit + ", u if unknown): "))
        prompt_specs.append(("sigma", "Enter sigma (" + entropy_rate_unit + ", u if unknown): "))
        prompt_specs.append(("T0", "Enter T0 (" + t0_unit + ", u if unknown): "))

    values = {}
    for key, prompt in prompt_specs:
        value = safe_input_unknown_float(prompt)
        if value == GO_BACK:
            return GO_BACK
        values[key] = value
    input_values = values.copy()
    if ideal_gas:
        values["x1"] = None
        values["x2"] = None
    if adiabatic or isentropic:
        values["Q"] = 0.0
    else:
        values.setdefault("Q", None)
    if isentropic:
        values["delta_s"] = 0.0
        values["Sdot"] = 0.0
        values["sigma"] = 0.0
    else:
        values.setdefault("delta_s", None)
        values.setdefault("Sdot", None)
        values.setdefault("sigma", None)
        values.setdefault("T0", None)
        values.setdefault("ExD", None)

    result = solve_compressor(
        fluid, unit_system, ideal_gas,
        isentropic, adiabatic, values, solve_for=solve_for
    )
    _history_record_steady(
        "Compressor Solver", fluid, unit_system, ideal_gas,
        isentropic, adiabatic, input_values, result
    )
    return display_message(turbine_result_lines(result, title="Compressor Solver"))


def _prompt_piston_solve_for(ideal_gas, isentropic, adiabatic):
    options = _piston_solve_for_options(ideal_gas, isentropic, adiabatic)
    lines = ["Solve For", ""]
    valid = []
    for i, (_, label) in enumerate(options, start=1):
        opt = str(i)
        valid.append(opt)
        lines.append(opt + ". " + label)
    choice = paged_choice(lines, valid)
    if choice == GO_BACK:
        return GO_BACK
    return options[int(choice) - 1][0]


def _history_record_piston(fluid, unit_system, ideal_gas, isentropic, adiabatic, input_values, result):
    if result is None:
        return
    values = result.get("values", {})
    states = result.get("states", {})
    process = "Isentropic" if isentropic else ("Adiabatic" if adiabatic else "Non-adiabatic")
    model = "Ideal Gas" if ideal_gas else "Non Ideal Gas"
    lines = [
        "Piston Solver",
        process + ", " + _history_fluid_name(fluid) + ", " + _history_unit_name(unit_system) + ", " + model,
        "",
        "Given:",
    ]

    result_keys = ["T1", "p1"]
    if not ideal_gas:
        result_keys.append("x1")
    result_keys.append("V1")
    result_keys.extend(["T2", "p2"])
    if not ideal_gas:
        result_keys.append("x2")
    result_keys.extend(["V2", "A", "m", "W", "Q", "delta_s", "Sdot", "sigma"])
    if result.get("isentropic"):
        result_keys.append("ExD")
    else:
        result_keys.extend(["T0", "ExD"])

    any_given = False
    for key in result_keys:
        if key in input_values and input_values.get(key) is not None:
            lines.append(_format_piston_value(key, input_values.get(key), unit_system, ideal_gas, states))
            any_given = True
    if not any_given:
        lines.append("None")

    lines.extend(["", "Found:"])
    any_found = False
    for key in result_keys:
        if key not in input_values or input_values.get(key) is None:
            value = values.get(key)
            if value is not None:
                lines.append(_format_piston_value(key, value, unit_system, ideal_gas, states))
                any_found = True
    if not any_found:
        lines.append("No additional values solved.")

    if result.get("errors"):
        lines.extend(["", "Check inputs:"])
        for message in result["errors"]:
            lines.append("- " + str(message))
    if result.get("missing"):
        lines.extend(["", "Missing info:"])
        for message in result["missing"]:
            lines.append("- " + str(message))
    _history_add(lines)


def piston_solver_menu():
    isentropic = _prompt_yes_no("Is the piston process isentropic?")
    if isentropic == GO_BACK:
        return GO_BACK

    adiabatic = False
    if not isentropic:
        adiabatic = _prompt_yes_no("Is the piston process adiabatic?")
        if adiabatic == GO_BACK:
            return GO_BACK

    ideal_gas = _prompt_yes_no("Use ideal-gas model?")
    if ideal_gas == GO_BACK:
        return GO_BACK

    if ideal_gas:
        fluid = prompt_fluid(get_ideal_gas_options())
    else:
        fluid = prompt_fluid(SUPPORTED_FLUIDS)
    if fluid == GO_BACK:
        return GO_BACK

    unit_system = prompt_unit_system()
    if unit_system == GO_BACK:
        return GO_BACK

    solve_for = _prompt_piston_solve_for(ideal_gas, isentropic, adiabatic)
    if solve_for == GO_BACK:
        return GO_BACK

    temp_unit = _turbine_temp_unit(unit_system, ideal_gas)
    pressure_unit = _turbine_pressure_unit(unit_system)
    volume_unit = _piston_volume_unit(unit_system)
    area_unit = _piston_area_unit(unit_system)
    mass_unit = _piston_mass_unit(unit_system)
    energy_unit = _piston_energy_unit(unit_system)
    entropy_unit = _turbine_entropy_unit(unit_system)
    entropy_total_unit = _piston_entropy_total_unit(unit_system)
    t0_unit = _dead_state_temp_unit(unit_system)

    prompt_specs = [
        ("T1", "Enter T1 (" + temp_unit + ", u if unknown): "),
        ("p1", "Enter P1 (" + pressure_unit + ", u if unknown): "),
    ]
    if not ideal_gas:
        prompt_specs.append(("x1", "Enter x1 (quality, u if unknown): "))
    prompt_specs.append(("V1", "Enter V1 (" + volume_unit + ", u if unknown): "))
    prompt_specs.extend([
        ("T2", "Enter T2 (" + temp_unit + ", u if unknown): "),
        ("p2", "Enter P2 (" + pressure_unit + ", u if unknown): "),
    ])
    if not ideal_gas:
        prompt_specs.append(("x2", "Enter x2 (quality, u if unknown): "))
    prompt_specs.extend([
        ("V2", "Enter V2 (" + volume_unit + ", u if unknown): "),
        ("A", "Enter A (" + area_unit + ", u if unknown): "),
        ("m", "Enter m (" + mass_unit + ", u if unknown): "),
        ("W", "Enter W out (" + energy_unit + ", u if unknown): "),
    ])
    if not adiabatic and not isentropic:
        prompt_specs.append(("Q", "Enter Q in (" + energy_unit + ", u if unknown): "))
    if not isentropic:
        prompt_specs.append(("delta_s", "Enter delta s (" + entropy_unit + ", u if unknown): "))
        prompt_specs.append(("Sdot", "Enter Sdot (" + entropy_total_unit + ", u if unknown): "))
        prompt_specs.append(("sigma", "Enter sigma (" + entropy_total_unit + ", u if unknown): "))
        prompt_specs.append(("T0", "Enter T0 (" + t0_unit + ", u if unknown): "))

    values = {}
    for key, prompt in prompt_specs:
        value = safe_input_unknown_float(prompt)
        if value == GO_BACK:
            return GO_BACK
        values[key] = value
    input_values = values.copy()
    if ideal_gas:
        values["x1"] = None
        values["x2"] = None
    if adiabatic or isentropic:
        values["Q"] = 0.0
    else:
        values.setdefault("Q", None)
    if isentropic:
        values["delta_s"] = 0.0
        values["Sdot"] = 0.0
        values["sigma"] = 0.0
    else:
        values.setdefault("delta_s", None)
        values.setdefault("Sdot", None)
        values.setdefault("sigma", None)
        values.setdefault("T0", None)
        values.setdefault("ExD", None)

    result = solve_piston(
        fluid, unit_system, ideal_gas,
        isentropic, adiabatic, values, solve_for=solve_for
    )
    _history_record_piston(
        fluid, unit_system, ideal_gas,
        isentropic, adiabatic, input_values, result
    )
    return display_message(piston_result_lines(result))


def nozzle_solver_menu():
    isentropic = _prompt_yes_no("Is the nozzle isentropic?")
    if isentropic == GO_BACK:
        return GO_BACK

    ideal_gas = _prompt_yes_no("Use ideal-gas model?")
    if ideal_gas == GO_BACK:
        return GO_BACK

    if ideal_gas:
        fluid = prompt_fluid(get_ideal_gas_options())
    else:
        fluid = prompt_fluid(SUPPORTED_FLUIDS)
    if fluid == GO_BACK:
        return GO_BACK

    unit_system = prompt_unit_system()
    if unit_system == GO_BACK:
        return GO_BACK

    solve_for = _prompt_nozzle_solve_for(ideal_gas, isentropic)
    if solve_for == GO_BACK:
        return GO_BACK

    temp_unit = _turbine_temp_unit(unit_system, ideal_gas)
    pressure_unit = _turbine_pressure_unit(unit_system)
    velocity_unit = _nozzle_velocity_unit(unit_system)
    mdot_unit = _turbine_mdot_unit(unit_system)
    entropy_unit = _turbine_entropy_unit(unit_system)
    entropy_rate_unit = _turbine_entropy_rate_unit(unit_system)
    t0_unit = _dead_state_temp_unit(unit_system)

    prompt_specs = [
        ("T1", "Enter T1 (" + temp_unit + ", u if unknown): "),
        ("p1", "Enter P1 (" + pressure_unit + ", u if unknown): "),
    ]
    if not ideal_gas:
        prompt_specs.append(("x1", "Enter x1 (quality, u if unknown): "))
    prompt_specs.append(("V1", "Enter V1 (" + velocity_unit + ", u if unknown): "))
    prompt_specs.extend([
        ("T2", "Enter T2 (" + temp_unit + ", u if unknown): "),
        ("p2", "Enter P2 (" + pressure_unit + ", u if unknown): "),
    ])
    if not ideal_gas:
        prompt_specs.append(("x2", "Enter x2 (quality, u if unknown): "))
    prompt_specs.extend([
        ("V2", "Enter V2 (" + velocity_unit + ", u if unknown): "),
        ("mdot", "Enter mdot (" + mdot_unit + ", u if unknown): "),
    ])
    if not isentropic:
        prompt_specs.append(("delta_s", "Enter delta s (" + entropy_unit + ", u if unknown): "))
        prompt_specs.append(("Sdot", "Enter Sdot (" + entropy_rate_unit + ", u if unknown): "))
        prompt_specs.append(("sigma", "Enter sigma (" + entropy_rate_unit + ", u if unknown): "))
        prompt_specs.append(("T0", "Enter T0 (" + t0_unit + ", u if unknown): "))

    values = {}
    for key, prompt in prompt_specs:
        value = safe_input_unknown_float(prompt)
        if value == GO_BACK:
            return GO_BACK
        values[key] = value
    input_values = values.copy()
    if ideal_gas:
        values["x1"] = None
        values["x2"] = None
    if isentropic:
        values["delta_s"] = 0.0
        values["Sdot"] = 0.0
        values["sigma"] = 0.0
    else:
        values.setdefault("delta_s", None)
        values.setdefault("Sdot", None)
        values.setdefault("sigma", None)
        values.setdefault("T0", None)
        values.setdefault("ExD", None)

    result = solve_nozzle(
        fluid, unit_system, ideal_gas,
        isentropic, values, solve_for=solve_for
    )
    _history_record_nozzle(
        fluid, unit_system, ideal_gas,
        isentropic, input_values, result
    )
    return display_message(nozzle_result_lines(result))


def expansion_valve_solver_menu():
    fluid = prompt_fluid(SUPPORTED_FLUIDS)
    if fluid == GO_BACK:
        return GO_BACK

    unit_system = prompt_unit_system()
    if unit_system == GO_BACK:
        return GO_BACK

    temp_unit = _turbine_temp_unit(unit_system, False)
    pressure_unit = _turbine_pressure_unit(unit_system)
    t0_unit = _dead_state_temp_unit(unit_system)
    prompt_specs = [
        ("T1", "Enter T1 (" + temp_unit + ", u if unknown): "),
        ("p1", "Enter P1 (" + pressure_unit + ", u if unknown): "),
        ("x1", "Enter x1 (quality, u if unknown): "),
        ("T2", "Enter T2 (" + temp_unit + ", u if unknown): "),
        ("p2", "Enter P2 (" + pressure_unit + ", u if unknown): "),
        ("x2", "Enter x2 (quality, u if unknown): "),
        ("T0", "Enter T0 (" + t0_unit + ", u if unknown): "),
    ]

    values = {}
    for key, prompt in prompt_specs:
        value = safe_input_unknown_float(prompt)
        if value == GO_BACK:
            return GO_BACK
        values[key] = value
    input_values = values.copy()

    result = solve_expansion_valve(fluid, unit_system, values)
    _history_record_expansion_valve(fluid, unit_system, input_values, result)
    return display_message(expansion_valve_result_lines(result))


def _prompt_steady_fluid_model():
    ideal_gas = _prompt_yes_no("Use ideal-gas model?")
    if ideal_gas == GO_BACK:
        return GO_BACK

    if ideal_gas:
        fluid = prompt_fluid(get_ideal_gas_options())
    else:
        fluid = prompt_fluid(SUPPORTED_FLUIDS)
    if fluid == GO_BACK:
        return GO_BACK

    unit_system = prompt_unit_system()
    if unit_system == GO_BACK:
        return GO_BACK

    return ideal_gas, fluid, unit_system


def initially_evacuated_solver_menu():
    setup = _prompt_steady_fluid_model()
    if setup == GO_BACK:
        return GO_BACK
    ideal_gas, fluid, unit_system = setup

    temp_unit = _turbine_temp_unit(unit_system, ideal_gas)
    pressure_unit = _turbine_pressure_unit(unit_system)
    t0_unit = _dead_state_temp_unit(unit_system)
    prompt_specs = [
        ("T1", "Enter T1 (" + temp_unit + ", u if unknown): "),
        ("p1", "Enter P1 (" + pressure_unit + ", u if unknown): "),
    ]
    if not ideal_gas:
        prompt_specs.append(("x1", "Enter x1 (quality, u if unknown): "))
    prompt_specs.extend([
        ("T2", "Enter T2 (" + temp_unit + ", u if unknown): "),
        ("p2", "Enter P2 (" + pressure_unit + ", u if unknown): "),
    ])
    if not ideal_gas:
        prompt_specs.append(("x2", "Enter x2 (quality, u if unknown): "))
    prompt_specs.append(("T0", "Enter T0 (" + t0_unit + ", u if unknown): "))

    values = {}
    for key, prompt in prompt_specs:
        value = safe_input_unknown_float(prompt)
        if value == GO_BACK:
            return GO_BACK
        values[key] = value
    input_values = values.copy()

    result = solve_initially_evacuated(fluid, unit_system, ideal_gas, values)
    _history_record_initially_evacuated(fluid, unit_system, ideal_gas, input_values, result)
    return display_message(initially_evacuated_result_lines(result))


def multi_stream_mixing_chamber_solver_menu():
    setup = _prompt_steady_fluid_model()
    if setup == GO_BACK:
        return GO_BACK
    ideal_gas, fluid, unit_system = setup

    inlet_count = safe_input_positive_int("Enter number of inputs: ")
    if inlet_count == GO_BACK:
        return GO_BACK
    outlet_count = safe_input_positive_int("Enter number of outputs: ")
    if outlet_count == GO_BACK:
        return GO_BACK

    temp_unit = _turbine_temp_unit(unit_system, ideal_gas)
    pressure_unit = _turbine_pressure_unit(unit_system)
    mdot_unit = _turbine_mdot_unit(unit_system)
    t0_unit = _dead_state_temp_unit(unit_system)
    values = {}
    t0_value = safe_input_unknown_float("Enter T0 (" + t0_unit + ", u if unknown): ")
    if t0_value == GO_BACK:
        return GO_BACK
    values["T0"] = t0_value
    streams = {"in": [], "out": []}

    for side, count in (("in", inlet_count), ("out", outlet_count)):
        for i in range(1, count + 1):
            suffix = _mixing_stream_suffix(side, i)
            stream = {
                "side": side,
                "index": i,
                "T": None,
                "p": None,
                "x": None,
                "mdot": None,
            }
            prompt_specs = [
                ("T", "Enter T" + suffix + " (" + temp_unit + ", u if unknown): "),
                ("p", "Enter P" + suffix + " (" + pressure_unit + ", u if unknown): "),
            ]
            if not ideal_gas:
                prompt_specs.append(("x", "Enter x" + suffix + " (quality, u if unknown): "))
            prompt_specs.append(("mdot", "Enter mdot" + suffix + " (" + mdot_unit + ", u if unknown): "))

            for key, prompt in prompt_specs:
                value = safe_input_unknown_float(prompt)
                if value == GO_BACK:
                    return GO_BACK
                stream[key] = value
            if ideal_gas:
                stream["x"] = None
            streams[side].append(stream)

    input_streams = _copy_mixing_streams(streams)
    input_values = values.copy()
    result = solve_mixing_chamber(fluid, unit_system, ideal_gas, streams, values=values)
    _history_record_mixing_chamber(fluid, unit_system, ideal_gas, input_streams, input_values, result)
    return display_message(mixing_chamber_result_lines(result))


def mixing_chamber_solver_menu():
    lines = [
        "Mixing Chamber",
        "",
        "1. Initially evacuated",
        "2. Mixing Chamber",
    ]
    choice = paged_choice(lines, ["1", "2"])
    if choice == GO_BACK:
        return GO_BACK
    if choice == "1":
        return initially_evacuated_solver_menu()
    if choice == "2":
        return multi_stream_mixing_chamber_solver_menu()
    return None


def steady_state_solver_menu():
    lines = [
        "Steady-State Solver",
        "",
        "1. Turbine",
        "2. Compressor",
        "3. Piston",
        "4. Nozzles",
        "5. Expansion Valves",
        "6. Mixing Chamber",
    ]
    choice = paged_choice(lines, ["1", "2", "3", "4", "5", "6"])
    if choice == GO_BACK:
        return GO_BACK
    if choice == "1":
        return turbine_solver_menu()
    if choice == "2":
        return compressor_solver_menu()
    if choice == "3":
        return piston_solver_menu()
    if choice == "4":
        return nozzle_solver_menu()
    if choice == "5":
        return expansion_valve_solver_menu()
    if choice == "6":
        return mixing_chamber_solver_menu()
    return None


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


def _history_record_steady(title, fluid, unit_system, ideal_gas, isentropic, adiabatic, input_values, result):
    if result is None:
        return

    values = result.get("values", {})
    states = result.get("states", {})
    process = "Isentropic" if isentropic else ("Adiabatic" if adiabatic else "Non-adiabatic")
    model = "Ideal Gas" if ideal_gas else "Non Ideal Gas"

    lines = [
        title,
        process + ", " + _history_fluid_name(fluid) + ", " + _history_unit_name(unit_system) + ", " + model,
        "",
        "Given:",
    ]

    result_keys = ["T1", "p1"]
    if not ideal_gas:
        result_keys.append("x1")
    result_keys.extend(["T2", "p2"])
    if not ideal_gas:
        result_keys.append("x2")
    result_keys.extend(["mdot", "W", "efficiency", "Q", "delta_s", "Sdot", "sigma"])
    if result.get("isentropic"):
        result_keys.append("ExD")
    else:
        result_keys.extend(["T0", "ExD"])

    any_given = False
    for key in result_keys:
        if key in input_values and input_values.get(key) is not None:
            lines.append(_format_turbine_value(key, input_values.get(key), unit_system, ideal_gas, states))
            any_given = True
    if not any_given:
        lines.append("None")

    lines.extend(["", "Found:"])
    any_found = False
    for key in result_keys:
        if key not in input_values or input_values.get(key) is None:
            value = values.get(key)
            if value is not None:
                lines.append(_format_turbine_value(key, value, unit_system, ideal_gas, states))
                any_found = True
    if not any_found:
        lines.append("No additional values solved.")

    if result.get("errors"):
        lines.extend(["", "Check inputs:"])
        for message in result["errors"]:
            lines.append("- " + str(message))
    if result.get("missing"):
        lines.extend(["", "Missing info:"])
        for message in result["missing"]:
            lines.append("- " + str(message))

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


def _carnot_energy_unit(unit_system):
    return "kJ" if _unit_system_key(unit_system) == "metric" else "Btu"


def _carnot_temp_unit(unit_system):
    return "K" if _unit_system_key(unit_system) == "metric" else "R"


def _carnot_entropy_unit(unit_system):
    return "kJ/K" if _unit_system_key(unit_system) == "metric" else "Btu/R"


def _carnot_performance_key(device):
    return "efficiency" if device == "heat_engine" else "COP"


def _carnot_device_label(device):
    labels = {
        "heat_engine": "Heat Engine",
        "refrigerator": "Refrigerator",
        "heat_pump": "Heat Pump",
    }
    return labels.get(device, str(device))


def _carnot_reversible_label(reversible):
    if reversible is True:
        return "Yes"
    if reversible is False:
        return "No"
    return "Unknown"


def _normalize_carnot_performance(device, value, notes):
    val = _safe_float(value)
    if val is None:
        return None
    if device == "heat_engine" and val > 1.0 and val <= 100.0:
        notes.append("Efficiency entered above 1 was interpreted as percent.")
        val = val / 100.0
    return val


def _solve_carnot_energy_balance(values):
    changed = False
    qh = _safe_float(values.get("Q_H"))
    ql = _safe_float(values.get("Q_L"))
    work = _safe_float(values.get("W"))
    if values.get("W") is None and qh is not None and ql is not None:
        values["W"] = qh - ql
        changed = True
    elif values.get("Q_H") is None and ql is not None and work is not None:
        values["Q_H"] = ql + work
        changed = True
    elif values.get("Q_L") is None and qh is not None and work is not None:
        values["Q_L"] = qh - work
        changed = True
    return changed


def _solve_carnot_performance_relation(values, device):
    changed = False
    key = _carnot_performance_key(device)
    perf = _safe_float(values.get(key))
    qh = _safe_float(values.get("Q_H"))
    ql = _safe_float(values.get("Q_L"))
    work = _safe_float(values.get("W"))

    if device == "heat_engine":
        if values.get("efficiency") is None and work is not None and qh not in (None, 0):
            values["efficiency"] = work / qh
            changed = True
        elif values.get("W") is None and perf is not None and qh is not None:
            values["W"] = perf * qh
            changed = True
        elif values.get("Q_H") is None and perf not in (None, 0) and work is not None:
            values["Q_H"] = work / perf
            changed = True
        elif values.get("Q_L") is None and perf is not None and qh is not None:
            values["Q_L"] = qh * (1.0 - perf)
            changed = True
        elif values.get("Q_H") is None and perf is not None and perf != 1.0 and ql is not None:
            values["Q_H"] = ql / (1.0 - perf)
            changed = True
        return changed

    numerator_key = "Q_L" if device == "refrigerator" else "Q_H"
    numerator = ql if device == "refrigerator" else qh
    if values.get("COP") is None and numerator is not None and work not in (None, 0):
        values["COP"] = numerator / work
        changed = True
    elif values.get(numerator_key) is None and perf is not None and work is not None:
        values[numerator_key] = perf * work
        changed = True
    elif values.get("W") is None and perf not in (None, 0) and numerator is not None:
        values["W"] = numerator / perf
        changed = True
    return changed


def _carnot_temp_performance(device, th, tl):
    if th is None or tl is None:
        return None
    th = float(th)
    tl = float(tl)
    if th <= 0.0 or tl <= 0.0 or th <= tl:
        return None
    if device == "heat_engine":
        return 1.0 - tl / th
    if device == "refrigerator":
        return tl / (th - tl)
    if device == "heat_pump":
        return th / (th - tl)
    return None


def _solve_carnot_entropy_values(values, device):
    changed = False
    qh = _safe_float(values.get("Q_H"))
    ql = _safe_float(values.get("Q_L"))
    th = _safe_float(values.get("T_H"))
    tl = _safe_float(values.get("T_L"))
    s_high = None
    s_low = None

    if qh is not None and th not in (None, 0):
        if device == "heat_engine":
            s_high = -qh / th
        else:
            s_high = qh / th
    if ql is not None and tl not in (None, 0):
        if device == "heat_engine":
            s_low = ql / tl
        else:
            s_low = -ql / tl

    if values.get("Sdot_H") is None and s_high is not None:
        values["Sdot_H"] = s_high
        changed = True
    if values.get("Sdot_L") is None and s_low is not None:
        values["Sdot_L"] = s_low
        changed = True
    if values.get("sigma") is None and s_high is not None and s_low is not None:
        values["sigma"] = s_high + s_low
        changed = True
    return changed


def _solve_reversible_temp_relation(values, device):
    changed = False
    key = _carnot_performance_key(device)
    th = _safe_float(values.get("T_H"))
    tl = _safe_float(values.get("T_L"))
    perf = _safe_float(values.get(key))

    if values.get(key) is None and th is not None and tl is not None:
        solved = _carnot_temp_performance(device, th, tl)
        if solved is not None:
            values[key] = solved
            changed = True
    elif device == "heat_engine" and perf is not None:
        if values.get("T_L") is None and th is not None:
            values["T_L"] = th * (1.0 - perf)
            changed = True
        elif values.get("T_H") is None and tl is not None and perf != 1.0:
            values["T_H"] = tl / (1.0 - perf)
            changed = True
    elif device == "refrigerator" and perf not in (None, 0):
        if values.get("T_H") is None and tl is not None:
            values["T_H"] = tl * (1.0 + 1.0 / perf)
            changed = True
        elif values.get("T_L") is None and th is not None:
            values["T_L"] = perf * th / (perf + 1.0)
            changed = True
    elif device == "heat_pump" and perf is not None:
        if values.get("T_L") is None and th is not None and perf != 0.0:
            values["T_L"] = th * (1.0 - 1.0 / perf)
            changed = True
        elif values.get("T_H") is None and tl is not None and perf != 1.0:
            values["T_H"] = perf * tl / (perf - 1.0)
            changed = True

    th = _safe_float(values.get("T_H"))
    tl = _safe_float(values.get("T_L"))
    qh = _safe_float(values.get("Q_H"))
    ql = _safe_float(values.get("Q_L"))
    if th is not None and tl is not None and th != 0.0:
        ratio = tl / th
        if values.get("Q_L") is None and qh is not None:
            values["Q_L"] = qh * ratio
            changed = True
        elif values.get("Q_H") is None and ql is not None and ratio != 0.0:
            values["Q_H"] = ql / ratio
            changed = True
    elif qh not in (None, 0) and ql is not None:
        ratio = ql / qh
        if values.get("T_L") is None and th is not None:
            values["T_L"] = th * ratio
            changed = True
        elif values.get("T_H") is None and tl is not None and ratio != 0.0:
            values["T_H"] = tl / ratio
            changed = True
    return changed


def solve_carnot_cycle(device, reversible, values):
    values = values.copy()
    notes = []
    errors = []
    missing = []
    key = _carnot_performance_key(device)
    values[key] = _normalize_carnot_performance(device, values.get(key), notes)
    values.setdefault("T0", None)
    values.setdefault("ExD", None)
    if reversible is True:
        values["sigma"] = 0.0
        values["ExD"] = 0.0

    for numeric_key in ("T_H", "T_L", "Q_H", "Q_L", "W", key):
        if values.get(numeric_key) is not None and float(values[numeric_key]) < 0.0:
            errors.append(numeric_key + " must be nonnegative.")
    _check_t0_value(values, errors)
    if values.get("T_H") is not None and values.get("T_L") is not None:
        if float(values["T_H"]) <= float(values["T_L"]):
            errors.append("T_H must be greater than T_L.")

    for _ in range(8):
        changed = False
        if _solve_carnot_energy_balance(values):
            changed = True
        if _solve_carnot_performance_relation(values, device):
            changed = True
        if reversible is True and _solve_reversible_temp_relation(values, device):
            changed = True
        if _solve_carnot_entropy_values(values, device):
            changed = True
        if _solve_exergy_destruction(values):
            changed = True
        if not changed:
            break

    _solve_carnot_energy_balance(values)
    _solve_carnot_performance_relation(values, device)
    _solve_carnot_entropy_values(values, device)
    if reversible is True and values.get("sigma") is not None and _close_enough(values.get("sigma"), 0.0):
        values["ExD"] = 0.0
    _solve_exergy_destruction(values)

    qh = _safe_float(values.get("Q_H"))
    ql = _safe_float(values.get("Q_L"))
    work = _safe_float(values.get("W"))
    perf = _safe_float(values.get(key))
    th = _safe_float(values.get("T_H"))
    tl = _safe_float(values.get("T_L"))
    carnot_perf = _carnot_temp_performance(device, th, tl)

    if qh is not None and ql is not None and work is not None:
        if not _close_enough(qh, ql + work):
            errors.append("Cycle energy balance requires Q_H = Q_L + W.")
    if device == "heat_engine" and perf is not None:
        if perf > 1.0:
            errors.append("Heat-engine efficiency cannot exceed 1.")
        if qh not in (None, 0) and work is not None and not _close_enough(perf, work / qh):
            errors.append("Efficiency must equal W / Q_H.")
    if device in ("refrigerator", "heat_pump") and perf is not None:
        numerator = ql if device == "refrigerator" else qh
        if numerator is not None and work not in (None, 0) and not _close_enough(perf, numerator / work):
            errors.append("COP does not match the heat/work inputs.")

    if reversible is True and carnot_perf is not None and perf is not None:
        if not _close_enough(perf, carnot_perf):
            errors.append("Reversible/Carnot performance does not match the temperature reservoirs.")
    if reversible is True and None not in (qh, ql, th, tl):
        if qh == 0.0 or th == 0.0 or not _close_enough(ql / qh, tl / th):
            errors.append("Reversible/Carnot heat ratio requires Q_L / Q_H = T_L / T_H.")
    sigma = _safe_float(values.get("sigma"))
    if sigma is not None:
        if reversible is True and not _close_enough(sigma, 0.0):
            errors.append("Reversible cycles require sigma = 0.")
        elif reversible is False and (sigma < 0.0 or _close_enough(sigma, 0.0)):
            errors.append("Irreversible cycles require positive entropy generation.")
        elif sigma < 0.0:
            errors.append("Entropy generation cannot be negative.")
    if reversible is False and carnot_perf is not None and perf is not None:
        if perf > carnot_perf or _close_enough(perf, carnot_perf):
            errors.append("Irreversible devices must perform below the Carnot limit.")
    if reversible is None and carnot_perf is not None and perf is not None:
        if _close_enough(perf, carnot_perf):
            notes.append("Performance matches the reversible Carnot value for the given reservoirs.")
        elif perf < carnot_perf:
            notes.append("Performance is below the reversible Carnot limit.")
        else:
            errors.append("Performance exceeds the reversible Carnot limit.")

    for out_key in ("T_H", "T_L", "Q_H", "Q_L", "W", key, "Sdot_H", "Sdot_L", "sigma"):
        if values.get(out_key) is None:
            missing.append(out_key + " needs more information.")
    if values.get("ExD") is None:
        missing.append("Exergy destruction needs T0 and sigma.")

    return {
        "values": values,
        "device": device,
        "reversible": reversible,
        "errors": errors,
        "missing": missing,
        "notes": notes,
    }


def _format_carnot_value(key, value, unit_system, device):
    if key == "T0":
        return _format_dead_state_temperature(value, unit_system)
    if key in ("T_H", "T_L"):
        return _ideal_change_display_value(key, value, unit_system)
    if key in ("Q_H", "Q_L", "W"):
        label = key
        unit = _carnot_energy_unit(unit_system)
        value_text = "u" if value is None else _display_number(value)
        if value_text == "u":
            return label + " = u"
        return label + " = " + value_text + " " + unit
    if key == "efficiency":
        value_text = "u" if value is None else _display_number(value)
        return "efficiency = " + value_text
    if key == "COP":
        value_text = "u" if value is None else _display_number(value)
        return "COP = " + value_text
    if key in ("Sdot_H", "Sdot_L", "sigma"):
        value_text = "u" if value is None else _display_number(value)
        label = {
            "Sdot_H": "Sdot_H",
            "Sdot_L": "Sdot_L",
            "sigma": "sigma",
        }[key]
        if value_text == "u":
            return label + " = u"
        return label + " = " + value_text + " " + _carnot_entropy_unit(unit_system)
    if key == "ExD":
        value_text = "u" if value is None else _display_number(value)
        if value_text == "u":
            return "Exergy destruction = u"
        return "Exergy destruction = " + value_text + " " + _carnot_energy_unit(unit_system)
    return key + " = " + ("u" if value is None else _display_number(value))


def carnot_result_lines(result, unit_system):
    values = result["values"]
    device = result["device"]
    perf_key = _carnot_performance_key(device)
    lines = [
        "Carnot Cycles",
        _carnot_device_label(device),
        "Reversible: " + _carnot_reversible_label(result["reversible"]),
        "",
        "Results",
    ]
    keys = ("T_H", "T_L", "Q_H", "Q_L", "W", perf_key, "Sdot_H", "Sdot_L", "sigma", "T0", "ExD")
    ordered = _ordered_known_then_unknown(keys, lambda item: values.get(item) is None)
    for item in ordered:
        lines.append(_format_carnot_value(item, values.get(item), unit_system, device))

    if result["errors"]:
        lines.extend(["", "Check inputs"])
        for message in result["errors"]:
            lines.append("- " + str(message))
    if result["missing"]:
        lines.extend(["", "Missing info"])
        seen = []
        for message in result["missing"]:
            if message not in seen:
                seen.append(message)
                lines.append("- " + message)
    if result["notes"]:
        lines.extend(["", "Notes"])
        for message in result["notes"]:
            lines.append("- " + str(message))
    return lines


def _history_record_carnot(unit_system, input_values, result):
    if result is None:
        return
    values = result["values"]
    device = result["device"]
    perf_key = _carnot_performance_key(device)
    keys = ("T_H", "T_L", "Q_H", "Q_L", "W", perf_key, "Sdot_H", "Sdot_L", "sigma", "T0", "ExD")
    lines = [
        "Carnot Cycles",
        _carnot_device_label(device) + ", " + _history_unit_name(unit_system),
        "Reversible: " + _carnot_reversible_label(result["reversible"]),
        "",
        "Given:",
    ]
    any_given = False
    for key in keys:
        if input_values.get(key) is not None:
            lines.append(_format_carnot_value(key, input_values.get(key), unit_system, device))
            any_given = True
    if not any_given:
        lines.append("None")

    lines.extend(["", "Found:"])
    any_found = False
    for key in keys:
        if input_values.get(key) is None and values.get(key) is not None:
            lines.append(_format_carnot_value(key, values.get(key), unit_system, device))
            any_found = True
    if not any_found:
        lines.append("No additional values solved.")
    if result.get("errors"):
        lines.extend(["", "Check inputs:"])
        for message in result["errors"]:
            lines.append("- " + str(message))
    if result.get("missing"):
        lines.extend(["", "Missing info:"])
        for message in result["missing"]:
            lines.append("- " + str(message))
    _history_add(lines)


def _prompt_carnot_reversible():
    lines = [
        "System Reversible?",
        "",
        "1. Yes",
        "2. No",
        "3. Unknown",
    ]
    choice = paged_choice(lines, ["1", "2", "3"])
    if choice == GO_BACK:
        return GO_BACK
    if choice == "1":
        return True
    if choice == "2":
        return False
    return None


def _prompt_carnot_device():
    lines = [
        "Carnot Cycle Type",
        "",
        "1. Heat Engine",
        "2. Refrigerator",
        "3. Heat Pump",
    ]
    choice = paged_choice(lines, ["1", "2", "3"])
    if choice == GO_BACK:
        return GO_BACK
    return {
        "1": "heat_engine",
        "2": "refrigerator",
        "3": "heat_pump",
    }[choice]


def carnot_cycles_menu():
    reversible = _prompt_carnot_reversible()
    if reversible == GO_BACK:
        return GO_BACK
    device = _prompt_carnot_device()
    if device == GO_BACK:
        return GO_BACK
    unit_system = prompt_unit_system()
    if unit_system == GO_BACK:
        return GO_BACK

    temp_unit = _carnot_temp_unit(unit_system)
    energy_unit = _carnot_energy_unit(unit_system)
    perf_key = _carnot_performance_key(device)
    perf_prompt = "Enter efficiency (0-1 or %, u if unknown): " if device == "heat_engine" else "Enter COP (u if unknown): "
    prompt_specs = [
        ("T_H", "Enter T_H (" + temp_unit + ", u if unknown): "),
        ("T_L", "Enter T_L (" + temp_unit + ", u if unknown): "),
        ("Q_H", "Enter Q_H (" + energy_unit + ", u if unknown): "),
        ("Q_L", "Enter Q_L (" + energy_unit + ", u if unknown): "),
        ("W", "Enter W (" + energy_unit + ", u if unknown): "),
        (perf_key, perf_prompt),
        ("T0", "Enter T0 (" + temp_unit + ", u if unknown): "),
    ]
    values = {}
    for key, prompt in prompt_specs:
        value = safe_input_unknown_float(prompt)
        if value == GO_BACK:
            return GO_BACK
        values[key] = value

    result = solve_carnot_cycle(device, reversible, values)
    _history_record_carnot(unit_system, values, result)
    return display_message(carnot_result_lines(result, unit_system))
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
    dispatch = {'1': 'real_fluid_lookup_menu', '2': 'ideal_gas_lookup_menu', '3': 'steady_state_solver_menu', '4': 'carnot_cycles_menu', '5': 'unit_conversion_menu', '6': 'history_menu', '7': 'quit'}
    lines = ['Thermo', '', '1. Real Fluid lookup', '2. Ideal Gas Lookup', '3. Steady State Solver', '4. Carnot Cycles', '5. Unit Converter', '6. History', '7. Quit']
    while True:
        choice = paged_choice(lines, ['1', '2', '3', '4', '5', '6', '7'])
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
