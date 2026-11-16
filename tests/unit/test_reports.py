r"""
Unit test suite for OsdagBridge Report Generator and Styles.
Covers:
  - Centralized styles, geometry, and color palettes
  - Chart generation engines (UR summary, material take-offs)
  - LongTable header repetition (\endhead, \endfirsthead)
  - Chapter 3, 5, 7 refactoring and BOM volume calculations
"""

import os
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
from osdagbridge.core.boq.boq_generator import calculate_material_quantities
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


def test_chart_generation_engines(tmp_path):
    """Verify UR summary and material quantity chart engines."""
    tmp_dir = str(tmp_path)
    ur_path = generate_ur_summary_chart({}, tmp_dir)
    assert ur_path is not None
    assert os.path.exists(ur_path)

    st_path, co_path = generate_material_quantity_chart({}, {}, tmp_dir)
    assert st_path is not None and os.path.exists(st_path)
    assert co_path is not None and os.path.exists(co_path)


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

    with open(result.tex_path, "r", encoding="utf-8") as f:
        tex = f.read()

    assert "bottom=2.8cm" in tex
    assert "footskip=38pt" in tex
    assert "tableHeaderBg" in tex
    assert "ur_summary.png" in tex
    assert "material_steel.png" in tex
    assert "Footpath and Pedestrian Live Loads" in tex
    assert "\\endhead" in tex
