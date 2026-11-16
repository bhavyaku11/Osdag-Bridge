# Product Requirement Document (PRD) & Technical Specification
## OsdagBridge: LaTeX Report Generator Refactoring & Systematic Software Testing

**Document Version:** 1.0.0  
**Target Project:** FOSSEE Osdag Winter Internship 2026 (Tasks 3 & 6 Dual Track)  
**Author:** Bhavya Kumar  
**Status:** In Review / Ready for Phased Execution  

---

## 1. Executive Summary & Synergy

This project combines two high-impact, complementary engineering efforts for **OsdagBridge** (the specialized short-span steel girder bridge design plugin for Osdag):

1. **Task 3: LaTeX Report Generator Refactoring & Enhancements**:
   Refactor the report generation pipeline (`src/osdagbridge/core/reports/`) into a modern, centralized, publication-grade reporting engine using PyLaTeX and Matplotlib. Fixes layout bleed, multi-page table header truncation, and footer collisions while adding automated Utilization Ratio (UR) and Material Take-Off charts.
2. **Task 6: OsdagBridge Software Testing & Issue Reporting**:
   Conduct exhaustive, multi-tier functional testing across basic/additional inputs, custom materials, multi-run state persistence, and input/output dictionary validation. Identifies, logs, and provides code-level fixes for critical bugs on the upstream repository.

### The Engineering Synergy
Testing the software (Task 6) directly exercises the report generator (Task 3). Finding dictionary inconsistencies, missing load tables, and BOM calculation discrepancies provides immediate code-level root cause diagnoses that feed directly into fixing the reporting codebase and raising authoritative GitHub issues.

---

## 2. Task 3 Deep-Dive: LaTeX Report Generator Refactoring

### 2.1 The Problem
The current report generation in `core/reports/`:
- Has hardcoded styling parameters (font sizes, table colors, margins, padding) scattered across individual chapter files (`chap1.py` through `chap9.py`).
- Tables split across multiple pages without repeating headers (`\endhead`), causing confusion in multi-page structural data.
- Row heights and page margins cause text (such as Girder G4 entries) to bleed directly into the bottom footer box.
- Vehicle and footway live loads are merged in Chapter 3 without clear separation of units or IRC vehicle classes.
- Lacks visual data summaries for Demand/Capacity Utilization Ratios and Material Take-offs.

### 2.2 Functional Requirements for Task 3

| ID | Requirement | Architectural Solution | Target Files |
|---|---|---|---|
| **TR-3.1** | **Centralized Style & Theme System** | Create `styles.py` / `theme.py` as the single source of truth for color palettes, font definitions, table padding, margins, and header/footer configurations. | `core/reports/styles.py` |
| **TR-3.2** | **Repeated Table Headers Across Pages** | Implement PyLaTeX `LongTable` or standard LaTeX `longtable` environment with `\endfirsthead`, `\endhead`, `\endfoot`, and `\endlastfoot`. | `core/reports/report_utils.py`, `chap2.py` - `chap7.py` |
| **TR-3.3** | **Footer Overlap & Geometry Fixes** | Adjust geometry package parameters (`headsep`, `footskip`, `bottom=2.5cm`), row heights, and buffer thresholds (`\pagebreak`, `\keepwithnext`) to eliminate page bleed. | `core/reports/report_generator.py`, `templates/` |
| **TR-3.4** | **Load & Geometry Table Refactoring** | Separate Chapter 3 loads into distinct tables: (a) Vehicle Live Loads (IRC 70R, Class A, Class SV, etc.) with impact factors, braking, and centrifugal forces; (b) Footway/Pedestrian loads. | `core/reports/chap3.py` |
| **TR-3.5** | **Utilization Ratio (UR) Visualizations** | Programmatically generate bar charts for primary elements (Plate Girders, Concrete Deck Slab, Cross Bracing, End Diaphragms) with a red dashed threshold line at `UR = 1.0` embedded in Section 5.5. | `core/reports/chap5.py`, `core/reports/plot_utils.py` |
| **TR-3.6** | **Material Quantity Bar Charts** | Programmatically generate bar charts summarizing Bill of Materials from Chapter 7: Structural steel tonnage breakdown and Concrete volume ($m^3$) vs. Rebar weight (MT). | `core/reports/chap7.py`, `core/reports/plot_utils.py` |

---

## 3. Task 6 Deep-Dive: Software Testing & Issue Reporting

### 3.1 The Problem
Ensuring computational reliability, UI responsiveness, and data integrity in civil engineering software requires exhaustive testing across complex input matrices, sequential recalculations, and state persistence.

### 3.2 Functional Requirements for Task 6

