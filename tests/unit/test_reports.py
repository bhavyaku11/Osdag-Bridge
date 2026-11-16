r"""
Unit test suite for OsdagBridge Report Generator and Styles.
Covers:
  - Centralized styles, geometry, and color palettes
  - Chart generation engines (UR summary, material take-offs) with zero fabrication
  - Incomplete / partial material breakdown warnings and diagnostics
  - LongTable header repetition (\endhead, \endfirsthead)
  - Chapter 3, 5, 7 refactoring and BOM volume calculations
  - Regression testing for Issue #103 (missing girder detection, no silent fallbacks)
  - Parameterized material assumptions
  - Input validation: rejection of NaN, inf, fractional girder counts, negative spans
  - Mass vs. volume consistency validation ($m \approx A \times \rho$)
  - Optional PDF compilation verification
"""

import math
import os
import shutil
import pytest

from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_70R_WHEELED,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_NO_OF_FOOTPATHS
)

from osdagbridge.core.reports.styles import ReportStyle, ColorPalette, GeometryConfig, TableFormatting
from osdagbridge.core.reports.report_utils import build_table_with_headers
from osdagbridge.core.reports.plot_utils import generate_ur_summary_chart, generate_material_quantity_chart
from osdagbridge.core.boq.boq_generator import calculate_material_quantities, resolve_girder_value
from osdagbridge.core.reports.report_generator import (
    ReportMetadata,
    ReportOptions,
    ReportRequest,
    ReportPayload,
    ReportFigures,
    generate_report
)


def test_styles_geometry_and_colors():
    """Verify centralized style definitions and geometry clearances."""
    geom = ReportStyle.get_geometry_preamble()
    assert "bottom=2.8cm" in geom
    assert "footskip=38pt" in geom

    colors = ReportStyle.get_latex_color_definitions()
    assert "tableHeaderBg" in colors
    assert "osdagGreen" in colors
    assert "osdagPass" in colors

    tbl = ReportStyle.get_table_preamble()
    assert "\\tabcolsep" in tbl
    assert "\\arraystretch" in tbl
    assert "\\newcolumntype{L}" in tbl


def test_build_longtable_header():
    """Verify LongTable header/footer repetition macros."""
    lt_str = build_table_with_headers(
        col_spec="|L{5cm}|p{10cm}|",
        header_row=r"\textbf{Param} & \textbf{Val}",
        caption="Sample Test Table",
        label="tab:sample",
        body_rows=["Row 1 & Value 1 \\\\[4pt]\n\\hline"]
    )
    assert "\\begin{longtable}{|L{5cm}|p{10cm}|}" in lt_str
    assert "\\endfirsthead" in lt_str
    assert "\\endhead" in lt_str
    assert "\\endfoot" in lt_str
    assert "\\endlastfoot" in lt_str
    assert "\\rowcolor{tableHeaderBg}" in lt_str
    assert "Row 1 & Value 1" in lt_str


def test_chart_generation_engines_zero_fabrication(tmp_path):
    """Verify that chart engines enforce engineering integrity and never fabricate results."""
    tmp_dir = str(tmp_path)

    # 1. Strict engineering mode without data must return None (NO fabricated numbers)
    diag = {}
    assert generate_ur_summary_chart({}, tmp_dir, demo_mode=False, diagnostics=diag) is None
    assert "ur_summary: no calculated utilization ratios present in output_dict" in diag.get("charts_skipped", [])

    # 2. Strict engineering mode with valid 0.0 UR must be accepted (not treated as missing)
    valid_zero_out = {"steeldesign.details.bending.utilization_ratio": 0.0}
    zero_chart = generate_ur_summary_chart(valid_zero_out, tmp_dir, demo_mode=False)
    assert zero_chart is not None and os.path.exists(zero_chart)

    # 3. Explicit demo mode generates benchmark visual
    demo_ur = generate_ur_summary_chart({}, tmp_dir, demo_mode=True)
    assert demo_ur is not None and os.path.exists(demo_ur)

    # 4. Populated material quantities generate valid breakdown charts
    quantities = {
        "steel_girders_wt_total": "32.50",
        "bracing_top_wt_total": "2.80",
        "concrete_deck_vol_total": "54.00",
        "rebar_deck_wt_total": "6.48"
    }
    st_path, co_path = generate_material_quantity_chart({}, quantities, tmp_dir)
    assert st_path is not None and os.path.exists(st_path)
    assert co_path is not None and os.path.exists(co_path)


def test_material_chart_partial_quantities_warning(tmp_path):
    """Verify that partial material quantities trigger explicit warnings and diagnostics."""
    tmp_dir = str(tmp_path)
    # Only Main Girders available; bracing and studs are missing
    partial_quantities = {
        "steel_girders_wt_total": "28.00"
    }
    diag = {}
    st_path, co_path = generate_material_quantity_chart({}, partial_quantities, tmp_dir, demo_mode=False, diagnostics=diag)

    assert st_path is not None and os.path.exists(st_path)
    # Must record warning in diagnostics that partial quantities were plotted
    assert any("Partial breakdown" in w for w in diag.get("warnings", []))


