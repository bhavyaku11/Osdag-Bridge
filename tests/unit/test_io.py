"""
Unit test suite for OsdagBridge Input/Output, Model Loading, and File Serialization.
Covers:
  - JSON bridge model loading and schema sanity
  - Missing and corrupted file handling
  - Type-safe key resolution and unit conversions
  - BOQ input dictionary parsing
"""

import json
import os
import pytest

from osdagbridge.cli.commands import load_json_input
from osdagbridge.core.utils.common import KEY_SPAN, KEY_TS_NO_OF_GIRDERS, KEY_TS_DECK_THICKNESS
from osdagbridge.core.boq.boq_generator import calculate_material_quantities


def test_load_valid_sample_model(tmp_path):
    """Verify loading of a valid JSON model file."""
    model_data = {
        KEY_SPAN: 24.0,
        KEY_TS_NO_OF_GIRDERS: 4,
        KEY_TS_DECK_THICKNESS: 220,
        "typical_section.overall_bridge_width": 10.3,
    }
    model_file = tmp_path / "bridge.json"
    model_file.write_text(json.dumps(model_data), encoding="utf-8")

    loaded = load_json_input(str(model_file))
    assert isinstance(loaded, dict)
    assert loaded[KEY_SPAN] == 24.0
    assert loaded[KEY_TS_NO_OF_GIRDERS] == 4


def test_load_non_existent_file():
    """Verify load_json_input raises FileNotFoundError on missing files."""
    with pytest.raises(FileNotFoundError):
        load_json_input("/non/existent/path/bridge.json")


def test_load_malformed_json(tmp_path):
    """Verify load_json_input raises ValueError / JSONDecodeError on malformed JSON content."""
    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("{ span: 24.0, invalid_syntax ", encoding="utf-8")

    with pytest.raises((ValueError, json.JSONDecodeError)):
        load_json_input(str(corrupt_file))


def test_boq_empty_and_invalid_inputs():
    """Verify BOQ generator behaves safely on non-dict or empty inputs."""
    res_none = calculate_material_quantities(None, None)
    assert "_warnings" in res_none
    assert any("not a valid dictionary" in w for w in res_none["_warnings"])

    res_empty = calculate_material_quantities({}, {})
    assert "_warnings" in res_empty
    assert any("Missing mandatory bridge geometry" in w for w in res_empty["_warnings"])