| ID | Requirement | Methodology & Scope | Target Artifacts |
|---|---|---|---|
| **TR-6.1** | **Input & Customization Testing** | Execute test matrix across basic geometric inputs (spans 10m–30m, 2–6 girders, varying carriageway widths) and custom steel/concrete material properties. | Comprehensive test case matrix spreadsheet (`.xlsx`/`.csv`) |
| **TR-6.2** | **Multi-Run & State Persistence Testing** | Execute >= 3 consecutive sequential runs per session (Unlock ➔ Modify inputs ➔ Re-run Design). Check for stale data retention, memory accumulation, or GUI crashes. | Sequential multi-run test logs & screenshots |
| **TR-6.3** | **Input/Output Dictionary Audit** | Compare UI inputs vs. `self.input_dict` vs. `self.output_dict` vs. final design reports and display docks. Flag unmapped or mutated keys. | Side-by-side data dictionary audit table |
| **TR-6.4** | **Component Structural Coverage** | Audit all bridge elements: main plate girders, longitudinal/transverse stiffeners, cross bracings, end diaphragms, shear connectors, and RC deck slab. | Component-by-component coverage checklist |
| **TR-6.5** | **GitHub Issue Creation with Code Fixes** | Log formal, reproducible issues on `Nidhikhare12/OsdagBridge` with clear steps, traceback logs, dictionaries, and code-level patches identifying exact source files. | Live GitHub issue links with patch snippets |

---

## 4. System Architecture for Refactored Reporting (`core/reports/`)

```
src/osdagbridge/core/reports/
├── __init__.py
├── styles.py                 # [NEW] Single source of truth: colors, fonts, margins, table styles
├── plot_utils.py             # [NEW] Programmatic chart generator (UR ratio plots & Material Take-off)
├── report_generator.py       # [REFACTORED] Master orchestrator with enhanced geometry & pdflatex runner
├── report_utils.py           # [REFACTORED] LaTeX sanitization, longtable wrappers, unit formatting
├── chap1.py - chap9.py       # [REFACTORED] Modular chapter generators consuming styles.py
└── templates/                # Title page, header/footer definitions, macros
```

---

## 5. Phased Implementation Roadmap

```
Phase 1: Research, Baseline Generation & Test Matrix Design
  ├── Analyze existing report generation code & extract baseline output
  ├── Design comprehensive testing matrix (20+ test scenarios across spans & materials)
  └── Establish test-case logging format and dictionary auditing scripts

Phase 2: Centralized Style System & Table Infrastructure (Task 3)
  ├── Implement `styles.py` with global themes, colors, and margins
  ├── Refactor table generators to use `LongTable` with repeated headers (\endhead)
  └── Fix vertical spacing and footer bleed (Page 30+ margin adjustments)

Phase 3: Chart Visualization Engines (Task 3)
  ├── Build `plot_utils.py` for Utilization Ratio bar chart with 1.0 threshold
  ├── Build Material Quantity bar charts (tonnage & concrete volume vs rebar)
  └── Integrate plots dynamically into Section 5.5 and Chapter 7

Phase 4: Chapter Refactoring & Table Modernization (Task 3)
  ├── Refactor Chapter 3 (distinct vehicle live load vs footway load tables)
  ├── Clean up Chapters 1, 2, 4, 5, 6, 7, 8, 9 using centralized styling
  └── Generate Report_Before.pdf vs Report_After.pdf comparison

Phase 5: Exhaustive Software Testing & State Persistence (Task 6)
  ├── Run multi-run testing sequences (unlock -> modify -> recalculate)
  ├── Execute custom material edge cases and geometric extremes
  └── Perform comprehensive Input/Output dictionary verification

Phase 6: Code-Level Bug Diagnosis & GitHub Issue Logging (Task 6)
  ├── Identify root causes in OsdagBridge source files for identified bugs
  ├── Prepare formal GitHub issue writeups with screenshots, logs, and code patches
  └── Open/contribute issues on upstream Nidhikhare12/OsdagBridge

Phase 7: Packaging, Documentation & Video Demonstration
  ├── Compile comprehensive PDF Testing & Refactoring Report
  ├── Create demonstration screencast showcasing report changes and testing workflows
  └── Finalize ZIP submission archive
```

---

## 6. Deliverables Checklist

### Task 3 Deliverables:
- [ ] Refactored Python reporting codebase in `osdagbridge/src/osdagbridge/core/reports/`
- [ ] `Report_Before.pdf` (baseline report)
- [ ] `Report_After.pdf` (enhanced report showcasing all 6 requirements)
- [ ] Technical changes document detailing architectural and styling decisions

### Task 6 Deliverables:
- [ ] Comprehensive Software Testing Report (PDF)
- [ ] Test case log matrix (working vs failed scenarios, `.osi` files)
- [ ] Live GitHub issue links with suggested code-level fixes
- [ ] Demonstration screencast video (3–10 minutes)
