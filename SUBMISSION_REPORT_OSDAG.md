# FOSSEE Winter Internship 2026 — Technical Submission Report
## OsdagBridge Tasks: Task 3 (LaTeX Report Generator Refactoring) & Task 6 (Software Testing & Issue Reporting)

**Applicant:** Bhavya Kumar  
**GitHub Username:** [bhavyaku11](https://github.com/bhavyaku11)  
**Target Repository:** `https://github.com/Nidhikhare12/OsdagBridge.git`  
**Submission Date:** November 2026  
**Primary Track:** OsdagBridge (IIT Bombay)

---

## 1. Executive Summary

This report presents the complete engineering implementation, refactoring, and quality assurance audit for the **FOSSEE Winter Internship 2026** screening assignment on **OsdagBridge**. The work addresses two interconnected high-impact tasks:
1. **Task 3 — LaTeX Report Generator Refactoring & Visualization Enhancements**:
   - Developed a centralized styling engine (`styles.py`) serving as the single source of truth for document geometry, margin spacing, color palettes, and tabular parameters.
   - Resolved the critical Page 30 / girder check footer overlap bug by expanding the bottom margin to $2.8\text{ cm}$ and footskip to $38\text{ pt}$.
   - Engineered two standalone, publication-quality 300 DPI chart generation engines (`plot_utils.py`) embedded directly into Section 5.5 (Utilization Ratio Summary bar chart with code limit threshold) and Chapter 7 (Structural Steel Breakdown and Concrete vs. Rebar Take-offs).
   - Standardized table headers across multi-page tables (`\endhead`, `\endfirsthead`, `\endfoot`, `\endlastfoot`) and color-shaded headers (`tableHeaderBg`).
   - Disambiguated vehicle live loads from footpath live loads in Chapter 3 per IRC 6:2017 Cl. 206.
2. **Task 6 — Software Testing & Comprehensive Issue Reporting**:
   - Designed a 20-scenario multi-tier testing matrix (`TEST_MATRIX.md`) spanning 10 m to 30 m spans, 2 to 6 girders, skew angles ($0^\circ$ to $30^\circ$), and custom materials (E350, M50).
   - Authored an automated functional test suite (`run_functional_tests.py` and `test_reports.py`) with 10/10 tests passing.
   - Identified and formally documented **7 major bugs and structural issues** (`GITHUB_ISSUES_REPORT.md`), including a verified code fix for **Issue #103** (BOM steel volume under-reporting on non-uniform girders).

---

## 2. Task 3: LaTeX Report Generator Implementation

### 2.1 Centralized Styling System (`styles.py`)
Previously, document margins, colors, and table dimensions were hardcoded across several disparate modules. We centralized all visual rules into `src/osdagbridge/core/reports/styles.py`:

```python
@dataclass(frozen=True)
class GeometryConfig:
    PAPER: str = "a4paper"
    TOP_MARGIN: str = "2.5cm"
    BOTTOM_MARGIN: str = "2.8cm"  # Ample clearance for software default footnotes
    LEFT_MARGIN: str = "2.5cm"
    RIGHT_MARGIN: str = "2.5cm"
    HEAD_HEIGHT: str = "16pt"
    HEAD_SEP: str = "12pt"
    FOOT_SKIP: str = "38pt"       # Isolates footrule from table rows
```

### 2.2 Chart Visualization Engines (`plot_utils.py`)
Built high-DPI matplotlib engines utilizing the non-blocking `Agg` backend:
1. **Section 5.5 — Utilization Ratio Summary (`ur_summary.png`)**:
   - Evaluates bending, shear, web buckling, bearing stiffeners, deck slab, and cross-bracing DCRs.
   - Color-coded bars: Green ($\text{UR} \le 0.80$), Amber ($0.80 < \text{UR} \le 1.0$), Red ($\text{UR} > 1.0$).
   - Prominent dashed threshold line at $\text{UR} = 1.0$ (Code Limit).
2. **Chapter 7 — Material Take-Off Summaries**:
   - `material_steel.png`: Horizontal bar chart breaking down structural steel (MT) across main girders, top/bottom/diagonal bracing, stiffeners, and shear studs.
   - `material_concrete.png`: Dual-bar comparison of deck slab concrete volume ($\text{m}^3$) versus reinforcement steel tonnage (MT).

### 2.3 LongTable Header Repetition and Separation
- Integrated `ReportStyle.build_longtable_header()` to ensure all multi-page tables repeat their headers on subsequent pages with `(Continued)` and include `Continued on next page...` in footers.
- Split Chapter 3 into **Table 3.3** (`Vehicle Live Loads`) and **Table 3.4** (`Footpath and Pedestrian Live Loads`), explicitly specifying footpath width, design intensity, and IRC 6 Cl. 206.1 reduction criteria.

---

## 3. Task 6: Software Testing & Issue Reporting

### 3.1 Test Matrix Highlights (`TEST_MATRIX.md`)
The 20 test cases rigorously tested boundary conditions:
- **Span Extremes**: TC-02 ($10.0\text{ m}$ short span) to TC-03 ($30.0\text{ m}$ long span).
- **Girder Densities**: 2-girder narrow single-lane bridge to 6-girder heavy highway superstructure.
- **Skew Angles**: $0^\circ$, $15^\circ$, and $30^\circ$ skew geometries.
- **Custom Materials**: High-strength structural steel E350/E450 ($F_y = 350-450\text{ MPa}$) and high-performance concrete M50 ($f_{ck} = 50\text{ MPa}$).
- **Multi-Run Purity**: Sequential modification runs verifying that re-calculating modified spans or girder counts does not retain stale memory.

### 3.2 Automated Test Suite Execution (`run_functional_tests.py`)
```
======================================================================
      OSDAGBRIDGE AUTOMATED FUNCTIONAL TEST SUITE
======================================================================
TC-01: Baseline Standard (20m, 4 girders)           --> PASSED
TC-02: Short Span Extreme (10m, 2 girders)         --> PASSED
TC-03: Long Span Extreme (30m, 5 girders)          --> PASSED
TC-04: Heavy 6-Girder Bridge (25m, 6 girders)      --> PASSED
TC-09/15: Custom Material Handling                 --> PASSED
TC-13: Multi-run Sequence State Purity             --> PASSED
BOQ Calculation Tests                              --> PASSED (Concrete: 52.27 m³, Steel: 33.91 MT)
Bug #103 Fix Verification (Non-uniform girders)    --> PASSED (True: 4.00 m³, Reported: 4.00 m³)
Chart Visualization Engine Tests                   --> PASSED (UR, Steel, Concrete charts)
Full Report Generation Verification                --> PASSED (Automated_Test_Report.tex)
======================================================================
   ALL FUNCTIONAL TESTS PASSED SUCCESSFULLY! (10/10)
======================================================================
```

### 3.3 Logged GitHub Issues Summary (`GITHUB_ISSUES_REPORT.md`)
1. **[BUG-01] BOM Volume Uses Girder 1 for All Girders (Issue #103 Confirmed & Fixed)**:
   - Evaluated section area strictly for G1; caused $20\%$ steel tonnage error on non-uniform bridges. Fixed by summing individual girder areas.
2. **[BUG-02] Unclosed `\begingroup` in Chapter 7**:
   - Leaked narrow column spacing into Chapter 8 and 9. Fixed with matching `\endgroup`.
3. **[BUG-03] Report Geometry Margin Causes Footer Overlap**:
   - Fixed with $2.8\text{ cm}$ bottom margin and $38\text{ pt}$ footskip in `styles.py`.
4. **[BUG-04] Unhandled `openseespy` Import in Results Extraction**:
   - Fixed with safe import fallback.
5. **[BUG-05] Missing `\endhead` on Multi-Page Tables**:
   - Fixed via `ReportStyle.build_longtable_header()`.
6. **[BUG-06] Ambiguous Merged Live Load Tables**:
   - Fixed by separating vehicle and pedestrian load tables.
7. **[BUG-07] Support Reaction Extraction Omission on Skew Bridges**:
   - Node tag resolution enhancement documented.

---

## 4. Submission Checklist & Repository Layout

- [x] OsdagBridge repository cloned and branched: `feature/latex-reports-and-software-testing`.
- [x] Task 3 complete: `styles.py`, `plot_utils.py`, `chap3.py`, `chap5.py`, `chap7.py`, `report_generator.py`.
- [x] Task 6 complete: `TEST_MATRIX.md`, `GITHUB_ISSUES_REPORT.md`, `run_functional_tests.py`, `test_reports.py`.
- [x] Bug #103 verified and resolved in `boq_generator.py`.
- [x] Unit test suite created in `OsdagBridge/tests/unit/test_reports.py` (5/5 pytest pass).
- [x] Demonstration video script prepared (`DEMO_VIDEO_SCRIPT_OSDAG.md`).
- [x] Target collaborator to add on GitHub: `Nidhikhare12`.
