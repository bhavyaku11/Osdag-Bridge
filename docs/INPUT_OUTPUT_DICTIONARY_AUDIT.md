# OsdagBridge Input/Output Data Dictionary Audit
## FOSSEE Winter Internship 2026 — Task 6 (TR-6.3 Data Verification)

This document provides a comprehensive side-by-side audit of the canonical input dictionaries (`input_dict`), numerical analysis demands, design capacity checks, and Bill of Quantities (BOQ) output dictionaries (`output_dict`) across OsdagBridge.

---

## 1. Primary Geometric & Superstructure Inputs

| Canonical Key (`common.py`) | Parameter Description | Expected Type | Engineering Units | Feasibility Bounds | Handled by Validator | Report Chapter |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `KEY_SPAN` (`geometry.span`) | Effective span length of bridge | `float` | $\text{m}$ | $5.0 \le L \le 50.0$ | `_validate_inputs()` | Ch. 2, Table 2.1 |
| `KEY_TS_NO_OF_GIRDERS` (`typical_section.no_of_girders`) | Number of longitudinal plate girders | `int` | Count | $N \ge 2$, integer only | `_validate_inputs()` | Ch. 2, Table 2.1 |
| `KEY_TS_GIRDER_SPACING` (`typical_section.girder_spacing`) | Transverse center-to-center girder spacing | `float` | $\text{m}$ | $1.2 \le s \le 4.5$ | `_validate_inputs()` | Ch. 2, Table 2.1 |
| `KEY_TS_DECK_OVERHANG` (`typical_section.deck_overhang`) | Cantilever slab overhang beyond outer girder | `float` | $\text{m}$ | $0.0 \le w_{oh} \le 2.5$ | `_validate_inputs()` | Ch. 2, Table 2.1 |
| `KEY_TS_DECK_THICKNESS` (`typical_section.deck_thickness`) | Structural RC slab depth | `float` | $\text{mm}$ | $180 \le t_d \le 450$ | `_validate_inputs()` | Ch. 2, Table 2.1 |
| `KEY_SKEW_ANGLE` (`geometry.skew_angle`) | Superstructure skew alignment angle | `float` | Degrees (°) | $0.0 \le \theta \le 45.0$ | `_validate_inputs()` | Ch. 2, Table 2.1 |
| `KEY_DESIGN_MODE` (`design_mode`) | Design optimization methodology | `str` | Enum | `"Specified"` / `"Optimized"` | `_validate_inputs()` | Exec Summary |

---

## 2. Material Property & Assumption Inputs

| Canonical Key | Parameter Description | Expected Type | Default | Override Key (`design_options`) | Report Mapping |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `KEY_MATERIAL_GIRDER_DENSITY` | Structural steel material density | `float` | $78.5\text{ kN/m}^3$ | `material_assumptions.girder_density_t_m3` | Ch. 2, Table 2.3 |
| `KEY_MATERIAL_DECK_DENSITY` | Reinforced concrete material density | `float` | $25.0\text{ kN/m}^3$ | `material_assumptions.concrete_density_t_m3` | Ch. 2, Table 2.3 |
| `KEY_MATERIAL_STEEL_YIELD` | Nominal yield strength ($F_y$) | `float` | $250.0\text{ MPa}$ | `material.structural_steel.fy` | Ch. 2, Table 2.3 |
| `KEY_MATERIAL_STEEL_ULTIMATE` | Nominal ultimate strength ($F_u$) | `float` | $410.0\text{ MPa}$ | `material.structural_steel.fu` | Ch. 2, Table 2.3 |
| `KEY_DECK_CONCRETE_GRADE` | Concrete characteristic cube strength ($f_{ck}$) | `str` / `float` | `"M40"` ($40\text{ MPa}$) | `material.concrete.grade` | Ch. 2, Table 2.3 |
| `KEY_WC_MATERIAL` | Wearing course surfacing composition | `str` | `"Bituminous"` | `wearing_coat.material` | Ch. 2, Table 2.2 |
| `KEY_WC_THICKNESS` | Wearing course layer depth | `float` | $75\text{ mm}$ | `wearing_coat.thickness` | Ch. 2, Table 2.2 |

---

## 3. Live Load & Environmental Demands

| Canonical Key | Loading Type | Standard Specification | Reduction / Impact Factor Handling | Report Mapping |
| :--- | :--- | :--- | :--- | :--- |
| `KEY_LL_IRC_CLASS_A` | Wheeled Train Live Load | IRC 6:2017 Cl. 204 | Impact allowance per Cl. 208 | Ch. 3, Table 3.3 |
| `KEY_LL_IRC_70R_WHEELED` | 100-tonne Wheeled Vehicle | IRC 6:2017 Cl. 204 | Impact allowance per Cl. 208 | Ch. 3, Table 3.3 |
| `KEY_LL_IRC_70R_TRACKED` | 70-tonne Bogie Tracked Vehicle | IRC 6:2017 Cl. 204 | Impact allowance per Cl. 208 | Ch. 3, Table 3.3 |
| `KEY_TS_FOOTPATH_WIDTH` | Footpath Pedestrian Geometry | IRC 6:2017 Cl. 206.1 | Width in mm | Ch. 3, Table 3.4 |
| `KEY_TS_NO_OF_FOOTPATHS` | Footpath Configuration | Enum | `"None"`, `"One Side"`, `"Both Sides"` | Ch. 3, Table 3.4 |

---

## 4. Bill of Quantities (BOQ) Output Keys & Provenance Tracking

| Output Key | Physical Quantity | Calculation Method | Provenance & Validation Logic |
| :--- | :--- | :--- | :--- |
| `steel_girders_vol_total` | Structural steel girder volume ($\text{m}^3$) | Sum over all $N$ girders: $\sum A_i \times L$ | **Bug #103 Fix**: Resolves per-girder cross-sections. Rejects silent fallback if girder data is incomplete. |
| `steel_girders_wt_total` | Total girder mass ($\text{MT}$) | Sum over all $N$ girders: $\sum m_i \times L / 1000$ | Evaluates mass-volume consistency against $A_i \times \rho_{\text{steel}}$. Flags discrepancies $> 15\%$. |
| `concrete_deck_vol_total` | Deck slab concrete volume ($\text{m}^3$) | $W_{\text{deck}} \times t_d \times L$ | Computed directly from validated transverse deck dimensions. |
| `rebar_deck_wt_total` | Deck reinforcement rebar mass ($\text{MT}$) | $V_{\text{concrete}} \times \text{rate}_{\text{rebar}} / 1000$ | Configurable rate (default $120.0\text{ kg/m}^3$). Parameterized in `material_assumptions`. |
| `_girder_mass_provenance` | Mass calculation origin list | Array of strings per girder | Explicitly tags `"provided"` vs `"computed_from_density"`. |
| `_warnings` | Validation & consistency log | Array of warning strings | Captures physical discrepancies, non-uniform deviations, and input gaps without failing execution. |

---

## 5. Audit Conclusions & Normalization Rules

1. **Strict Type Coercion**: Any numeric string (`"24.0"`, `"4"`) is safely parsed via `_parse_strict_positive_float()` and `_parse_strict_positive_int()`.
2. **Rejection of Non-Physical Quantities**: Floating-point values such as `NaN`, `+inf`, `-inf`, or fractional girder counts (`4.8`) are strictly rejected.
3. **No Ghost Material Assumptions**: Visualization charts extract concrete grades (`M50`, `M40`) and rebar grades (`Fe 500`) directly from `inputs`, defaulting to neutral labels (`"Concrete Volume"`, `"Reinforcement Steel"`) when unspecified rather than fabricating designations.
