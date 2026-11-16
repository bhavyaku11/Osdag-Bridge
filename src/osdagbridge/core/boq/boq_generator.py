# =============================================================================
# OsdagBridge — BOQ (Bill of Quantities) Generator
# =============================================================================

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_GIRDER_SPACING,
)

logger = logging.getLogger("osdagbridge.core.boq_generator")

# Standard Engineering Constants (IS 800 / IRC 112 / IS 456)
DEFAULT_CONCRETE_DENSITY_T_M3 = 2.5   # Reinforced / Plain concrete density: 2.5 t/m³ (25 kN/m³)
DEFAULT_REBAR_RATE_KG_M3 = 120.0       # Standard preliminary estimation rate: 120 kg/m³ of concrete
STEEL_DENSITY_KG_M3 = 7850.0          # Structural steel density: 7850 kg/m³ (7.85 t/m³)


def _parse_strict_positive_float(val: Any) -> Optional[float]:
    """
    Parses a strictly positive, finite float.
    Rejects: None, non-numeric types, NaN, inf, -inf, zero, and negative values.
    """
    if val is None:
        return None
    try:
        f = float(val)
        if not math.isfinite(f) or f <= 0.0:
            return None
        return f
    except (ValueError, TypeError):
        return None


def _parse_strict_positive_int(val: Any) -> Optional[int]:
    """
    Parses a strictly positive integer.
    Rejects: None, non-numeric types, NaN, inf, <= 0, and fractional floats (e.g. 4.8).
    """
    if val is None:
        return None
    try:
        f = float(val)
        if not math.isfinite(f) or f <= 0.0:
            return None
        if not f.is_integer():
            return None
        return int(f)
    except (ValueError, TypeError):
        return None


def has_per_girder_scheme(source: dict, base_key: str) -> bool:
    """Detects whether source defines per-girder keys (e.g. .G1.M1, .G1, etc.)."""
    if not isinstance(source, dict):
        return False
    prefix = f"{base_key}.G"
    return any(k.startswith(prefix) for k in source.keys())


def resolve_girder_value(source: dict, base_key: str, i: int = 0) -> Any:
    """
    Resolve a girder property from source dict for girder index i (0-based).
    
    Resolution Priority:
    1. Checks per-girder candidates for girder i: f"{base_key}.G{i + 1}.M1" or f"{base_key}.G{i + 1}".
    2. If per-girder keys are detected in the dataset but this specific girder G{i+1} is missing,
       raises KeyError rather than silently duplicating another girder's property.
    3. If no per-girder keys exist anywhere in the dataset, falls back to the legacy scalar base_key
       (valid for uniform bridge girder sections).
    """
    if not isinstance(source, dict):
        raise TypeError(f"Source must be a dict, got {type(source).__name__}")

    # 1. Exact candidates for Girder G{i+1}
    g_candidates = [
        f"{base_key}.G{i + 1}.M1",
        f"{base_key}.G{i + 1}",
    ]
    for key in g_candidates:
        if key in source and source[key] is not None:
            return source[key]

    # 2. Check if dataset uses per-girder scheme
    if has_per_girder_scheme(source, base_key):
        raise KeyError(
            f"Incomplete per-girder dataset: property '{base_key}' missing for girder G{i + 1}"
        )

    # 3. If per-girder scheme is NOT in use, allow global scalar key
    if base_key in source and source[base_key] is not None:
        return source[base_key]

    raise KeyError(f"Girder property '{base_key}' not found in input source")


