# =============================================================================
# Chapter 3: Loads and Load Combinations
# Refactored for FOSSEE OsdagBridge Standards:
#   - Clean separation of Vehicle Live Loads and Footpath Live Loads (Cl. 206)
#   - LongTable headers repeated on page breaks (\endhead, \endfirsthead)
#   - Color shaded headers matching ReportStyle (tableHeaderBg)
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_CB_LOAD,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_IRC_CLASS_SV,
    KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_PL_SELF_WEIGHT_FACTOR,
    KEY_RL_LOAD_VALUE,
    KEY_SL_DAMPING,
    KEY_SL_DEAD_LOAD_MODE,
    KEY_SL_DEAD_LOAD_VALUE,
    KEY_SL_HORIZONTAL_COEFF,
    KEY_SL_IMPORTANCE_FACTOR,
    KEY_SL_LIVE_LOAD_MODE,
    KEY_SL_LIVE_LOAD_VALUE,
    KEY_SL_SEISMIC_ZONE,
    KEY_SL_SOIL_TYPE,
    KEY_SL_SPECTRAL_COEFF,
    KEY_SL_TIME_PERIOD,
    KEY_SL_VERTICAL_COEFF,
    KEY_SL_ZONE_FACTOR,
    KEY_SPAN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_HIGHEST_MAX_TEMP,
    KEY_TL_LOWEST_MIN_TEMP,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_NO_OF_FOOTPATHS,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_BASIC_WIND_SPEED,
    KEY_WL_HOURLY_MEAN_WIND,
    KEY_WL_HOURLY_WIND_PRESSURE,
    KEY_WL_LONGITUDINAL_WIND_FORCE,
    KEY_WL_TERRAIN_TYPE,
    KEY_WL_TRANSVERSE_WIND_FORCE,
    KEY_WL_VERTICAL_WIND_FORCE
)

from osdagbridge.core.reports.report_utils import _tex, _render_value, build_table_with_headers


