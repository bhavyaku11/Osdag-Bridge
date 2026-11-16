# OsdagBridge

[![OsdagBridge CI](https://github.com/bhavyaku11/Osdag-Bridge/actions/workflows/ci.yml/badge.svg)](https://github.com/bhavyaku11/Osdag-Bridge/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

OsdagBridge is a modular, shared-core software engineering suite for the automated modeling, structural analysis, limit state design checking, material estimation, and LaTeX design reporting of steel-concrete composite highway bridges within the **Osdag (Open Steel Design and Graphics)** ecosystem at **IIT Bombay**.

> **Upstream Task Origin**: This repository is developed as part of the FOSSEE Osdag Winter Internship 2026, forked from the upstream target repository [`Nidhikhare12/OsdagBridge`](https://github.com/Nidhikhare12/OsdagBridge).  
> **Active Contribution Focus**: **Task 3** (LaTeX Report Generator Refactoring) and **Task 6** (Software Testing & Issue Reporting).

---

## Key Capabilities & Contributions

### 1. Task 3: Centralized LaTeX Report Generator
- **Consistent Visual Styling**: Centralized geometry management (`ReportStyle`, `GeometryConfig`) with top margin 2.5 cm, bottom margin 2.8 cm, and footskip 38 pt to eliminate page-footer text overlap.
- **Repeated LongTable Headers**: Multi-page tables implemented using `\begin{longtable}` with `\endfirsthead`, `\endhead`, `\endfoot`, and `\endlastfoot`, ensuring column titles repeat across page breaks.
- **Strict Zero-Fabrication Chart Engines**: Visual charts (`plot_utils.py`) for Demand-to-Capacity Ratios (`ur_summary.png`) and Material Take-Off (`material_steel.png`, `material_concrete.png`) rendered at 300 DPI without placeholder or fabricated data.
- **7-Chapter Modular Assembly**: Covers project information, input geometry, load calculations (IRC 6), analysis results, design checks (IRC 22 / IS 800), drawings, and Bill of Materials (BOM).

### 2. Task 6: Software Testing & Upstream Issue #103 Fix
- **Issue #103 Resolution (Non-Uniform Girder Quantities)**: Fixed the structural steel volume and mass calculation in `boq_generator.py`. In bridges with varying interior and exterior girders, each girder is calculated independently. Missing girders in per-girder schemes are caught with explicit `KeyError` exceptions rather than silently duplicating Girder 1.
- **Strict Numerical Validation & Mass Integrity**: Added validation rejecting non-finite numbers (NaN, inf) and fractional girder counts (e.g., 4.8), coupled with cross-validation of girder mass against section area $\times \rho_{\text{steel}}$ to flag physical discrepancies (>15%).
- **Comprehensive Test Suite**:
  - **Unit & Integration Suite**: 30 automated tests covering analysis math, limit state DCR evaluation, JSON I/O, CLI dispatch, partial-quantity chart warnings, mass consistency checks, and report compilation.
  - **25-Scenario Functional Test Matrix (`run_functional_tests.py`)**: Covers span variations (10m to 30m), 2 to 6 girders, high skew angles (up to 30°), custom steel/concrete grades (E350, E450, M50), multi-run memory isolation, and live loading cases. All 25 scenarios pass cleanly using isolated temporary directories.

---

## Installation

### Prerequisites
- Python >= 3.11
- Standard build tools (`pip`, `setuptools`, `wheel`)

```bash
# Clone the repository
git clone https://github.com/bhavyaku11/Osdag-Bridge.git
cd Osdag-Bridge

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

---

## Command-Line Interface (CLI)

OsdagBridge includes an integrated CLI:

```bash
# Display version and build information
osdagbridge version

# Validate bridge model input geometry
osdagbridge analyze resources/sample_bridge_model.json

# Compute Bill of Quantities (BOQ) material take-off
osdagbridge boq resources/sample_bridge_model.json

# Generate publication-quality 7-chapter LaTeX report and charts
osdagbridge report resources/sample_bridge_model.json --output-dir ./report_out
```

---

## Testing & Quality Assurance

### Run Unit and Integration Tests (pytest)
```bash
pytest -v
```

### Run the 25-Scenario Functional Test Matrix
```bash
python3 tests/run_functional_tests.py
```

### Continuous Integration
Continuous integration runs on every push and pull request via GitHub Actions (`.github/workflows/ci.yml`), testing on Python 3.11 and 3.12.

---

## Project Structure

```
OsdagBridge/
├── .github/workflows/ci.yml     # Automated GitHub Actions CI workflow
├── src/
│   └── osdagbridge/
│       ├── cli/                 # CLI entry point, argument parsing, commands
│       │   ├── __main__.py
│       │   └── commands.py
│       ├── core/                # Core domain packages
│       │   ├── boq/             # Bill of Quantities generator & Issue #103 fix
│       │   ├── bridge_types/    # Plate girder and box girder models
│       │   │   └── plate_girder/ # Analyser, designer, sizing, plategirderbridge
│       │   ├── loads/           # Vehicle definitions and IRC 6 placement
│       │   ├── reports/         # 7-chapter LaTeX generator, styles, plot_utils
│       │   ├── solvers/         # OpenSeesPy & ospgrillage adapters
│       │   └── utils/           # Canonical keys and unit definitions
│       └── desktop/             # Desktop GUI interface (PySide)
├── tests/
│   ├── unit/                    # Unit tests for analyser, designer, io, reports
│   ├── integration/             # Integration tests for API and CLI
│   ├── run_functional_tests.py  # 25-scenario automated functional test matrix runner
│   └── TEST_MATRIX.md           # Formal specification of the 20 testing scenarios
├── resources/                   # Sample models and bridge input templates
├── docs/                        # Architecture, Developer, User Guides, and PRDs
└── pyproject.toml               # Package specifications and pytest configurations
```

---

## License

This project is licensed under the MIT License. See `LICENSE` for details.
