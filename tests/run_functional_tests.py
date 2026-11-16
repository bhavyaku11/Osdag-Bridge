"""
Automated Functional Test Suite & Test Matrix Runner for OsdagBridge.
Tests core functionality, dictionary key integrity, custom material handling,
multi-run state purity, BOQ calculations, and report generation.

Execution:
    python3 tests/run_functional_tests.py
"""

import os
import sys
import copy
import logging

# Ensure OsdagBridge src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'OsdagBridge', 'src')))

from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_DESIGN_MODE,
    KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_70R_WHEELED,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS
)

from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
from osdagbridge.core.boq.boq_generator import calculate_material_quantities
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
        # Member sectional definitions
        "member_properties.girder_details.section_properties.area": 0.045,
        "member_properties.girder_details.section_properties.mass": 353.25,
    }


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


def test_tc09_custom_material_normalization():
    """TC-09 & TC-15: Custom steel and concrete grade normalization."""
    logger.info("Running TC-09/15: Custom Material Handling...")
    bridge = PlateGirderBridge()
    inputs = build_base_input()
    inputs["material.structural_steel.grade"] = "Custom"
    inputs["material.structural_steel.fy"] = "350"
    inputs["material.structural_steel.fu"] = "490.5"
    inputs["material.concrete.grade"] = "Custom"
    inputs["material.concrete.fck"] = "50"
    bridge.set_input(inputs)

    # Coercion checks
    assert bridge.input_dict["material.structural_steel.fy"] == 350
    assert bridge.input_dict["material.structural_steel.fu"] == 490.5
    assert bridge.input_dict["material.concrete.fck"] == 50
    logger.info("TC-09/15 PASSED.")


def test_tc13_multi_run_state_purity():
    """TC-13: Multi-run sequence verifying state isolation."""
    logger.info("Running TC-13: Multi-run Sequence State Purity...")
    bridge = PlateGirderBridge()

    # Run 1: 20m span
    inputs1 = build_base_input(span=20.0, n_girders=4)
    bridge.set_input(inputs1)
    assert bridge.input_dict[KEY_SPAN] == 20.0

    # Run 2: Modified to 15m span on same instance
    inputs2 = copy.deepcopy(inputs1)
    inputs2[KEY_SPAN] = 15.0
    inputs2[KEY_TS_NO_OF_GIRDERS] = 3
    bridge.set_input(inputs2)

    assert bridge.input_dict[KEY_SPAN] == 15.0
    assert bridge.input_dict[KEY_TS_NO_OF_GIRDERS] == 3
    logger.info("TC-13 PASSED.")


def test_boq_calculations():
    """Test Bill of Quantities (BOQ) calculations across deck concrete, steel, and rebar."""
    logger.info("Running BOQ Calculation Tests...")
    inputs = build_base_input(span=24.0, n_girders=4, spacing=2.5, overhang=1.2, thickness=220)
    outputs = {}

    quantities = calculate_material_quantities(inputs, outputs)

    assert "concrete_deck_vol_total" in quantities
    assert "steel_girders_wt_total" in quantities
    assert "rebar_deck_wt_total" in quantities

    conc_vol = float(quantities["concrete_deck_vol_total"])
    assert conc_vol > 0.0, f"Expected positive concrete volume, got {conc_vol}"

    steel_wt = float(quantities["steel_girders_wt_total"])
    assert steel_wt > 0.0, f"Expected positive steel weight, got {steel_wt}"

    logger.info("BOQ Tests PASSED (Concrete Vol: %.2f m³, Steel: %.2f MT).", conc_vol, steel_wt)


def test_boq_non_uniform_girders_fix_verification():
    """
    Verify Fix for Bug #103:
    When exterior and interior girders have distinct sectional areas,
    calculate_material_quantities accurately sums each individual girder volume.
    """
    logger.info("Running Bug #103 Fix Verification (Non-uniform girder areas)...")
    inputs = build_base_input(span=20.0, n_girders=4)
    # G1 (Exterior): 0.040 m²
    inputs["member_properties.girder_details.section_properties.area.G1.M1"] = 0.040
    # G2 (Interior): 0.060 m² (heavier interior girder)
    inputs["member_properties.girder_details.section_properties.area.G2.M1"] = 0.060
    inputs["member_properties.girder_details.section_properties.area.G3.M1"] = 0.060
    # G4 (Exterior): 0.040 m²
    inputs["member_properties.girder_details.section_properties.area.G4.M1"] = 0.040

    quantities = calculate_material_quantities(inputs, {})
    total_vol = float(quantities["steel_girders_vol_total"])

    # True volume = (2 * 0.040 + 2 * 0.060) * 20.0 = 0.200 * 20.0 = 4.0 m³
    true_vol = (2 * 0.040 + 2 * 0.060) * 20.0
    logger.info("Reported Volume: %.2f m³ | True Volume: %.2f m³", total_vol, true_vol)
    assert abs(total_vol - true_vol) < 0.01, f"Expected true volume {true_vol}, got {total_vol}"
    logger.info("BUG #103 FIX VERIFIED: Volume calculation accurately accounts for individual girder cross sections!")


def test_chart_generation():
    """Verify high-resolution chart generators."""
    logger.info("Running Chart Visualization Engine Tests...")
    test_dir = "/tmp/osdag_test_charts_suite"
    os.makedirs(test_dir, exist_ok=True)

    ur_path = generate_ur_summary_chart({}, test_dir)
    assert ur_path is not None and os.path.exists(ur_path)

    st_path, co_path = generate_material_quantity_chart({}, {}, test_dir)
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

    logger.info("Full Report Generation PASSED: %s", result.tex_path)


def run_all_tests():
    """Run all functional test suite cases."""
    print("=" * 70)
    print("      OSDAGBRIDGE AUTOMATED FUNCTIONAL TEST SUITE")
    print("=" * 70)
    test_tc01_baseline_standard()
    test_tc02_short_span()
    test_tc03_long_span()
    test_tc04_heavy_6_girder()
    test_tc09_custom_material_normalization()
    test_tc13_multi_run_state_purity()
    test_boq_calculations()
    test_boq_non_uniform_girders_fix_verification()
    test_chart_generation()
    test_full_report_generation()
    print("=" * 70)
    print("   ALL FUNCTIONAL TESTS PASSED SUCCESSFULLY! (10/10)")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
