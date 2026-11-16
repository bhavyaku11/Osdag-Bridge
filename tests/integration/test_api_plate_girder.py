"""
Integration test suite for OsdagBridge Plate Girder Python API.
Covers:
  - PlateGirderBridge lifecycle (set_input, layout solving)
  - Integration with BOQ material estimator
  - Report payload assembly and LaTeX code emission
"""

import os
import pytest

from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_70R_WHEELED,
)
from osdagbridge.core.boq.boq_generator import calculate_material_quantities
from osdagbridge.core.reports.report_generator import (
    ReportMetadata,
    ReportOptions,
    ReportRequest,
    build_report_payload,
    generate_report
)


def test_plate_girder_bridge_api_lifecycle(tmp_path):
    """Verify programmatic usage of PlateGirderBridge API from initialization to report compilation."""
    bridge = PlateGirderBridge()
    assert bridge is not None

    sample_inputs = {
        KEY_SPAN: 24.0,
        KEY_TS_NO_OF_GIRDERS: 4,
        KEY_TS_GIRDER_SPACING: 2.6,
        KEY_TS_DECK_OVERHANG: 1.25,
        KEY_TS_DECK_THICKNESS: 220,
        "typical_section.overall_bridge_width": 10.3,
        "member_properties.girder_details.section_properties.area": 0.048,
        "member_properties.girder_details.section_properties.mass": 376.8,
        KEY_LL_IRC_CLASS_A: True,
        KEY_LL_IRC_70R_WHEELED: True,
    }

    # 1. Test input setting and layout solving
    bridge.set_input(sample_inputs)
    bridge._solve_bridge_layout()
    assert bridge.output_dict is not None
    assert bridge.output_dict[KEY_SPAN] == 24.0

    # 2. Test BOQ integration
    quantities = calculate_material_quantities(sample_inputs, {})
    assert quantities["steel_girders_vol_total"] != "N.A."
    assert quantities["concrete_deck_vol_total"] != "N.A."
    assert float(quantities["steel_girders_vol_total"]) > 0
    assert float(quantities["concrete_deck_vol_total"]) > 0

    # 3. Test Report Generation from API
    out_dir = str(tmp_path / "api_report")
    os.makedirs(out_dir, exist_ok=True)
    meta = ReportMetadata(
        project_name="API Integration Bridge",
        project_location="NH-48",
        designer="Automation Agent",
        client="NHAI",
        company="IIT Bombay / FOSSEE"
    )
    options = ReportOptions(
        sections=['project_info', 'inputs', 'loads', 'quantities'],
        include_figures=False,
        include_toc=True,
        include_pdf=False
    )
    request = ReportRequest(
        metadata=meta,
        options=options,
        output_dir=out_dir,
        file_stem="api_bridge_report"
    )

    payload = build_report_payload(request, sample_inputs, {})
    result = generate_report(payload, request)

    assert result.tex_path and os.path.isfile(result.tex_path)
    with open(result.tex_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "API Integration Bridge" in content
    assert "NH-48" in content
    assert "\\begin{longtable}" in content
    assert "\\endfirsthead" in content
    assert "\\endhead" in content
