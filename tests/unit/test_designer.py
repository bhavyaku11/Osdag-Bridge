"""
Unit test suite for OsdagBridge Limit State Designer & DCR Engine.
Covers:
  - DCREngine status evaluation (PASS, WARN, FAIL thresholds)
  - Demand-to-Capacity ratio calculations
  - Multi-category check grouping (Flexure, Shear, Interaction, Buckling, Fatigue, SLS)
  - Governing DCR and category mapping
"""

import pytest
from osdagbridge.core.bridge_types.plate_girder.designer import (
    DemandEnvelope,
    CapacityResults,
    DCREngine,
    CheckResult
)


def test_dcr_engine_classification_thresholds():
    """Verify DCR classification logic: PASS (<0.90), WARN (0.90-1.0), FAIL (>=1.0)."""
    assert DCREngine.classify(0.0) == "PASS"
    assert DCREngine.classify(0.72) == "PASS"
    assert DCREngine.classify(0.89) == "PASS"
    assert DCREngine.classify(0.90) == "WARN"
    assert DCREngine.classify(0.95) == "WARN"
    assert DCREngine.classify(0.99) == "WARN"
    assert DCREngine.classify(1.00) == "FAIL"
    assert DCREngine.classify(1.25) == "FAIL"


def test_dcr_engine_check_addition_and_status():
    """Verify check registration and overall status aggregation."""
    demand = DemandEnvelope(Mu_kNm=1200.0, Vu_kN=450.0, Nsc=50)
    capacity = CapacityResults(Md_kNm=2000.0, Mb_kNm=1800.0)
    engine = DCREngine(demand, capacity)

    # 1. Add passing flexure check: 1200 / 2000 = 0.60
    chk1 = engine._add_check(
        check_id=1,
        name="Flexural Strength (ULS)",
        clause="IRC 22 Cl.603.3",
        demand=1200.0,
        capacity=2000.0,
        unit="kNm",
        note="Bending under LC-ULS-1"
    )
    assert chk1.dcr == 0.60
    assert chk1.status == "PASS"

    # 2. Add shear check: 450 / 600 = 0.75
    chk2 = engine._add_check(
        check_id=2,
        name="Vertical Shear Strength (ULS)",
        clause="IRC 22 Cl.604.2",
        demand=450.0,
        capacity=600.0,
        unit="kN",
        note="Plastic shear resistance"
    )
    assert chk2.dcr == 0.75
    assert chk2.status == "PASS"

    # Overall max DCR should be 0.75 and overall status PASS
    assert engine.max_dcr() == 0.75
    assert engine.overall_status() == "PASS"


def test_dcr_engine_warning_and_failure_states():
    """Verify engine transitions to WARN and FAIL correctly when individual checks exceed limits."""
    demand = DemandEnvelope(Mu_kNm=1900.0, Vu_kN=620.0, Nsc=50)
    capacity = CapacityResults(Md_kNm=2000.0)
    engine = DCREngine(demand, capacity)

    # Add near-limit check: 1900 / 2000 = 0.95 -> WARN
    engine._add_check(
        check_id=1,
        name="Flexural Strength (ULS)",
        clause="IRC 22 Cl.603.3",
        demand=1900.0,
        capacity=2000.0,
        unit="kNm",
        note="Near limit"
    )
    assert engine.max_dcr() == 0.95
    assert engine.overall_status() == "WARN"

    # Add failing check: 620 / 600 = 1.0333 -> FAIL
    engine._add_check(
        check_id=2,
        name="Shear Strength (ULS)",
        clause="IRC 22 Cl.604.2",
        demand=620.0,
        capacity=600.0,
        unit="kN",
        note="Over-capacity shear"
    )
    assert engine.max_dcr() == 1.0333
    assert engine.overall_status() == "FAIL"


def test_dcr_category_aggregation():
    """Verify category_urs groups check IDs into canonical design categories 1-8."""
    demand = DemandEnvelope(Mu_kNm=1000.0, Vu_kN=300.0, Nsc=50)
    capacity = CapacityResults(Md_kNm=2000.0)
    engine = DCREngine(demand, capacity)

    # Check 1 belongs to Category 1 ("Strength – Flexure")
    engine._add_check(1, "Bending Moment", "Cl.603", 1000.0, 2000.0, "kNm", "Midspan")
    # Check 2 belongs to Category 2 ("Strength – Shear")
    engine._add_check(2, "Vertical Shear", "Cl.604", 300.0, 500.0, "kN", "Support")

    cats = engine.category_urs()
    assert 1 in cats
    assert cats[1]["label"] == "Strength – Flexure"
    assert cats[1]["max_dcr"] == 0.50
    assert cats[1]["status"] == "PASS"

    assert 2 in cats
    assert cats[2]["label"] == "Strength – Shear"
    assert cats[2]["max_dcr"] == 0.60
    assert cats[2]["status"] == "PASS"
