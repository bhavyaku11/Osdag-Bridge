# OsdagBridge Architecture Documentation

OsdagBridge is an open-source, multi-platform engineering software suite developed under the **FOSSEE (Free and Open Source Software for Education)** initiative at **IIT Bombay**. It provides automated structural modeling, finite element grillage analysis, IRC 22 / IS 800 limit state code checking, Bill of Quantities (BOQ) estimation, and publication-ready LaTeX design report generation for composite steel-concrete highway bridges.

---

## 1. High-Level Architectural Overview

OsdagBridge is structured into clean, decoupled layers separating domain modeling, numerical computation, code verification, data serialization, and reporting:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        User & API Entry Points                         │
│   • CLI (osdagbridge.cli)           • Desktop UI (PyQt6 / QWebEngine)  │
│   • Programmatic Python API         • Web / Cloud Headless API         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     Bridge Orchestration Core                          │
│   • PlateGirderBridge / BoxGirderBridge                                │
│   • Input Coercion, Normalization & Geometric Bounds Validation        │
│   • Bridge Layout & Alignment Solver                                   │
└──────────────┬────────────────────┬────────────────────┬───────────────┘
               │                    │                    │
               ▼                    ▼                    ▼
┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐
│  Analysis & Grillage │ │ Code Design & Checks │ │   BOQ & Estimator    │
│  • OpenSeesPy FEA    │ │  • IRC 22:2015 ULS   │ │  • Concrete & Rebar  │
│  • ospgrillage mesh  │ │  • IS 800:2007 Steel │ │  • Multi-Girder Area │
│  • Vehicle Placements│ │  • DCREngine (1-8)   │ │  • Bracing & Studs   │
└──────────────┬───────┘ └──────────┬───────────┘ └──────────┬───────────┘
               │                    │                        │
               └────────────────────┼────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   LaTeX Engineering Report Generator                   │
│   • Centralized Styling & Geometry Clearances (ReportStyle)            │
│   • Publication-Grade Chart Generators (matplotlib dpi=300)            │
│   • Repeated LongTable Headers (\endfirsthead, \endhead, \endfoot)     │
│   • 7-Chapter Modular LaTeX Assembly & pdflatex Toolchain              │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Subsystems

### 2.1 CLI & Automation Interface (`osdagbridge.cli`)
The command-line interface provides lightweight, headless access to the full engineering suite:
- `osdagbridge analyze <model.json>`: Syntactic, geometric, and material validation of bridge definitions.
- `osdagbridge boq <model.json>`: Instant material take-off computing steel, concrete, rebar, stud, and barrier quantities.
- `osdagbridge report <model.json> [--output-dir DIR]`: Automated assembly of publication-quality `.tex` reports and charts.
- `osdagbridge version`: Version, author, and licensing information.

### 2.2 Bridge Domain Modeling (`osdagbridge.core.bridge_types`)
The `PlateGirderBridge` class represents the fully verified, production-tested superstructure model within OsdagBridge, serving as the foundation for analysis, limit state design checking, BOQ calculations, and LaTeX reporting. (Other bridge superstructure configurations such as box girders and trusses exist as upstream architectural scaffolding for future internship phases).

Key lifecycle stages in `PlateGirderBridge`:
1. `set_input(dict)`: Deep copies and coerces input parameters into strongly typed values.
2. `_validate_inputs()`: Enforces geometric and physical feasibility bounds ($L > 0$, $N_{girders} \ge 2$, positive spacing).
3. `_solve_bridge_layout()`: Computes transverse offsets, cantilever spans, and deck widths.
4. `setup_grillage()`: Synthesizes longitudinal girder elements, transverse slab mesh, and diaphragms.

### 2.3 Structural Grillage Analysis (`osdagbridge.core.solvers` & `analyser.py`)
- Adapts OpenSeesPy through an `ospgrillage` grillage mesh abstraction.
- Implements IRC 6:2017 standard live load models: Class A, Class 70R Wheeled, Class 70R Tracked, and Special Vehicles.
- Automatically calculates seismic spectral accelerations ($S_a/g$) per IS 1893:2016 for Rock, Medium, and Soft soils.
- Evaluates load combinations across Ultimate Limit States (ULS) and Serviceability Limit States (SLS).

### 2.4 IRC 22 / IS 800 Limit State Design (`osdagbridge.core.bridge_types.plate_girder.designer`)
- `IRC22CapacityCalculator`: Computes effective flange widths ($b_{eff}$), neutral axis depth ($x_u$), plastic moment capacity ($M_d$), vertical shear resistance ($V_d$), shear buckling resistance ($V_{cr}$), and lateral torsional buckling moment ($M_b$).
- `DCREngine`: Evaluates Demand-to-Capacity Ratios against canonical safety thresholds:
  - **PASS**: $DCR < 0.90$
  - **WARN**: $0.90 \le DCR < 1.00$
  - **FAIL**: $DCR \ge 1.00$
- Aggregates checks into 8 standardized engineering categories (Flexure, Shear, Interaction, LTB, Longitudinal Shear, Fatigue, SLS Stresses, Deflections).

### 2.5 Material Take-Off & BOQ Engine (`osdagbridge.core.boq.boq_generator`)
- Computes structural steel weight, concrete deck volume, reinforcement rebar tonnage, shear connector counts, and crash barrier volumes.
- **Architectural Solution for Issue #103**: Supports non-uniform girder cross-sections without silent fallback. When a per-girder scheme (`.G1`, `.G2`) is detected, every girder must be resolved independently. If a girder (e.g. G3) is missing, it raises an explicit validation error and outputs `"N.A."` with warning diagnostics rather than copying G1 dimensions.
- Allows user override of material densities and rebar rates via `design_options.material_assumptions`.

### 2.6 LaTeX Report Generator Engine (`osdagbridge.core.reports`)
- Emits clean, modular LaTeX source code complying with standard academic and industrial formatting.
- Features multi-page table continuation using `\begin{longtable}`, `\endfirsthead`, `\endhead`, `\endfoot`, and `\endlastfoot`.
- Integrates vector-quality charts generated via matplotlib with strict zero-fabrication guarantees (`demo_mode=False` default).

---

## 3. Data Integrity & Verification Principles

1. **Zero Fabrication**: Engineering calculation results and utilization ratios are never fabricated or estimated with placeholder values. If a solver result is absent, the engine reports uncalculated status (`N.A.` / `None`).
2. **Deterministic Multi-Run Isolation**: Bridge state is strictly instance-scoped. Successive modifications to geometry or materials do not retain stale cached calculations from previous runs.
3. **Explicit Error Propagation**: Missing girder dimensions or invalid geometry values surface as structured warnings and validation exceptions.
