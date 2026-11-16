# OsdagBridge Multi-Tier Software Testing Matrix
## FOSSEE Osdag Winter Internship 2026 — Task 6 (Software Testing & Issue Reporting)

This document defines the systematic test matrix, parameter variations, dictionary audit checkpoints, and multi-run state persistence tests executed across OsdagBridge.

---

## 1. Overview of Test Case Matrix (20 Scenarios)

| Case ID | Category | Span (m) | No. of Girders | Carriageway (m) | Skew (°) | Material Configuration | Key Verification Focus |
|---|---|---|---|---|---|---|---|
| **TC-01** | Baseline Standard | 20.0 | 4 | 7.5 | 0 | Default (E250, M40) | Standard baseline run, baseline report generation |
| **TC-02** | Short Span Extreme | 10.0 | 2 | 4.25 (Single Lane) | 0 | Default (E250, M35) | 2-girder load distribution, grillage mesh density |
| **TC-03** | Long Span Extreme | 30.0 | 5 | 11.0 (3 Lanes) | 0 | E350, M45 | Deflection limits, lateral torsional buckling check |
| **TC-04** | Heavy 6-Girder Bridge | 25.0 | 6 | 14.5 (4 Lanes) | 0 | E350, M40 | Multi-girder shear distribution, cross-frame forces |
| **TC-05** | Skew Angle Geometry | 18.0 | 4 | 7.5 | 15 | Default (E250, M40) | Torsional moment at obtuse corners, bearing uplift |
| **TC-06** | High Skew Extreme | 22.0 | 4 | 8.5 | 30 | E350, M45 | Transverse bracing shear, diaphragm rotation |
| **TC-07** | Zero Overhang Edge | 15.0 | 3 | 7.0 | 0 | Default (E250, M40) | Outer girder self-weight load placement (Bug #91) |
| **TC-08** | Large Overhang Edge | 20.0 | 3 | 7.5 | 0 | Default (E250, M40) | Cantilever slab bending, barrier load eccentricity |
| **TC-09** | Custom Steel E350 | 24.0 | 4 | 7.5 | 0 | Custom ($F_y=350$ MPa, $F_u=490$ MPa) | Material property registration and yield strength check |
| **TC-10** | Custom High-Strength Steel | 28.0 | 4 | 9.5 | 0 | Custom ($F_y=450$ MPa, $F_u=570$ MPa) | Web slenderness limits, yield strength safety checks |
| **TC-11** | Custom Concrete Grade | 16.0 | 4 | 7.5 | 0 | Custom M50 ($f_{ck}=50$ MPa) | Composite modular ratio $m$, deck slab capacity |
| **TC-12** | Custom Deck Density | 20.0 | 4 | 7.5 | 0 | Custom ($\gamma_c=26$ kN/m³, $\gamma_s=79$ kN/m³) | Dead load self-weight recalculation |
| **TC-13** | Multi-Run Sequence 1 | 20.0 ➔ 15.0 | 4 | 7.5 | 0 | Default ➔ Modified | Unlock ➔ modify span ➔ re-run; check stale state |
| **TC-14** | Multi-Run Sequence 2 | 20.0 | 4 ➔ 3 | 7.5 | 0 | Default ➔ Modified | Unlock ➔ change girder count ➔ re-run; check CAD refresh |
| **TC-15** | Multi-Run Sequence 3 | 20.0 | 4 | 7.5 | 0 | Default ➔ Custom Material | Unlock ➔ modify steel yield strength ➔ re-run |
| **TC-16** | Heavy IRC Class 70R | 20.0 | 4 | 7.5 | 0 | Default | Class 70R Tracked & Wheeled eccentric loading |
| **TC-17** | Special Vehicle (SV) | 25.0 | 5 | 11.0 | 0 | E350, M45 | Multi-axle SV loading, governing moment/shear check |
| **TC-18** | Footway Load Only | 12.0 | 3 | 4.25 | 0 | Default | Pedestrian bridge loading, minimum live load |
| **TC-19** | Empty Custom Field Guard | 20.0 | 4 | 7.5 | 0 | Custom Radio with empty input | Pre-save validation error dialog handling |
| **TC-20** | Unsaved Changes Guard | 20.0 | 4 | 7.5 | 0 | Modify inputs, close dialog | Close event warning dialog verification |

---

## 2. Dictionary Audit Points (Input vs. Output vs. Report)

For each executed scenario, the following keys must be audited across three stages:

1. **Geometry & Cross Section**:
   - `KEY_SPAN`
   - `KEY_TS_NO_OF_GIRDERS`
   - `KEY_TS_GIRDER_SPACING`
   - `KEY_TS_DECK_OVERHANG`
   - `KEY_TS_DECK_THICKNESS`
2. **Material Properties**:
   - `KEY_MATERIAL_STEEL_YIELD`
   - `KEY_MATERIAL_CONCRETE_GRADE`
   - `KEY_MATERIAL_GIRDER_DENSITY`
   - `KEY_MATERIAL_DECK_DENSITY`
3. **Analysis Demands**:
   - `KEY_SD_MOMENT_MU` (Governing Bending Moment)
   - `KEY_SD_SHEAR_VU` (Governing Shear Force)
   - `KEY_SD_MAX_DEFLECTION` (Live Load Deflection)
4. **Design Capacities & DCR**:
   - `KEY_SD_MD` (Design Bending Strength)
   - `KEY_SD_VD` (Design Shear Strength)
   - `KEY_UTIL_BENDING` (Bending Utilization Ratio)
   - `KEY_UTIL_SHEAR` (Shear Utilization Ratio)
   - `KEY_UTIL_INTERACTION` (M-V Interaction Ratio)
5. **Bill of Materials**:
   - `steel_girders_wt_total` vs `steel_girders_vol_total * density`
   - `concrete_deck_vol_total` vs modeled geometry
   - `rebar_deck_wt_total` vs design reinforcement
