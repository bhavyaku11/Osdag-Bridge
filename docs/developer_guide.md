# OsdagBridge Developer Guide

This guide describes how to set up a development environment, run test suites, contribute code, and maintain software quality across the **OsdagBridge** repository.

---

## 1. Prerequisites & Environment Setup

### 1.1 Requirements
- **Python**: 3.11, 3.12, 3.13, or 3.14
- **Operating Systems**: Linux (Ubuntu 20.04+), macOS (12+), Windows (10/11)
- **Optional LaTeX Compiler** (for PDF output): `pdflatex` (TeX Live or MacTeX) or `latexmk`. The LaTeX `.tex` generation itself requires no external tools.

### 1.2 Development Installation

Clone your fork of OsdagBridge and set up a virtual environment:

```bash
git clone https://github.com/bhavyaku11/Osdag-Bridge.git
cd Osdag-Bridge

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies in editable mode with development/test extras
pip install --upgrade pip setuptools wheel
pip install -e ".[dev]"
```

Verify that the CLI entry points are accessible:

```bash
osdagbridge version
# Or run as a module:
python3 -m osdagbridge.cli version
```

---

## 2. Repository Layout

```
OsdagBridge/
├── src/
│   └── osdagbridge/
│       ├── cli/                 # CLI entry point, argument parsing, commands
│       │   ├── __main__.py
│       │   └── commands.py
│       ├── core/                # Core domain and computational packages
│       │   ├── boq/             # Bill of Quantities generator & Issue #103 resolution
│       │   ├── bridge_types/    # Plate girder and box girder bridge models
│       │   │   └── plate_girder/ # Analyser, designer, initial sizing, plategirderbridge
│       │   ├── loads/           # Vehicle definitions and IRC 6 placement
│       │   ├── reports/         # 7-chapter LaTeX generator, styles, plot_utils
│       │   ├── solvers/         # OpenSeesPy & ospgrillage adapters
│       │   └── utils/           # Canonical dot-notation keys, unit definitions
│       └── desktop/             # Desktop GUI application (PyQt)
├── tests/
│   ├── unit/                    # Fast isolated unit tests (analyser, designer, io, reports)
│   ├── integration/             # Component integration tests (api, cli)
│   ├── run_functional_tests.py  # 25-scenario automated functional test matrix runner
│   └── TEST_MATRIX.md           # Formal specification of the 20 testing scenarios
├── resources/                   # Sample models and bridge configurations
├── docs/                        # Architecture, Developer, User Guides, and PRDs
└── pyproject.toml               # Package specifications and pytest configurations
```

---

## 3. Testing Workflow

OsdagBridge employs a multi-tiered automated verification suite. All tests must pass before submitting code changes.

### 3.1 Running Unit & Integration Tests (pytest)
Pytest is configured via `pyproject.toml` with automatic Python source path discovery:

```bash
pytest -v
```

To run a specific test suite:

```bash
pytest tests/unit/test_reports.py -v
pytest tests/unit/test_designer.py -v
pytest tests/integration/test_cli_plate_girder.py -v
```

### 3.2 Running the Full 25-Scenario Functional Test Matrix
The functional runner verifies end-to-end model creation, parameter variation, custom material normalization, multi-run state purity, Issue #103 regression fixes, zero-fabrication plotting, and full LaTeX compilation:

```bash
python3 tests/run_functional_tests.py
```

Expected output:
```
======================================================================
   ALL FUNCTIONAL TEST MATRIX SCENARIOS PASSED SUCCESSFULLY! (25/25)
======================================================================
```

---

## 4. Engineering Standards & Coding Guidelines

### 4.1 Zero-Fabrication Guarantee
Under no circumstances should calculation functions fall back to fabricated numbers (e.g. inserting `0.76` for uncalculated bending moments or `45.2` MT for missing girders). If data is absent:
- Return `None` for optional chart visuals.
- Output `"N.A."` in tables.
- Append a clear diagnostic warning to `_warnings`.

### 4.2 Handling Per-Girder Variations (Issue #103)
When reading girder properties, always use `resolve_girder_value()`:
- If a dataset defines per-girder keys (e.g. `.G1.M1`, `.G2.M1`), each girder $i$ must be resolved explicitly.
- If girder $i$ is missing from a per-girder dataset, do **not** fall back to `.G1` or any other girder. Raise a `KeyError` so the validation system can inform the user.
- Legacy scalar keys (e.g. `member_properties.girder_details.section_properties.area`) are only used when no per-girder keys are defined in the dataset.

### 4.3 LaTeX Formatting Standards
- Long tables must use `\begin{longtable}` with `\endfirsthead`, `\endhead`, `\endfoot`, and `\endlastfoot`.
- Table header background color is styled using `\rowcolor{tableHeaderBg}`.
- Page margins: top 2.5 cm, bottom 2.8 cm, footskip 38 pt to prevent text overlapping page footers.

---

## 5. Contribution & Git Workflow

1. Fork the upstream target repository `Nidhikhare12/OsdagBridge`.
2. Create a descriptive feature branch:
   ```bash
   git checkout -b feature/latex-reports-and-software-testing
   ```
3. Commit your changes with clear, structured messages.
4. Run all test suites:
   ```bash
   pytest -v && python3 tests/run_functional_tests.py
   ```
5. Push to your fork and submit a Pull Request.