def test_boq_non_uniform_girder_volume():
    """Verify Issue #103 fix: Non-uniform girder sectional areas sum correctly."""
    inputs = {
        KEY_SPAN: 20.0,
        KEY_TS_NO_OF_GIRDERS: 4,
        KEY_TS_GIRDER_SPACING: 2.5,
        KEY_TS_DECK_OVERHANG: 1.2,
        KEY_TS_DECK_THICKNESS: 220,
        "typical_section.overall_bridge_width": 9.9,
        "member_properties.girder_details.section_properties.area.G1.M1": 0.040,
        "member_properties.girder_details.section_properties.area.G2.M1": 0.060,
        "member_properties.girder_details.section_properties.area.G3.M1": 0.060,
        "member_properties.girder_details.section_properties.area.G4.M1": 0.040,
    }
    quantities = calculate_material_quantities(inputs, {})
    total_vol = float(quantities["steel_girders_vol_total"])
    true_vol = (2 * 0.040 + 2 * 0.060) * 20.0
    assert abs(total_vol - true_vol) < 0.01
    assert not quantities.get("_warnings")


def test_boq_missing_girder_rejection_issue_103():
    """Verify that when a per-girder scheme is active and Girder 3 is missing, it is NOT silently replaced by G1."""
    inputs = {
        KEY_SPAN: 20.0,
        KEY_TS_NO_OF_GIRDERS: 4,
        KEY_TS_GIRDER_SPACING: 2.5,
        KEY_TS_DECK_OVERHANG: 1.2,
        KEY_TS_DECK_THICKNESS: 220,
        "typical_section.overall_bridge_width": 9.9,
        "member_properties.girder_details.section_properties.area.G1.M1": 0.040,
        "member_properties.girder_details.section_properties.area.G2.M1": 0.060,
        # Girder 3 is intentionally missing
        "member_properties.girder_details.section_properties.area.G4.M1": 0.040,
    }
    base_key = "member_properties.girder_details.section_properties.area"

    # resolve_girder_value must raise KeyError for girder index 2 (G3)
    with pytest.raises(KeyError) as exc_info:
        resolve_girder_value(inputs, base_key, 2)
    assert "missing for girder G3" in str(exc_info.value)

    # calculate_material_quantities must report N.A. and flag warnings rather than fabricating
    quantities = calculate_material_quantities(inputs, {})
    assert quantities["steel_girders_vol_total"] == "N.A."
    assert quantities["steel_girders_wt_total"] == "N.A."
    warnings = quantities.get("_warnings", [])
    assert any("G3" in w for w in warnings)


def test_boq_configurable_material_assumptions():
    """Verify that configurable material densities and rebar rates take effect."""
    inputs = {
        KEY_SPAN: 20.0,
        KEY_TS_NO_OF_GIRDERS: 4,
        KEY_TS_DECK_THICKNESS: 200,
        "typical_section.overall_bridge_width": 10.0,
        "member_properties.girder_details.section_properties.area": 0.05,
        "design_options.material_assumptions": {
            "concrete_density_t_m3": 2.4,
            "rebar_rate_kg_m3": 100.0,
            "steel_density_kg_m3": 7800.0
        }
    }
    quantities = calculate_material_quantities(inputs, {})
    # Concrete volume = 20 * 10 * 0.2 = 40.0 m^3
    # Concrete wt = 40.0 * 2.4 = 96.0 MT
    assert quantities["concrete_deck_vol_total"] == "40.00"
    assert quantities["concrete_deck_wt_total"] == "96.00"
    # Rebar wt = 40.0 * 100.0 kg = 4000.0 kg = 4.0 MT
    assert quantities["rebar_deck_wt_total"] == "4.00"
    assert quantities["_assumptions"]["concrete_density_t_m3"] == 2.4


def test_boq_invalid_numerical_inputs_rejection():
    """Verify that NaN, infinity, fractional girder counts, and negative values are strictly rejected."""
    base = {
        KEY_SPAN: 20.0,
        KEY_TS_NO_OF_GIRDERS: 4,
        KEY_TS_DECK_THICKNESS: 220,
        "typical_section.overall_bridge_width": 10.0,
        "member_properties.girder_details.section_properties.area": 0.04
    }

    # 1. Fractional girder count (e.g. 4.8) must be rejected
    m_fractional = dict(base, **{KEY_TS_NO_OF_GIRDERS: 4.8})
    q_frac = calculate_material_quantities(m_fractional, {})
    assert any("Girder count must be a positive integer" in w for w in q_frac["_warnings"])
    assert q_frac["steel_girders_vol_total"] == "N.A."

    # 2. NaN span must be rejected
    m_nan = dict(base, **{KEY_SPAN: float("nan")})
    q_nan = calculate_material_quantities(m_nan, {})
    assert any("Bridge span must be a positive, finite number" in w for w in q_nan["_warnings"])

    # 3. Infinite span must be rejected
    m_inf = dict(base, **{KEY_SPAN: float("inf")})
    q_inf = calculate_material_quantities(m_inf, {})
    assert any("Bridge span must be a positive, finite number" in w for w in q_inf["_warnings"])

    # 4. Negative girder count
    m_neg = dict(base, **{KEY_TS_NO_OF_GIRDERS: -3})
    q_neg = calculate_material_quantities(m_neg, {})
    assert any("Girder count must be a positive integer" in w for w in q_neg["_warnings"])


