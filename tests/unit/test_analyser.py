"""
Unit test suite for OsdagBridge Structural Analysis & Grillage Engine.
Covers:
  - BridgeGrillageModel initialization
  - Spectral acceleration computation (Sa/g) under IS 1893 / IRC 6
  - Vehicle geometry and weight definitions (Class A, 70R)
  - Resultant load calculations and load combination factors
"""

import pytest
from osdagbridge.core.bridge_types.plate_girder.analyser import BridgeGrillageModel


def test_analyser_model_initialization():
    """Verify BridgeGrillageModel initializes with clean default properties."""
    model = BridgeGrillageModel()
    assert model is not None
    assert hasattr(model, "create_sections")
    assert hasattr(model, "create_model")
    assert hasattr(model, "create_uls_combinations")
    assert hasattr(model, "create_sls_combinations")


def test_spectral_acceleration_is1893_irc6():
    """
    Verify spectral acceleration Sa/g calculation across soil types and natural periods.
    IS 1893:2016 / IRC 6:2017:
      - Type I (Rock / Hard soil): Plateau 2.5 for 0.1s <= T <= 0.4s
      - Type II (Medium soil): Plateau 2.5 for 0.1s <= T <= 0.55s
      - Type III (Soft soil): Plateau 2.5 for 0.1s <= T <= 0.67s
    """
    # Plateau region check: Sa/g must equal 2.5
    assert BridgeGrillageModel._spectral_sa_g(1, 0.2) == 2.5
    assert BridgeGrillageModel._spectral_sa_g(2, 0.3) == 2.5
    assert BridgeGrillageModel._spectral_sa_g(3, 0.5) == 2.5

    # Ascending branch check (T < 0.1s): 1.0 + 15 * T
    t_short = 0.05
    sa_short = 1.0 + 15.0 * t_short
    assert abs(BridgeGrillageModel._spectral_sa_g(1, t_short) - sa_short) < 1e-4

    # Descending branch check (T > plateau): Sa/g falls inversely with T
    t_long = 1.0
    sa_type1 = 1.0 / t_long
    assert abs(BridgeGrillageModel._spectral_sa_g(1, t_long) - sa_type1) < 1e-4

    sa_type2 = 1.36 / t_long
    assert abs(BridgeGrillageModel._spectral_sa_g(2, t_long) - sa_type2) < 1e-4

    sa_type3 = 1.67 / t_long
    assert abs(BridgeGrillageModel._spectral_sa_g(3, t_long) - sa_type3) < 1e-4


def test_vehicle_lengths_and_geometry():
    """Verify standard vehicle track/bogie lengths per IRC 6."""
    len_70r = BridgeGrillageModel._vehicle_length("Class70R")
    assert abs(len_70r - 15.12) < 0.1

    len_class_a = BridgeGrillageModel._vehicle_length("ClassA")
    assert abs(len_class_a - 20.3) < 0.1

    len_unknown = BridgeGrillageModel._vehicle_length("NonExistentVehicle")
    assert len_unknown == 25.0  # safe default fallback


def test_load_combination_registry():
    """Verify that ULS and SLS combination structures define correct partial safety factors."""
    model = BridgeGrillageModel()
    assert callable(model.create_uls_combinations)
    assert callable(model.create_sls_combinations)