def calculate_material_quantities(inputs: dict, outputs: dict) -> dict:
    """
    Calculate quantities (steel tonnage, concrete volume, rebar, studs)
    needed for the material take-off summary (Chapter 7).

    Guarantees:
    - Never silently duplicates G1 dimensions when a per-girder dataset has missing girders.
    - Strictly rejects non-physical inputs (NaN, infinity, fractional girder counts, negative values).
    - Checks mass per unit length against theoretical volume-density product ($m \approx A \times \rho$).
    - Captures all validation warnings in quantities['_warnings'].
    - Explicitly documents and parameterizes all density and rebar estimation assumptions.
    """
    warnings: List[str] = []

    quantities: Dict[str, Any] = {
        "steel_girders_vol_formula": r"\placeholder{Area $\times$ Length}",
        "steel_girders_qty": "N.A.",
        "steel_girders_vol_total": "N.A.",
        "steel_girders_wt_single": "N.A.",
        "steel_girders_wt_total": "N.A.",

        "steel_bracing_vol_formula": r"\placeholder{Area $\times$ Length}",
        "steel_bracing_qty": "N.A.",
        "steel_bracing_vol_total": "N.A.",
        "steel_bracing_wt_single": "N.A.",
        "steel_bracing_wt_total": "N.A.",

        "bracing_top_vol_formula": r"\placeholder{Area $\times$ Length}",
        "bracing_top_qty": "N.A.",
        "bracing_top_vol_total": "N.A.",
        "bracing_top_wt_single": "N.A.",
        "bracing_top_wt_total": "N.A.",

        "bracing_bot_vol_formula": r"\placeholder{Area $\times$ Length}",
        "bracing_bot_qty": "N.A.",
        "bracing_bot_vol_total": "N.A.",
        "bracing_bot_wt_single": "N.A.",
        "bracing_bot_wt_total": "N.A.",

        "bracing_diag_vol_formula": r"\placeholder{Area $\times$ Length}",
        "bracing_diag_qty": "N.A.",
        "bracing_diag_vol_total": "N.A.",
        "bracing_diag_wt_single": "N.A.",
        "bracing_diag_wt_total": "N.A.",

        "concrete_deck_vol_formula": r"\placeholder{Width $\times$ Thickness $\times$ Length}",
        "concrete_deck_qty": "N.A.",
        "concrete_deck_vol_total": "N.A.",
        "concrete_deck_wt_single": "N.A.",
        "concrete_deck_wt_total": "N.A.",

        "rebar_deck_vol_formula": r"\placeholder{Area $\times$ Length}",
        "rebar_deck_qty": "N.A.",
        "rebar_deck_vol_total": "N.A.",
        "rebar_deck_wt_single": "N.A.",
        "rebar_deck_wt_total": "N.A.",

        "shear_studs_vol_formula": r"\placeholder{Area $\times$ Height}",
        "shear_studs_qty": "N.A.",
        "shear_studs_vol_total": "N.A.",
        "shear_studs_wt_single": "N.A.",
        "shear_studs_wt_total": "N.A.",

        "crash_barrier_vol_formula": r"\placeholder{Area $\times$ Length}",
        "crash_barrier_qty": "N.A.",
        "crash_barrier_vol_total": "N.A.",
        "crash_barrier_wt_single": "N.A.",
        "crash_barrier_wt_total": "N.A.",

        "_warnings": warnings,
        "_assumptions": {}
    }

    if not isinstance(inputs, dict):
        warnings.append("Inputs is not a valid dictionary; calculation aborted.")
        return quantities

    outputs = outputs if isinstance(outputs, dict) else {}

    # Read configurable assumptions
    assumptions = inputs.get("design_options.material_assumptions", {})
    if not isinstance(assumptions, dict):
        assumptions = {}

    concrete_density_t_m3 = _parse_strict_positive_float(assumptions.get("concrete_density_t_m3")) or DEFAULT_CONCRETE_DENSITY_T_M3
    rebar_rate_kg_m3 = _parse_strict_positive_float(assumptions.get("rebar_rate_kg_m3")) or DEFAULT_REBAR_RATE_KG_M3
    steel_density_kg_m3 = _parse_strict_positive_float(assumptions.get("steel_density_kg_m3")) or STEEL_DENSITY_KG_M3

    quantities["_assumptions"] = {
        "concrete_density_t_m3": concrete_density_t_m3,
        "rebar_rate_kg_m3": rebar_rate_kg_m3,
        "steel_density_kg_m3": steel_density_kg_m3
    }

    try:
        span_raw = inputs.get(KEY_SPAN)
        if span_raw is None:
            span_raw = inputs.get("general.bridge_span") or inputs.get("span")
        n_girders_raw = inputs.get(KEY_TS_NO_OF_GIRDERS)
        if n_girders_raw is None:
            n_girders_raw = inputs.get("no_of_girders") or inputs.get("n_girders")

        if span_raw is None or n_girders_raw is None:
            warnings.append(f"Missing mandatory bridge geometry parameters: span={span_raw}, n_girders={n_girders_raw}")
            return quantities

        span = _parse_strict_positive_float(span_raw)
        if span is None:
            warnings.append(f"Bridge span must be a positive, finite number (got '{span_raw}')")
            return quantities

        n_girders = _parse_strict_positive_int(n_girders_raw)
        if n_girders is None:
            warnings.append(f"Girder count must be a positive integer (got '{n_girders_raw}')")
            return quantities

        # ─────────────────────────────────────────────────────────────────────
        # 1. Concrete Deck Volume (Cu.m) and Weight (MT)
        # ─────────────────────────────────────────────────────────────────────
        overall_width_val = inputs.get("typical_section.overall_bridge_width")
        deck_thickness_val = inputs.get(KEY_TS_DECK_THICKNESS)

        if overall_width_val is not None and deck_thickness_val is not None:
            overall_width = _parse_strict_positive_float(overall_width_val)
            deck_thickness_mm = _parse_strict_positive_float(deck_thickness_val)

            if overall_width and deck_thickness_mm:
                deck_thickness = deck_thickness_mm / 1000.0  # mm to m
                concrete_vol = span * overall_width * deck_thickness
                concrete_wt = concrete_vol * concrete_density_t_m3
                quantities["concrete_deck_vol_formula"] = (
                    f"${overall_width:.2f}\\text{{ m}} \\times {deck_thickness:.2f}\\text{{ m}} "
                    f"\\times {span:.2f}\\text{{ m}} = {concrete_vol:.2f}\\text{{ m}}^3$"
                )
                quantities["concrete_deck_qty"] = "1"
                quantities["concrete_deck_vol_total"] = f"{concrete_vol:.2f}"
                quantities["concrete_deck_wt_single"] = f"{concrete_wt:.2f}"
                quantities["concrete_deck_wt_total"] = f"{concrete_wt:.2f}"

                # 2. Reinforcement Steel (Estimated via design rate)
                rebar_wt_kg = concrete_vol * rebar_rate_kg_m3
                rebar_vol = rebar_wt_kg / steel_density_kg_m3
                rebar_area = rebar_vol / span if span > 0 else 0.0
                rebar_wt_mt = rebar_wt_kg / 1000.0

                quantities["rebar_deck_vol_formula"] = (
                    f"${rebar_area:.6f}\\text{{ m}}^2 \\times {span:.2f}\\text{{ m}} "
                    f"= {rebar_vol:.5f}\\text{{ m}}^3\\text{{ (est. @ {rebar_rate_kg_m3:.0f} kg/m}}^3\\text{{)}}$"
                )
                quantities["rebar_deck_qty"] = "1"
                quantities["rebar_deck_vol_total"] = f"{rebar_vol:.2f}"
                quantities["rebar_deck_wt_single"] = f"{rebar_wt_mt:.2f}"
                quantities["rebar_deck_wt_total"] = f"{rebar_wt_mt:.2f}"
            else:
                warnings.append(
                    f"Deck dimensions must be positive, finite numbers: overall_width='{overall_width_val}', deck_thickness='{deck_thickness_val}'"
                )

        # ─────────────────────────────────────────────────────────────────────
        # 3. Steel Girders (Cu.m) and Weight (MT) — Rigorous Per-Girder Resolution
        # ─────────────────────────────────────────────────────────────────────
        girder_errors: List[str] = []
        girder_areas: List[float] = []
        girder_masses: List[float] = []

        for gi in range(n_girders):
            g_area = None
            # Attempt 1: Direct section area property
            try:
                val = resolve_girder_value(inputs, "member_properties.girder_details.section_properties.area", gi)
                parsed_area = _parse_strict_positive_float(val)
                if parsed_area is not None:
                    g_area = parsed_area
                else:
                    girder_errors.append(f"Girder G{gi + 1}: sectional area must be a positive finite number (got '{val}')")
                    continue
            except KeyError as e:
                pass  # Fallback to computing from plate dimensions
            except (ValueError, TypeError) as e:
                girder_errors.append(f"Girder G{gi + 1}: invalid sectional area value ({e})")
                continue

            # Attempt 2: Compute from plate dimensions (web & flange plates)
            if g_area is None:
                try:
                    dw = _parse_strict_positive_float(resolve_girder_value(inputs, "member_properties.girder_details.section_input.web_depth", gi))
                    tw = _parse_strict_positive_float(resolve_girder_value(inputs, "member_properties.girder_details.section_input.web_thickness", gi))
                    bft = _parse_strict_positive_float(resolve_girder_value(inputs, "member_properties.girder_details.section_input.top_flange_width", gi))
                    tft = _parse_strict_positive_float(resolve_girder_value(inputs, "member_properties.girder_details.section_input.top_flange_thickness", gi))
                    bfb = _parse_strict_positive_float(resolve_girder_value(inputs, "member_properties.girder_details.section_input.bottom_flange_width", gi))
                    tfb = _parse_strict_positive_float(resolve_girder_value(inputs, "member_properties.girder_details.section_input.bottom_flange_thickness", gi))

                    if not (dw and tw and bft and tft and bfb and tfb):
                        girder_errors.append(f"Girder G{gi + 1}: non-positive or non-finite plate dimensions")
                        continue

                    g_area = ((dw * tw) + (bft * tft) + (bfb * tfb)) / 1e6  # mm² to m²
                except KeyError as e:
                    girder_errors.append(f"Girder G{gi + 1}: data missing ({e})")
                    continue
                except (ValueError, TypeError) as e:
                    girder_errors.append(f"Girder G{gi + 1}: invalid numeric plate dimensions ({e})")
                    continue

            girder_areas.append(g_area)

            # Resolve girder mass per meter and cross-check mass/volume consistency
            g_mass = None
            try:
                m_val = resolve_girder_value(inputs, "member_properties.girder_details.section_properties.mass", gi)
                parsed_m = _parse_strict_positive_float(m_val)
                if parsed_m is not None:
                    # Mass consistency check: m_expected = A * rho
                    expected_m = g_area * steel_density_kg_m3
                    discrepancy = abs(parsed_m - expected_m) / expected_m
                    if discrepancy > 0.15:
                        warnings.append(
                            f"Girder G{gi + 1}: provided mass ({parsed_m:.2f} kg/m) deviates by {discrepancy * 100:.1f}% "
                            f"from theoretical mass ({expected_m:.2f} kg/m = area {g_area:.4f} m² × density {steel_density_kg_m3:.1f} kg/m³)."
                        )
                    g_mass = parsed_m
            except Exception:
                pass

            if g_mass is None:
                # Density calculation: Area (m²) * steel density (kg/m³)
                g_mass = g_area * steel_density_kg_m3

            girder_masses.append(g_mass)

        if girder_errors:
            # An incomplete or missing girder must NEVER be silently filled with G1 dimensions!
            err_summary = "; ".join(girder_errors)
            warnings.append(f"Girder BOQ calculation incomplete: {err_summary}")
            quantities["steel_girders_vol_formula"] = r"\text{Incomplete Girder Input}"
            quantities["steel_girders_qty"] = str(n_girders)
            quantities["steel_girders_vol_total"] = "N.A."
            quantities["steel_girders_wt_single"] = "N.A."
            quantities["steel_girders_wt_total"] = "N.A."
        elif len(girder_areas) == n_girders:
            total_g_vol = sum(a * span for a in girder_areas)
            total_g_wt_kg = sum(m * span for m in girder_masses)
            total_g_wt_mt = total_g_wt_kg / 1000.0
            avg_wt_mt = total_g_wt_mt / n_girders if n_girders > 0 else 0.0

            all_same = (max(girder_areas) - min(girder_areas)) < 1e-6
            if all_same:
                single_area = girder_areas[0]
                quantities["steel_girders_vol_formula"] = (
                    f"${single_area:.4f}\\text{{ m}}^2 \\times {span:.2f}\\text{{ m}} = {single_area * span:.2f}\\text{{ m}}^3$"
                )
            else:
                area_parts = " + ".join([f"{a:.4f}" for a in girder_areas])
                quantities["steel_girders_vol_formula"] = (
                    f"$({area_parts})\\text{{ m}}^2 \\times {span:.2f}\\text{{ m}} = {total_g_vol:.2f}\\text{{ m}}^3$"
                )

            quantities["steel_girders_qty"] = str(n_girders)
            quantities["steel_girders_vol_total"] = f"{total_g_vol:.2f}"
            quantities["steel_girders_wt_single"] = f"{avg_wt_mt:.2f}"
            quantities["steel_girders_wt_total"] = f"{total_g_wt_mt:.2f}"

        # ─────────────────────────────────────────────────────────────────────
        # 4. Shear Stud Connectors (Cu.m) and Weight (MT)
        # ─────────────────────────────────────────────────────────────────────
        spacing_val = outputs.get("steeldesign.details.shear.longitudinal_spacing")
        studs_val = outputs.get("steeldesign.details.shear.studs_per_section")
        stud_d_val = outputs.get("steeldesign.details.shear.diameter") or inputs.get("design_options.shear_studs.diameter")
        stud_h_val = outputs.get("steeldesign.details.shear.height") or inputs.get("design_options.shear_studs.height")

        if spacing_val is not None and studs_val is not None and stud_d_val is not None and stud_h_val is not None:
            spacing_mm = _parse_strict_positive_float(spacing_val)
            studs_per_sec = _parse_strict_positive_int(studs_val)
            stud_d = _parse_strict_positive_float(stud_d_val)
            stud_h_mm = _parse_strict_positive_float(stud_h_val)

            if spacing_mm and studs_per_sec and stud_d and stud_h_mm:
                stud_h = stud_h_mm / 1000.0
                n_sections = int(span * 1000.0 / spacing_mm) + 1
                total_studs = n_girders * studs_per_sec * n_sections

                stud_area = (math.pi * (stud_d / 1000.0) ** 2) / 4.0
                stud_vol = stud_area * stud_h
                studs_total_vol = total_studs * stud_vol

                steel_density_t = steel_density_kg_m3 / 1000.0
                single_stud_wt = stud_vol * steel_density_t
                total_studs_wt = studs_total_vol * steel_density_t

                quantities["shear_studs_vol_formula"] = (
                    f"${stud_area:.6f}\\text{{ m}}^2 \\times {stud_h:.3f}\\text{{ m}} = {stud_vol:.6f}\\text{{ m}}^3$"
                )
                quantities["shear_studs_qty"] = str(total_studs)
                quantities["shear_studs_vol_total"] = f"{studs_total_vol:.2f}"
                quantities["shear_studs_wt_single"] = f"{single_stud_wt:.6f}"
                quantities["shear_studs_wt_total"] = f"{total_studs_wt:.3f}"
            else:
                warnings.append(f"Invalid numeric values for shear stud geometry: spacing={spacing_val}, studs={studs_val}")

        # ─────────────────────────────────────────────────────────────────────
        # 5. Steel Bracings (Cu.m) and Weight (MT)
        # ─────────────────────────────────────────────────────────────────────
        bracing_area_val = outputs.get("transverse_member_design.cb.section_properties.bracing.G1G2.A")
        cb_forces = outputs.get("crossbracing_forces_dict")
        bracing_len_val = None
        cb_spacing_val = None
        if isinstance(cb_forces, dict):
            cb_geom = cb_forces.get("geometry", {})
            if isinstance(cb_geom, dict):
                bracing_len_val = cb_geom.get("diagonal_length_m")
                cb_spacing_val = cb_geom.get("cb_spacing_m")

        spacing_val = inputs.get(KEY_TS_GIRDER_SPACING)

        if bracing_area_val is not None and bracing_len_val is not None and spacing_val is not None:
            bracing_area_cm2 = _parse_strict_positive_float(bracing_area_val)
            bracing_len = _parse_strict_positive_float(bracing_len_val)
            spacing = _parse_strict_positive_float(spacing_val)

            if bracing_area_cm2 and bracing_len and spacing:
                bracing_area = bracing_area_cm2 / 10000.0  # cm² to m²
                cb_spacing = _parse_strict_positive_float(cb_spacing_val) or 0.0
                n_panels = max(1, round(span / cb_spacing) - 1) if cb_spacing > 0.0 else max(3, int(span / 5.0))

                steel_density_t = steel_density_kg_m3 / 1000.0

                # 5a. Top Chord
                top_chord_qty = (n_girders - 1) * n_panels
                top_chord_vol_single = bracing_area * spacing
                top_chord_vol_total = top_chord_qty * top_chord_vol_single
                top_chord_wt_single = top_chord_vol_single * steel_density_t
                top_chord_wt_total = top_chord_vol_total * steel_density_t

                quantities["bracing_top_vol_formula"] = (
                    f"${bracing_area:.5f}\\text{{ m}}^2 \\times {spacing:.2f}\\text{{ m}} = {top_chord_vol_single:.5f}\\text{{ m}}^3$"
                )
                quantities["bracing_top_qty"] = str(top_chord_qty)
                quantities["bracing_top_vol_total"] = f"{top_chord_vol_total:.2f}"
                quantities["bracing_top_wt_single"] = f"{top_chord_wt_single:.4f}"
                quantities["bracing_top_wt_total"] = f"{top_chord_wt_total:.2f}"

                # 5b. Bottom Chord
                bot_chord_qty = (n_girders - 1) * n_panels
                bot_chord_vol_single = bracing_area * spacing
                bot_chord_vol_total = bot_chord_qty * bot_chord_vol_single
                bot_chord_wt_single = bot_chord_vol_single * steel_density_t
                bot_chord_wt_total = bot_chord_vol_total * steel_density_t

                quantities["bracing_bot_vol_formula"] = (
                    f"${bracing_area:.5f}\\text{{ m}}^2 \\times {spacing:.2f}\\text{{ m}} = {bot_chord_vol_single:.5f}\\text{{ m}}^3$"
                )
                quantities["bracing_bot_qty"] = str(bot_chord_qty)
                quantities["bracing_bot_vol_total"] = f"{bot_chord_vol_total:.2f}"
                quantities["bracing_bot_wt_single"] = f"{bot_chord_wt_single:.4f}"
                quantities["bracing_bot_wt_total"] = f"{bot_chord_wt_total:.2f}"

                # 5c. Diagonal
                diags_qty = (n_girders - 1) * n_panels * 2
                diag_vol_single = bracing_area * bracing_len
                diag_vol_total = diags_qty * diag_vol_single
                diag_wt_single = diag_vol_single * steel_density_t
                diag_wt_total = diag_vol_total * steel_density_t

                quantities["bracing_diag_vol_formula"] = (
                    f"${bracing_area:.5f}\\text{{ m}}^2 \\times {bracing_len:.2f}\\text{{ m}} = {diag_vol_single:.5f}\\text{{ m}}^3$"
                )
                quantities["bracing_diag_qty"] = str(diags_qty)
                quantities["bracing_diag_vol_total"] = f"{diag_vol_total:.2f}"
                quantities["bracing_diag_wt_single"] = f"{diag_wt_single:.4f}"
                quantities["bracing_diag_wt_total"] = f"{diag_wt_total:.2f}"

        # ─────────────────────────────────────────────────────────────────────
        # 6. Crash Barrier (Cu.m) and Weight (MT)
        # ─────────────────────────────────────────────────────────────────────
        cb_area_val = inputs.get("typical_section.crash_barrier.area")
        if cb_area_val is not None:
            cb_area_mm2 = _parse_strict_positive_float(cb_area_val)
            if cb_area_mm2:
                cb_area = cb_area_mm2 / 1e6  # mm² to m²
                cb_vol = cb_area * span
                cb_total_vol = 2 * cb_vol
                single_cb_wt = cb_vol * concrete_density_t_m3
                total_cb_wt = cb_total_vol * concrete_density_t_m3

                quantities["crash_barrier_vol_formula"] = (
                    f"${cb_area:.5f}\\text{{ m}}^2 \\times {span:.2f}\\text{{ m}} = {cb_vol:.5f}\\text{{ m}}^3$"
                )
                quantities["crash_barrier_qty"] = "2"
                quantities["crash_barrier_vol_total"] = f"{cb_total_vol:.2f}"
                quantities["crash_barrier_wt_single"] = f"{single_cb_wt:.2f}"
                quantities["crash_barrier_wt_total"] = f"{total_cb_wt:.2f}"
            else:
                warnings.append(f"Crash barrier area must be a positive finite number (got '{cb_area_val}')")

    except Exception as exc:
        logger.error("BOQ generation failed: %s", exc, exc_info=True)
        warnings.append(f"BOQ generator encountered unexpected error: {exc}")

    return quantities