def test_boq_mass_vs_volume_consistency_warning():
    """Verify that a >15% discrepancy between provided mass and theoretical mass generates a diagnostic warning."""
    # Area = 0.040 m^2, steel density = 7850 kg/m^3 -> expected mass = 314.0 kg/m
    # If provided mass is 50.0 kg/m, it deviates by >80%
    inputs = {
        KEY_SPAN: 20.0,
        KEY_TS_NO_OF_GIRDERS: 4,
        KEY_TS_DECK_THICKNESS: 220,
        "typical_section.overall_bridge_width": 10.0,
        "member_properties.girder_details.section_properties.area": 0.040,
        "member_properties.girder_details.section_properties.mass": 50.0  # heavily inconsistent
    }
    quantities = calculate_material_quantities(inputs, {})
    warnings = quantities.get("_warnings", [])
    assert any("deviates by" in w and "theoretical mass" in w for w in warnings)


def test_full_report_tex_assembly(tmp_path):
    """Verify full report generation produces valid .tex with charts and repeated headers."""
    out_dir = str(tmp_path)
    metadata = ReportMetadata(
        project_name="Unit Test Bridge",
        project_location="Mumbai",
        designer="Unit Tester",
        client="NHAI",
        company="FOSSEE",
        job_number="UT-01",
        report_date="Nov 2026"
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
        output_dir=out_dir,
        file_stem="unit_test_report"
    )
    payload = ReportPayload(
        metadata=metadata,
        options=options,
        inputs={
            KEY_SPAN: 20.0,
            KEY_TS_NO_OF_GIRDERS: 4,
            KEY_TS_GIRDER_SPACING: 2.5,
            KEY_TS_DECK_OVERHANG: 1.2,
            KEY_TS_DECK_THICKNESS: 220,
            "typical_section.overall_bridge_width": 9.9,
            "member_properties.girder_details.section_properties.area": 0.048,
            "member_properties.girder_details.section_properties.mass": 376.8,
            KEY_LL_IRC_CLASS_A: True,
            KEY_LL_IRC_70R_WHEELED: True,
            KEY_TS_FOOTPATH_WIDTH: 1500,
            KEY_TS_NO_OF_FOOTPATHS: "Both Sides",
        },
        analysis_summary={},
        design_checks=[],
        figures=ReportFigures(),
        output_dict={"steeldesign.details.bending.utilization_ratio": 0.72}
    )

    result = generate_report(payload, request)
    assert result.tex_path and os.path.exists(result.tex_path)
    assert isinstance(result.diagnostics, dict)
    assert "charts_generated" in result.diagnostics

    with open(result.tex_path, "r", encoding="utf-8") as f:
        tex = f.read()

    assert "bottom=2.8cm" in tex
    assert "footskip=38pt" in tex
    assert "tableHeaderBg" in tex
    assert "ur_summary.png" in tex
    assert "material_steel.png" in tex
    assert "material_concrete.png" in tex
    assert "Footpath and Pedestrian Live Loads" in tex
    assert "\\endhead" in tex
    assert "\\endfirsthead" in tex


@pytest.mark.skipif(not shutil.which("pdflatex"), reason="pdflatex compiler not installed in local environment")
def test_pdf_compilation_when_toolchain_present(tmp_path):
    """Test PDF compilation when pdflatex is present on PATH."""
    out_dir = str(tmp_path)
    metadata = ReportMetadata(
        project_name="PDF Smoke Test",
        project_location="Delhi",
        designer="Tester",
        client="MoRTH",
        company="IIT Bombay"
    )
    options = ReportOptions(
        sections=['project_info', 'inputs'],
        include_figures=False,
        include_toc=False,
        include_pdf=True
    )
    request = ReportRequest(
        metadata=metadata,
        options=options,
        output_dir=out_dir,
        file_stem="pdf_smoke"
    )
    payload = ReportPayload(
        metadata=metadata,
        options=options,
        inputs={KEY_SPAN: 15.0, KEY_TS_NO_OF_GIRDERS: 3},
        analysis_summary={},
        design_checks=[],
        figures=ReportFigures()
    )
    result = generate_report(payload, request)
    assert result.pdf_path and os.path.exists(result.pdf_path)
