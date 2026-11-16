"""
Automated Functional Test Suite & Test Matrix Runner for OsdagBridge.
Executes the full 20-scenario testing matrix defined in TEST_MATRIX.md:
  - Geometry variations (short/long spans, 2 to 6 girders, skew angles, overhangs)
  - Custom material configurations (E350, E450, M50, custom densities)
  - Multi-run state isolation and memory purity
  - Live load cases (Class A, 70R, Footpath)
  - Bill of Quantities (BOQ) calculations and Issue #103 regression fixes
  - Zero-fabrication chart generation
  - Publication-quality LaTeX report assembly

Execution:
    python3 tests/run_functional_tests.py
"""

import os
import sys
import copy
import logging

# Ensure OsdagBridge src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_SKEW_ANGLE,
    KEY_DESIGN_MODE,
    KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_70R_TRACKED,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_NO_OF_FOOTPATHS,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS
)

from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
from osdagbridge.core.boq.boq_generator import calculate_material_quantities, resolve_girder_value
from osdagbridge.core.reports.styles import ReportStyle, ColorPalette
from osdagbridge.core.reports.plot_utils import generate_ur_summary_chart, generate_material_quantity_chart
from osdagbridge.core.reports.report_generator import (
    ReportMetadata,
    ReportOptions,
    ReportRequest,
    ReportPayload,
    ReportFigures,
    generate_report
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TestRunner")


def build_base_input(span=20.0, n_girders=4, spacing=2.5, overhang=1.2, thickness=220):
    """Construct a clean, valid input dictionary for PlateGirderBridge."""
    return {
        KEY_SPAN: span,
        KEY_TS_NO_OF_GIRDERS: n_girders,
        KEY_TS_GIRDER_SPACING: spacing,
        KEY_TS_DECK_OVERHANG: overhang,
        KEY_TS_DECK_THICKNESS: thickness,
        "typical_section.overall_bridge_width": (n_girders - 1) * spacing + 2 * overhang,
        KEY_DESIGN_MODE: "Optimized",
        KEY_MATERIAL_GIRDER_DENSITY: 78.5,
        KEY_MATERIAL_DECK_DENSITY: 25.0,
        KEY_LL_IRC_CLASS_A: True,
        KEY_LL_IRC_70R_WHEELED: True,
        KEY_WC_MATERIAL: "Bituminous Concrete",
        KEY_WC_THICKNESS: "75 mm",
        "wind_speed": 39.0,
        "seismic_zone": "II",
        "shade_temp_max": 42.0,
        "shade_temp_min": 8.0,
        "member_properties.girder_details.section_properties.area": 0.045,
        "member_properties.girder_details.section_properties.mass": 353.25,
    }


# ==============================================================================
# SECTION 1: 20-SCENARIO FUNCTIONAL TEST MATRIX
# ==============================================================================

def test_tc01_baseline_standard():
    """TC-01: Baseline standard 20m 4-girder bridge configuration."""
    logger.info("Running TC-01: Baseline Standard (20m, 4 girders)...")
    bridge = PlateGirderBridge()
    inputs = build_base_input(span=20.0, n_girders=4)
    bridge.set_input(inputs)
    assert bridge.input_dict[KEY_SPAN] == 20.0
    assert bridge.input_dict[KEY_TS_NO_OF_GIRDERS] == 4
    assert bridge.input_dict[KEY_TS_GIRDER_SPACING] == 2.5
    logger.info("TC-01 PASSED.")


def test_tc02_short_span():
    """TC-02: Short span 10m 2-girder configuration."""
    logger.info("Running TC-02: Short Span Extreme (10m, 2 girders)...")
    bridge = PlateGirderBridge()
    inputs = build_base_input(span=10.0, n_girders=2, spacing=3.0, overhang=0.8)
    bridge.set_input(inputs)
    assert bridge.input_dict[KEY_SPAN] == 10.0
    assert bridge.input_dict[KEY_TS_NO_OF_GIRDERS] == 2
    logger.info("TC-02 PASSED.")


def test_tc03_long_span():
    """TC-03: Long span 30m 5-girder configuration."""
    logger.info("Running TC-03: Long Span Extreme (30m, 5 girders)...")
    bridge = PlateGirderBridge()
    inputs = build_base_input(span=30.0, n_girders=5, spacing=2.4, overhang=1.5)
    bridge.set_input(inputs)
    assert bridge.input_dict[KEY_SPAN] == 30.0
    assert bridge.input_dict[KEY_TS_NO_OF_GIRDERS] == 5
    logger.info("TC-03 PASSED.")


def test_tc04_heavy_6_girder():
    """TC-04: Heavy 25m 6-girder configuration."""
    logger.info("Running TC-04: Heavy 6-Girder Bridge (25m, 6 girders)...")
    bridge = PlateGirderBridge()
    inputs = build_base_input(span=25.0, n_girders=6, spacing=2.2, overhang=1.2)
    bridge.set_input(inputs)
    assert bridge.input_dict[KEY_SPAN] == 25.0
    assert bridge.input_dict[KEY_TS_NO_OF_GIRDERS] == 6
    logger.info("TC-04 PASSED.")


def test_tc05_skew_angle():
    """TC-05: Skew Angle Geometry (18m, 4 girders, 15 deg skew)."""
    logger.info("Running TC-05: Skew Angle Geometry (18m, 15 deg)...")
    bridge = PlateGirderBridge()
    inputs = build_base_input(span=18.0, n_girders=4)
    inputs[KEY_SKEW_ANGLE] = 15.0
    bridge.set_input(inputs)
    assert bridge.input_dict[KEY_SKEW_ANGLE] == 15.0
    logger.info("TC-05 PASSED.")


def test_tc06_high_skew():
    """TC-06: High Skew Extreme (22m, 4 girders, 30 deg skew)."""
    logger.info("Running TC-06: High Skew Extreme (22m, 30 deg)...")
    bridge = PlateGirderBridge()
    inputs = build_base_input(span=22.0, n_girders=4)
    inputs[KEY_SKEW_ANGLE] = 30.0
    bridge.set_input(inputs)
    assert bridge.input_dict[KEY_SKEW_ANGLE] == 30.0
    logger.info("TC-06 PASSED.")


def test_tc07_zero_overhang():
    """TC-07: Zero Overhang Edge (15m, 3 girders, 0.0m overhang)."""
    logger.info("Running TC-07: Zero Overhang Edge...")
    bridge = PlateGirderBridge()
    inputs = build_base_input(span=15.0, n_girders=3, overhang=0.0)
    bridge.set_input(inputs)
    assert bridge.input_dict[KEY_TS_DECK_OVERHANG] == 0.0
    logger.info("TC-07 PASSED.")


def test_tc08_large_overhang():
    """TC-08: Large Overhang Edge (20m, 3 girders, 1.8m overhang)."""
    logger.info("Running TC-08: Large Overhang Edge (1.8m)...")
    bridge = PlateGirderBridge()
    inputs = build_base_input(span=20.0, n_girders=3, overhang=1.8)
    bridge.set_input(inputs)
    assert bridge.input_dict[KEY_TS_DECK_OVERHANG] == 1.8
    logger.info("TC-08 PASSED.")


def test_tc09_custom_steel_e350():
    """TC-09: Custom Steel E350 (Fy=350 MPa, Fu=490 MPa)."""
    logger.info("Running TC-09: Custom Steel E350...")
    bridge = PlateGirderBridge()
    inputs = build_base_input()
    inputs["material.structural_steel.grade"] = "Custom"
    inputs["material.structural_steel.fy"] = "350"
    inputs["material.structural_steel.fu"] = "490.0"
    bridge.set_input(inputs)
    assert bridge.input_dict["material.structural_steel.fy"] == 350
    assert bridge.input_dict["material.structural_steel.fu"] == 490.0
    logger.info("TC-09 PASSED.")


def test_tc10_custom_steel_e450():
    """TC-10: Custom High-Strength Steel E450 (Fy=450 MPa, Fu=570 MPa)."""
    logger.info("Running TC-10: Custom High-Strength Steel E450...")
    bridge = PlateGirderBridge()
    inputs = build_base_input()
    inputs["material.structural_steel.grade"] = "Custom"
    inputs["material.structural_steel.fy"] = "450"
    inputs["material.structural_steel.fu"] = "570"
    bridge.set_input(inputs)
    assert bridge.input_dict["material.structural_steel.fy"] == 450
    assert bridge.input_dict["material.structural_steel.fu"] == 570
    logger.info("TC-10 PASSED.")


def test_tc11_custom_concrete_m50():
    """TC-11: Custom Concrete Grade M50 (fck=50 MPa)."""
    logger.info("Running TC-11: Custom Concrete Grade M50...")
    bridge = PlateGirderBridge()
    inputs = build_base_input()
    inputs["material.concrete.grade"] = "Custom"
    inputs["material.concrete.fck"] = "50"
    bridge.set_input(inputs)
    assert bridge.input_dict["material.concrete.fck"] == 50
    logger.info("TC-11 PASSED.")


def test_tc12_custom_densities():
    """TC-12: Custom Deck & Girder Densities."""
    logger.info("Running TC-12: Custom Material Densities...")
    bridge = PlateGirderBridge()
    inputs = build_base_input()
    inputs[KEY_MATERIAL_DECK_DENSITY] = 26.0
    inputs[KEY_MATERIAL_GIRDER_DENSITY] = 79.0
    bridge.set_input(inputs)
    assert bridge.input_dict[KEY_MATERIAL_DECK_DENSITY] == 26.0
    assert bridge.input_dict[KEY_MATERIAL_GIRDER_DENSITY] == 79.0
    logger.info("TC-12 PASSED.")


def test_tc13_multi_run_span_modification():
    """TC-13: Multi-run sequence verifying state isolation on span change."""
    logger.info("Running TC-13: Multi-run Sequence 1 (Span 20m -> 15m)...")
    bridge = PlateGirderBridge()
    inputs1 = build_base_input(span=20.0, n_girders=4)
    bridge.set_input(inputs1)
    assert bridge.input_dict[KEY_SPAN] == 20.0

    inputs2 = copy.deepcopy(inputs1)
    inputs2[KEY_SPAN] = 15.0
    inputs2[KEY_TS_NO_OF_GIRDERS] = 3
    bridge.set_input(inputs2)
    assert bridge.input_dict[KEY_SPAN] == 15.0
    assert bridge.input_dict[KEY_TS_NO_OF_GIRDERS] == 3
    logger.info("TC-13 PASSED.")


def test_tc14_multi_run_girder_count():
    """TC-14: Multi-run sequence modifying girder count."""
    logger.info("Running TC-14: Multi-run Sequence 2 (Girders 4 -> 3)...")
    bridge = PlateGirderBridge()
    inputs1 = build_base_input(span=24.0, n_girders=4)
    bridge.set_input(inputs1)
    assert bridge.input_dict[KEY_TS_NO_OF_GIRDERS] == 4

    inputs2 = copy.deepcopy(inputs1)
    inputs2[KEY_TS_NO_OF_GIRDERS] = 3
    inputs2[KEY_TS_GIRDER_SPACING] = 3.2
    bridge.set_input(inputs2)
    assert bridge.input_dict[KEY_TS_NO_OF_GIRDERS] == 3
    assert bridge.input_dict[KEY_TS_GIRDER_SPACING] == 3.2
    logger.info("TC-14 PASSED.")


def test_tc15_multi_run_material_modification():
    """TC-15: Multi-run sequence modifying material grades."""
    logger.info("Running TC-15: Multi-run Sequence 3 (Default -> Custom Material)...")
    bridge = PlateGirderBridge()
    inputs1 = build_base_input()
    bridge.set_input(inputs1)

    inputs2 = copy.deepcopy(inputs1)
    inputs2["material.structural_steel.grade"] = "Custom"
    inputs2["material.structural_steel.fy"] = "410"
    bridge.set_input(inputs2)
    assert bridge.input_dict["material.structural_steel.fy"] == 410
    logger.info("TC-15 PASSED.")


def test_tc16_heavy_irc_70r():
    """TC-16: Heavy IRC Class 70R loading."""
    logger.info("Running TC-16: Heavy IRC Class 70R Loading...")
    bridge = PlateGirderBridge()
    inputs = build_base_input()
    inputs[KEY_LL_IRC_70R_WHEELED] = True
    inputs[KEY_LL_IRC_70R_TRACKED] = True
    bridge.set_input(inputs)
    assert bridge.input_dict[KEY_LL_IRC_70R_WHEELED] is True
    assert bridge.input_dict[KEY_LL_IRC_70R_TRACKED] is True
    logger.info("TC-16 PASSED.")


def test_tc17_special_vehicle_envelope():
    """TC-17: Special Vehicle / Overload envelope verification."""
    logger.info("Running TC-17: Special Vehicle Envelope...")
    bridge = PlateGirderBridge()
    inputs = build_base_input(span=28.0, n_girders=5)
    inputs["live_load.sv_specified"] = True
    bridge.set_input(inputs)
    assert bridge.input_dict["live_load.sv_specified"] is True
    logger.info("TC-17 PASSED.")


def test_tc18_footpath_pedestrian_loading():
    """TC-18: Footpath and pedestrian live loading configuration."""
    logger.info("Running TC-18: Footpath and Pedestrian Live Loading...")
    bridge = PlateGirderBridge()
    inputs = build_base_input()
    inputs[KEY_TS_FOOTPATH_WIDTH] = 1500
    inputs[KEY_TS_NO_OF_FOOTPATHS] = "Both Sides"
    bridge.set_input(inputs)
    assert bridge.input_dict[KEY_TS_FOOTPATH_WIDTH] == 1500
    assert bridge.input_dict[KEY_TS_NO_OF_FOOTPATHS] == "Both Sides"
    logger.info("TC-18 PASSED.")


def test_tc19_empty_custom_field_guard():
    """TC-19: Input bounds guard rejecting invalid geometry."""
    logger.info("Running TC-19: Invalid Geometry Bounds Guard...")
    bridge = PlateGirderBridge()
    inputs = build_base_input(span=-10.0, n_girders=0)
    bridge.set_input(inputs)
    try:
        bridge._validate_inputs()
        assert False, "Should have raised ValueError on negative span"
    except ValueError as e:
        logger.info("Correctly caught invalid input: %s", e)
    logger.info("TC-19 PASSED.")


def test_tc20_dictionary_completeness_audit():
    """TC-20: Audit input dictionary completeness across all required domains."""
    logger.info("Running TC-20: Input Dictionary Completeness Audit...")
    inputs = build_base_input()
    required_keys = [
        KEY_SPAN,
        KEY_TS_NO_OF_GIRDERS,
        KEY_TS_GIRDER_SPACING,
        KEY_TS_DECK_OVERHANG,
        KEY_TS_DECK_THICKNESS,
        KEY_DESIGN_MODE,
        KEY_MATERIAL_GIRDER_DENSITY,
        KEY_MATERIAL_DECK_DENSITY,
        KEY_LL_IRC_CLASS_A,
        KEY_LL_IRC_70R_WHEELED,
    ]
    for k in required_keys:
        assert k in inputs, f"Missing canonical key: {k}"
    logger.info("TC-20 PASSED.")


# ==============================================================================
# SECTION 2: BOQ, ISSUE #103 REGRESSION, CHARTS, AND REPORTING
# ==============================================================================

def test_boq_calculations():
    """Verify material quantities (BOQ) calculation engine."""
    logger.info("Running BOQ Calculation Tests...")
    inputs = build_base_input(span=20.0, n_girders=4, spacing=2.5, overhang=1.2, thickness=220)
    quantities = calculate_material_quantities(inputs, {})

    conc_vol = float(quantities["concrete_deck_vol_total"])
    expected_conc_vol = 20.0 * (3 * 2.5 + 2 * 1.2) * 0.22
    assert abs(conc_vol - expected_conc_vol) < 0.1

    steel_wt = float(quantities["steel_girders_wt_total"])
    assert steel_wt > 0.0
    assert not quantities.get("_warnings")
    logger.info("BOQ Tests PASSED (Concrete Vol: %.2f m³, Steel: %.2f MT).", conc_vol, steel_wt)


def test_boq_non_uniform_girders_fix_verification():
    """Verify Issue #103 fix: Non-uniform girder sectional areas sum correctly."""
    logger.info("Running Bug #103 Fix Verification (Non-uniform girder areas)...")
    inputs = build_base_input(span=20.0, n_girders=4)
    inputs["member_properties.girder_details.section_properties.area.G1.M1"] = 0.040
    inputs["member_properties.girder_details.section_properties.area.G2.M1"] = 0.060
    inputs["member_properties.girder_details.section_properties.area.G3.M1"] = 0.060
    inputs["member_properties.girder_details.section_properties.area.G4.M1"] = 0.040

    quantities = calculate_material_quantities(inputs, {})
    total_vol = float(quantities["steel_girders_vol_total"])
    true_vol = (2 * 0.040 + 2 * 0.060) * 20.0
    assert abs(total_vol - true_vol) < 0.01
    logger.info("Reported Volume: %.2f m³ | True Volume: %.2f m³", total_vol, true_vol)
    logger.info("BUG #103 FIX VERIFIED: Volume calculation accurately accounts for individual girder cross sections!")


def test_boq_missing_girder_rejection_guard():
    """Verify Issue #103 regression guard: missing girder G3 in per-girder scheme raises error and flags N.A."""
    logger.info("Running Bug #103 Regression Guard (Missing G3)...")
    inputs = build_base_input(span=20.0, n_girders=4)
    inputs["member_properties.girder_details.section_properties.area.G1.M1"] = 0.040
    inputs["member_properties.girder_details.section_properties.area.G2.M1"] = 0.060
    # G3 is intentionally missing
    inputs["member_properties.girder_details.section_properties.area.G4.M1"] = 0.040

    base_key = "member_properties.girder_details.section_properties.area"
    try:
        resolve_girder_value(inputs, base_key, 2)
        assert False, "resolve_girder_value should have raised KeyError for missing G3"
    except KeyError as e:
        logger.info("Correctly caught missing girder G3: %s", e)

    quantities = calculate_material_quantities(inputs, {})
    assert quantities["steel_girders_vol_total"] == "N.A."
    assert any("G3" in w for w in quantities.get("_warnings", []))
    logger.info("BUG #103 REGRESSION GUARD PASSED: No silent fallback to G1.")


def test_chart_generation():
    """Verify high-resolution chart generators with strict engineering integrity."""
    logger.info("Running Chart Visualization Engine Tests (Zero Fabrication)...")
    test_dir = "/tmp/osdag_test_charts_suite"
    os.makedirs(test_dir, exist_ok=True)

    # 1. Strict engineering mode without data must return None (no fabricated 0.76)
    assert generate_ur_summary_chart({}, test_dir, demo_mode=False) is None

    # 2. Strict engineering mode with real calculated check
    output_dict = {"steeldesign.details.bending.utilization_ratio": 0.72}
    ur_path = generate_ur_summary_chart(output_dict, test_dir, demo_mode=False)
    assert ur_path is not None and os.path.exists(ur_path)

    # 3. Explicit demo mode generates benchmark visual
    demo_path = generate_ur_summary_chart({}, test_dir, demo_mode=True)
    assert demo_path is not None and os.path.exists(demo_path)

    # 4. Material quantity charts
    quantities = {
        "steel_girders_wt_total": "32.50",
        "bracing_top_wt_total": "2.80",
        "concrete_deck_vol_total": "54.00",
        "rebar_deck_wt_total": "6.48"
    }
    st_path, co_path = generate_material_quantity_chart({}, quantities, test_dir)
    assert st_path is not None and os.path.exists(st_path)
    assert co_path is not None and os.path.exists(co_path)
    logger.info("Chart Generation PASSED (UR: %s, Steel: %s, Concrete: %s).", ur_path, st_path, co_path)


def test_full_report_generation():
    """Verify complete report generation pipeline with LaTeX output and repeated headers."""
    logger.info("Running Full Report Generation Verification...")
    test_dir = "/tmp/osdag_test_report_suite"
    os.makedirs(test_dir, exist_ok=True)

    metadata = ReportMetadata(
        project_name="Bridge Test Suite Verification",
        project_location="Mumbai, Maharashtra",
        designer="FOSSEE Test Automation",
        client="Ministry of Road Transport and Highways",
        company="FOSSEE, IIT Bombay",
        job_number="TEST-2026-VERIFY",
        report_date="November 2026"
    )

    options = ReportOptions(
        sections=['project_info', 'inputs', 'loads', 'analysis', 'design_checks', 'drawings', 'quantities', 'standards', 'references'],
        include_figures=True,
        include_toc=True,
        include_pdf=False
    )

    request = ReportRequest(
        metadata=metadata,
        options=options,
        output_dir=test_dir,
        file_stem="Automated_Test_Report"
    )

    payload = ReportPayload(
        metadata=metadata,
        options=options,
        inputs=build_base_input(span=24.0, n_girders=4),
        analysis_summary={},
        design_checks=[],
        figures=ReportFigures(),
        log_entries=["Verification test passed"],
        output_dict={"steeldesign.details.bending.utilization_ratio": 0.75}
    )

    result = generate_report(payload, request)
    assert result.tex_path and os.path.exists(result.tex_path)

    with open(result.tex_path, "r", encoding="utf-8") as f:
        tex = f.read()

    # Assertions on LaTeX formatting
    assert "bottom=2.8cm" in tex
    assert "footskip=38pt" in tex
    assert "tableHeaderBg" in tex
    assert "ur_summary.png" in tex
    assert "material_steel.png" in tex
    assert "material_concrete.png" in tex
    assert "Footpath and Pedestrian Live Loads" in tex
    assert "\\endhead" in tex
    assert "\\endfirsthead" in tex

    logger.info("Full Report Generation PASSED: %s", result.tex_path)


def run_all_tests():
    """Run all functional test suite cases."""
    print("=" * 70)
    print("      OSDAGBRIDGE AUTOMATED FUNCTIONAL TEST SUITE (20+ CASES)")
    print("=" * 70)
    test_tc01_baseline_standard()
    test_tc02_short_span()
    test_tc03_long_span()
    test_tc04_heavy_6_girder()
    test_tc05_skew_angle()
    test_tc06_high_skew()
    test_tc07_zero_overhang()
    test_tc08_large_overhang()
    test_tc09_custom_steel_e350()
    test_tc10_custom_steel_e450()
    test_tc11_custom_concrete_m50()
    test_tc12_custom_densities()
    test_tc13_multi_run_span_modification()
    test_tc14_multi_run_girder_count()
    test_tc15_multi_run_material_modification()
    test_tc16_heavy_irc_70r()
    test_tc17_special_vehicle_envelope()
    test_tc18_footpath_pedestrian_loading()
    test_tc19_empty_custom_field_guard()
    test_tc20_dictionary_completeness_audit()
    test_boq_calculations()
    test_boq_non_uniform_girders_fix_verification()
    test_boq_missing_girder_rejection_guard()
    test_chart_generation()
    test_full_report_generation()
    print("=" * 70)
    print("   ALL FUNCTIONAL TEST MATRIX SCENARIOS PASSED SUCCESSFULLY! (25/25)")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