def ch3_loads(input_dict):
    # Live load vehicle names mapping
    vehicles = []
    if input_dict.get(KEY_LL_IRC_CLASS_A):
        vehicles.append("Class A")
    if input_dict.get(KEY_LL_IRC_70R_WHEELED):
        vehicles.append("Class 70R (Wheeled)")
    if input_dict.get(KEY_LL_IRC_70R_TRACKED):
        vehicles.append("Class 70R (Tracked)")
    if input_dict.get(KEY_LL_IRC_AA_WHEELED):
        vehicles.append("Class AA (Wheeled)")
    if input_dict.get(KEY_LL_IRC_AA_TRACKED):
        vehicles.append("Class AA (Tracked)")
    if input_dict.get(KEY_LL_IRC_CLASS_SV):
        vehicles.append("Class SV")
    if input_dict.get(KEY_LL_IRC_70R_BOGIE):
        vehicles.append("Class 70R (Bogie)")
    if input_dict.get(KEY_LL_IRC_CLASS_FATIGUE):
        vehicles.append("Class Fatigue")
    
    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            if isinstance(c, dict) and c.get('name'):
                vehicles.append(c['name'])
            elif isinstance(c, str):
                vehicles.append(c)
                
    vehicles_str = ", ".join(vehicles) if vehicles else "None"

    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
    span = input_dict.get(KEY_SPAN)
    impact_factor_str = ""
    if span not in (None, ""):
        try:
            span_m = float(span)
            factors = []
            if input_dict.get(KEY_LL_IRC_CLASS_A):
                im_a = IRC6_2017.cl_208_2_impact_factor(span_m)
                factors.append(f"Class A: {1.0 + im_a:.3f}")
            is_wheeled_heavy = (
                input_dict.get(KEY_LL_IRC_70R_WHEELED) or 
                input_dict.get(KEY_LL_IRC_AA_WHEELED) or 
                input_dict.get(KEY_LL_IRC_70R_BOGIE)
            )
            is_tracked_heavy = (
                input_dict.get(KEY_LL_IRC_70R_TRACKED) or 
                input_dict.get(KEY_LL_IRC_AA_TRACKED)
            )
            if is_wheeled_heavy or is_tracked_heavy:
                im_aa = IRC6_2017.cl_208_3_impact_factor(span_m)
                factors.append(f"Class AA/70R: {1.0 + im_aa:.3f}")
            
            if factors:
                impact_factor_str = ", ".join(factors)
            else:
                impact_factor_str = "N/A"
        except Exception:
            impact_factor_str = "N/A"
    else:
        impact_factor_str = "N/A"

    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    braking_force_str = ""
    if lanes not in (None, ""):
        try:
            lanes_int = int(lanes)
            braking_force_t = IRC6_2017.cl_211_2_braking_force(lanes_int)
            braking_force_kN = braking_force_t * 9.81
            braking_force_str = f"{braking_force_kN:.2f} kN ({braking_force_t:.2f} tonnes)"
        except Exception:
            braking_force_str = "N/A"
    else:
        braking_force_str = "N/A"

    # Footpath / Pedestrian loading
    fp_mode = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")
    fp_width = input_dict.get(KEY_TS_FOOTPATH_WIDTH, "")
    fp_count = input_dict.get(KEY_TS_NO_OF_FOOTPATHS, "None")
    
    if str(fp_mode).strip().lower() in ("as per irc 6", "as per irc6", "automatic"):
        try:
            fp_intensity = f"{IRC6_2017.cl_206_1_footway_load():.3f} kN/m\\textsuperscript{{2}}"
            fp_rule = "IRC 6:2017 Cl. 206.1 (5.0 kN/m\\textsuperscript{2} base reduced for span)"
        except Exception:
            fp_intensity = "4.000 kN/m\\textsuperscript{2}"
            fp_rule = "IRC 6:2017 Cl. 206.1"
    elif fp_value not in (None, ""):
        fp_intensity = f"{_tex(fp_value)} kN/m\\textsuperscript{{2}}"
        fp_rule = "User Defined Input"
    else:
        fp_intensity = "4.000 kN/m\\textsuperscript{2}"
        fp_rule = "IRC 6:2017 Standard Footway Live Load"

    fp_width_str = f"{_tex(fp_width)} mm" if fp_width not in (None, "") else "Not Applicable (No Footpath)"

    # Vz / Pz — prefer stored computed values; fall back to IRC6 Table 12
    vz_val = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    pz_val = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)
    if not vz_val or not pz_val:
        try:
            _vb = input_dict.get(KEY_WL_BASIC_WIND_SPEED) or input_dict.get('wind_speed')
            _h = input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT)
            _ter = {
                "Plain Terrain": "plain",
                "Terrain with Obstructions": "obstructed",
            }.get(str(input_dict.get(KEY_WL_TERRAIN_TYPE, "")).strip(), "plain")
            _res = IRC6_2017.table_12(float(_h), _ter, float(_vb))
            if not vz_val:
                vz_val = _res.get("Vz")
            if not pz_val:
                pz_val = _res.get("Pz")
        except Exception:
            pass
    vz_str = f"{float(vz_val):.2f} m/s" if vz_val not in (None, "") else "N/A"
    pz_str = f"{float(pz_val):.2f} N/m²" if pz_val not in (None, "") else "N/A"

    # Table 3.5 — Seismic: prefer stored computed values; fall back to IRC6 cl_218_5_1
    sl_zone_factor = input_dict.get(KEY_SL_ZONE_FACTOR)
    sl_spectral = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    sl_ah = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    sl_av = input_dict.get(KEY_SL_VERTICAL_COEFF)
    if not sl_ah or not sl_zone_factor:
        try:
            _zone = input_dict.get(KEY_SL_SEISMIC_ZONE) or input_dict.get('seismic_zone')
            _zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            _z = str(_zone).strip().upper()
            if _z.isdigit():
                _z = _zmap.get(_z)
            _smap = {"Type I – Rocky or Hard": 1, "Type II – Medium Soil": 2, "Type III – Soft Soil": 3}
            _st = _smap.get(str(input_dict.get(KEY_SL_SOIL_TYPE, "")), 1)
            _tp = input_dict.get(KEY_SL_TIME_PERIOD)
            _damp = input_dict.get(KEY_SL_DAMPING) or "5"
            _dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            _ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
            _dead = float(_dl_v) if str(input_dict.get(KEY_SL_DEAD_LOAD_MODE, "")) == "Custom" and _dl_v else 0.0
            _live = float(_ll_v) if str(input_dict.get(KEY_SL_LIVE_LOAD_MODE, "")) == "Custom" and _ll_v else 0.0
            _res = IRC6_2017.cl_218_5_1(zone=f"Zone {_z}", soil_type=_st, dead_load_kN=_dead,
                        live_load_kN=_live, period_T=float(_tp) if _tp else None,
                        damping_percent=float(_damp))
            if not sl_zone_factor:
                sl_zone_factor = _res.get("Z")
            if not sl_spectral:
                sl_spectral = _res.get("Sa_g_adjusted")
            if not sl_ah:
                sl_ah = _res.get("Ah")
            if not sl_av:
                sl_av = round(_res.get("Ah", 0) * 2 / 3, 4)
        except Exception:
            pass

    def _sl(v, unit=""):
        return f"{float(v):.4f}{unit}" if v not in (None, "") else "N/A"

    # Temperature
    tl_temp_min = tl_temp_max = tl_rise = tl_fall = "N/A"
    try:
        _tmax = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP) or input_dict.get('shade_temp_max')
        _tmin = input_dict.get(KEY_TL_LOWEST_MIN_TEMP) or input_dict.get('shade_temp_min')
        if _tmax and _tmin:
            _res = IRC6_2017.cl_215_2_effective_bridge_temperature(
                          float(_tmax), float(_tmin), 'metallic', False)
            _bt_min = _res.get('T_min', 0)
            _bt_max = _res.get('T_max', 0)
            _mean = (_bt_max + _bt_min) / 2.0
            tl_temp_min = f"{_bt_min:.2f}"
            tl_temp_max = f"{_bt_max:.2f}"
            tl_rise = f"{_bt_max - _mean:.2f}"
            tl_fall = f"{_mean - _bt_min:.2f}"
    except Exception:
        pass

    # --- Load Combinations ---
    _LOAD_LABEL_MAP = {
        'dead_load': 'DL',
        'surfacing': 'SIDL',
        'live_load': 'LL',
        'wind_load': 'WL',
        'thermal_load': 'TL',
        'vehicle_collision': 'VC',
        'barge_impact': 'BI',
        'floating_bodies': 'FB',
        'seismic': 'EQ',
    }

    def _fmt_factors(factors):
        parts = []
        for load, val in factors.items():
            label = _LOAD_LABEL_MAP.get(load, load.upper())
            if isinstance(val, dict):
                add = val.get('adding')
                rel = val.get('relieving')
                add_s = f"{add:.2f}" if add is not None else '--'
                rel_s = f"{rel:.2f}" if rel is not None else '--'
                parts.append(f"{label}({add_s}/{rel_s})")
            else:
                if val is None:
                    continue
                parts.append(f"{label}({val:.2f})")
        return ' + '.join(parts)

    uls_combos = IRC6_2017.uls_load_combinations()
    sls_combos = IRC6_2017.sls_load_combinations()
    lc_rows = []
    for i, combo in enumerate(uls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(
            f"ULS-{i:02d} & {cases} \\\\[4pt]\n\\hline"
        )
    for i, combo in enumerate(sls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(
            f"SLS-{i:02d} & {cases} \\\\[4pt]\n\\hline"
        )

    # 1. Dead Load - Self Weight
    t31 = build_table_with_headers(
        col_spec=r"|L{5.5cm}|p{10.0cm}|",
        header_row=r"\textbf{Parameter} & \textbf{Design Value}",
        caption="Dead Load --- Self Weight",
        label="tab:dead-load-sw",
        body_rows=[
            f"\\textnormal{{Steel Self-Weight Applied}} & {_render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, ' kN/m\\textsuperscript{3}')} \\\\[5pt]\n\\hline",
            f"\\textnormal{{Concrete Deck Weight}} & {_render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, ' kN/m\\textsuperscript{3}')} \\\\[5pt]\n\\hline",
            f"\\textnormal{{Self-Weight Factor}} & {_render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR)} \\\\[5pt]\n\\hline"
        ]
    )

    # 2. Dead Load - Surfacing & SIDL
    t32 = build_table_with_headers(
        col_spec=r"|L{5.5cm}|p{10.0cm}|",
        header_row=r"\textbf{Parameter} & \textbf{Design Value}",
        caption="Superimposed Dead Load (SIDL / DW)",
        label="tab:sidl",
        body_rows=[
            f"\\textnormal{{Wearing Course Material \\& Thickness}} & {_render_value(input_dict, KEY_WC_MATERIAL)} $\\times$ {_render_value(input_dict, KEY_WC_THICKNESS)} \\\\[5pt]\n\\hline",
            f"\\textnormal{{Crash Barrier SIDL}} & {_render_value(input_dict, KEY_CB_LOAD)} kN/m per barrier \\\\[5pt]\n\\hline",
            f"\\textnormal{{Railing Load}} & {_render_value(input_dict, KEY_RL_LOAD_VALUE)} kN/m\\sdstar{{}} \\\\[5pt]\n\\hline"
        ]
    )

    # 3. Vehicle Live Loads (IRC 6)
    t33 = build_table_with_headers(
        col_spec=r"|L{5.5cm}|p{10.0cm}|",
        header_row=r"\textbf{Traffic Live Load Parameter} & \textbf{Specification / Value}",
        caption="Vehicle Live Loads (IRC 6:2017)",
        label="tab:vehicular-live-load",
        body_rows=[
            f"\\textnormal{{Vehicular Loading Models Considered}} & {_tex(vehicles_str)} \\\\[5pt]\n\\hline",
            f"\\textnormal{{Impact Factor (IRC 6 Cl. 208)}} & {_tex(impact_factor_str)} \\\\[5pt]\n\\hline",
            f"\\textnormal{{Longitudinal Braking Force (IRC 6 Cl. 211)}} & {_tex(braking_force_str)} \\\\[5pt]\n\\hline",
            f"\\textnormal{{Number of Design Traffic Lanes}} & {_render_value(input_dict, KEY_WC_LD_LANE_TABLE_COUNT)} lanes \\\\[5pt]\n\\hline"
        ]
    )

    # 4. Footpath & Pedestrian Live Loads (IRC 6 Cl. 206)
    t34 = build_table_with_headers(
        col_spec=r"|L{5.5cm}|p{10.0cm}|",
        header_row=r"\textbf{Pedestrian / Footpath Parameter} & \textbf{Design Value / Clause}",
        caption="Footpath and Pedestrian Live Loads (IRC 6:2017 Cl. 206)",
        label="tab:footpath-live-load",
        body_rows=[
            f"\\textnormal{{Footpath Provision}} & {_tex(fp_count)} \\\\[5pt]\n\\hline",
            f"\\textnormal{{Clear Footpath Width}} & {fp_width_str} \\\\[5pt]\n\\hline",
            f"\\textnormal{{Pedestrian Live Load Intensity}} & {fp_intensity} \\\\[5pt]\n\\hline",
            f"\\textnormal{{Governing Code Clause / Provision}} & {fp_rule} \\\\[5pt]\n\\hline"
        ]
    )

    # 5. Wind Load (WL)
    t35 = build_table_with_headers(
        col_spec=r"|L{5.5cm}|p{10.0cm}|",
        header_row=r"\textbf{Wind Parameter} & \textbf{Design Value}",
        caption="Wind Load (WL) --- per IRC 6:2017",
        label="tab:wind-load",
        body_rows=[
            f"\\textnormal{{Basic Wind Speed, $V_b$}} & {_render_value(input_dict, 'wind_speed', ' m/s')} [from Project Location] \\\\[5pt]\n\\hline",
            f"\\textnormal{{Terrain Type}} & {_render_value(input_dict, KEY_WL_TERRAIN_TYPE)} \\\\[5pt]\n\\hline",
            f"\\textnormal{{Average Exposed Height, $H$}} & {_render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, ' m')} \\\\[5pt]\n\\hline",
            f"\\textnormal{{Hourly Mean Wind Speed, $V_z$}} & {_render_value(input_dict, KEY_WL_HOURLY_MEAN_WIND, ' m/s')} \\\\[5pt]\n\\hline",
            f"\\textnormal{{Hourly Wind Pressure, $P_z$}} & {_render_value(input_dict, KEY_WL_HOURLY_WIND_PRESSURE, ' N/m\\textsuperscript{2}')} \\\\[5pt]\n\\hline",
            f"\\textnormal{{Transverse Wind Force}} & {_render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, ' kN')} \\\\[5pt]\n\\hline",
            f"\\textnormal{{Longitudinal Wind Force}} & {_render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, ' kN')} \\\\[5pt]\n\\hline",
            f"\\textnormal{{Vertical Wind Force}} & {_render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, ' kN')} \\\\[5pt]\n\\hline"
        ]
    )

    # 6. Earthquake Load (EL)
    t36 = build_table_with_headers(
        col_spec=r"|L{5.5cm}|p{10.0cm}|",
        header_row=r"\textbf{Seismic Parameter} & \textbf{Design Value}",
        caption="Earthquake Load (EL) --- per IRC 6:2017",
        label="tab:earthquake-load",
        body_rows=[
            f"\\textnormal{{Seismic Zone}} & {_render_value(input_dict, 'seismic_zone')} [from Project Location] \\\\[5pt]\n\\hline",
            f"\\textnormal{{Zone Factor, $Z$}} & {_render_value(input_dict, KEY_SL_ZONE_FACTOR)} \\\\[5pt]\n\\hline",
            f"\\textnormal{{Importance Factor, $I$}} & {_render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR)} \\\\[5pt]\n\\hline",
            f"\\textnormal{{Type of Soil}} & {_render_value(input_dict, KEY_SL_SOIL_TYPE)} \\\\[5pt]\n\\hline",
            f"\\textnormal{{Spectral Acceleration Coefficient, $S_a/g$}} & {_render_value(input_dict, KEY_SL_SPECTRAL_COEFF)} \\\\[5pt]\n\\hline",
            f"\\textnormal{{Horizontal Seismic Coefficient, $A_h$}} & {_render_value(input_dict, KEY_SL_HORIZONTAL_COEFF)} \\\\[5pt]\n\\hline",
            f"\\textnormal{{Vertical Seismic Coefficient, $A_v$}} & {_render_value(input_dict, KEY_SL_VERTICAL_COEFF)} \\\\[5pt]\n\\hline"
        ]
    )

    # 7. Temperature Load (TL)
    t37 = build_table_with_headers(
        col_spec=r"|L{5.5cm}|p{10.0cm}|",
        header_row=r"\textbf{Thermal Parameter} & \textbf{Design Value}",
        caption="Temperature Load (TL) --- per IRC 6:2017",
        label="tab:temperature-load",
        body_rows=[
            f"\\textnormal{{Maximum Shade Temperature}} & {_render_value(input_dict, 'shade_temp_max')} $^\\circ$C \\\\[5pt]\n\\hline",
            f"\\textnormal{{Minimum Shade Temperature}} & {_render_value(input_dict, 'shade_temp_min')} $^\\circ$C \\\\[5pt]\n\\hline",
            f"\\textnormal{{Effective Bridge Temp. Range}} & {_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN)} to {_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX)} $^\\circ$C \\\\[5pt]\n\\hline",
            f"\\textnormal{{Temperature Rise / Fall for Design}} & +{_render_value(input_dict, KEY_TL_TEMP_RISE)} $^\\circ$C / \\textminus{{}}{_render_value(input_dict, KEY_TL_TEMP_FALL)} $^\\circ$C \\\\[5pt]\n\\hline"
        ]
    )

    # 8. Load Combinations (ULS & SLS)
    t38 = build_table_with_headers(
        col_spec=r"|C{3.0cm}|p{12.5cm}|",
        header_row=r"\textbf{Combination ID} & \textbf{Load Cases and Partial Safety Factors}",
        caption="Design Load Combinations (IRC 6:2017 Table B.1 to B.4)",
        label="tab:load-combinations",
        continued_caption="Design Load Combinations (Continued)",
        body_rows=lc_rows
    )

    return f"""
\\chapter{{Loads and Load Combinations}}
\\label{{ch:loads-combinations}}

This chapter details all primary loads applied to the superstructure in accordance with IRC 6:2017 and IS 800:2007, along with the derived Ultimate Limit State (ULS) and Serviceability Limit State (SLS) combinations considered during the structural grillage analysis.

\\vspace{{0.5em}}
{t31}

\\vspace{{0.5em}}
{t32}

\\vspace{{0.5em}}
{t33}

\\vspace{{0.5em}}
{t34}

\\vspace{{0.5em}}
{t35}

\\vspace{{0.5em}}
{t36}

\\vspace{{0.5em}}
{t37}

\\vspace{{0.5em}}
{t38}

\\noindent\\textit{{Note: All standard IRC 6 load combinations are systematically generated by the OsdagBridge structural grillage engine. Any user-specified special vehicle or custom environmental load cases are compounded per code specifications.}}
"""
