# OsdagBridge User Guide

Welcome to **OsdagBridge**, the open-source engineering suite for the automated modeling, structural analysis, design verification, and report generation of composite steel-concrete highway bridges.

---

## 1. Quickstart

### 1.1 Installation
Clone the repository and install with `pip`:

```bash
git clone https://github.com/bhavyaku11/Osdag-Bridge.git
cd Osdag-Bridge
pip install -e .
```

Verify your installation:

```bash
osdagbridge version
```

---

## 2. Command-Line Interface (CLI)

OsdagBridge includes a command-line interface for automating analysis, material estimation, and report drafting.

### 2.1 Model Analysis (`analyze`)
Validates the geometric parameters, material classifications, and load cases of a bridge definition file:

```bash
osdagbridge analyze resources/sample_bridge_model.json
```

Output:
```text
========================================================
      OsdagBridge — Structural Model Verification
========================================================

Loaded bridge model: resources/sample_bridge_model.json
  - Span Length: 24.0 m
  - Number of Girders: 4
  - Total Input Parameters: 24

Model geometry validated successfully.
```

### 2.2 Material Take-Off & BOQ (`boq`)
Computes component volumes, unit weights, and total tonnage for the bridge superstructure:

```bash
osdagbridge boq resources/sample_bridge_model.json
```

Output:
```text
=========================================================================
           OsdagBridge — Material Take-Off & BOQ Estimator
=========================================================================

Bridge Geometry: Span = 24.0 m, Girders = 4

ITEM / COMPONENT                 QTY      VOL (Cu.m)     TOTAL WT (MT) 
------------------------------------------------------------------------
Main Structural Steel Girders    4        4.61           36.17         
Reinforced Concrete Deck Slab    1        54.38          135.96        
Deck Slab Reinforcement Steel    1        0.83           6.53          
Shear Stud Connectors            N.A.     N.A.           N.A.          
Cross-Bracing (Top Chord)        N.A.     N.A.           N.A.          
Cross-Bracing (Bottom Chord)     N.A.     N.A.           N.A.          
Cross-Bracing (Diagonals)        N.A.     N.A.           N.A.          
RCC Crash Barrier                2        8.64           21.60         
------------------------------------------------------------------------

All component quantities computed with zero validation warnings.
```

### 2.3 LaTeX Design Report Generation (`report`)
Generates a complete 7-chapter design report adhering to IRC 22:2015 and IS 800:2007 formatting:

```bash
osdagbridge report resources/sample_bridge_model.json --output-dir ./report_output
```

This generates:
- `./report_output/Bridge_Design_Report.tex`: Complete LaTeX source document.
- `./report_output/images/ur_summary.png`: Demand-to-Capacity ratio summary chart.
- `./report_output/images/material_steel.png`: Structural steel component breakdown chart.
- `./report_output/images/material_concrete.png`: Concrete volume vs. rebar tonnage chart.

If a local LaTeX distribution (`pdflatex`) is installed, the engine automatically compiles the `.tex` file into a PDF.

---

## 3. Bridge Input Model Format

Bridge models are specified as JSON files with canonical dot-notation keys:

```json
{
  "geometry.span": 24.0,
  "typical_section.no_of_girders": 4,
  "typical_section.girder_spacing": 2.6,
  "typical_section.deck_overhang": 1.25,
  "typical_section.deck_thickness": 220,
  "typical_section.overall_bridge_width": 10.3,
  "typical_section.crash_barrier.area": 180000.0,
  "design_mode": "Optimized",
  "material_density.girder": 78.5,
  "material_density.deck": 25.0,
  "live_load.irc_class_a": true,
  "live_load.irc_70r_wheeled": true,
  "wearing_coat.material": "Bituminous Concrete",
  "wearing_coat.thickness": "75 mm",
  "wind_speed": 39.0,
  "seismic_zone": "II",
  "member_properties.girder_details.section_properties.area": 0.048,
  "member_properties.girder_details.section_properties.mass": 376.8
}
```

### 3.1 Non-Uniform Girder Configurations
For non-uniform bridges where interior and exterior girders have different dimensions, specify per-girder sections:

```json
{
  "geometry.span": 24.0,
  "typical_section.no_of_girders": 4,
  "member_properties.girder_details.section_properties.area.G1.M1": 0.040,
  "member_properties.girder_details.section_properties.area.G2.M1": 0.060,
  "member_properties.girder_details.section_properties.area.G3.M1": 0.060,
  "member_properties.girder_details.section_properties.area.G4.M1": 0.040
}
```

Every girder in the bridge must be defined. If any girder is missing, the BOQ estimator flags a validation warning and avoids fabricating estimates.

### 3.2 Material Assumptions Overrides
To customize material density or rebar estimation factors:

```json
{
  "design_options.material_assumptions": {
    "concrete_density_t_m3": 2.4,
    "rebar_rate_kg_m3": 110.0,
    "steel_density_kg_m3": 7850.0
  }
}
```

---

## 4. Frequently Asked Questions (FAQ)

**Q: Do I need LaTeX installed to use OsdagBridge?**  
A: No. OsdagBridge generates the complete `.tex` source and high-resolution chart images without needing any LaTeX tools installed. A LaTeX compiler (`pdflatex`) is only needed if you wish to compile the `.tex` file directly to `.pdf`.

**Q: How do I compile the generated `.tex` report to `.pdf` manually?**  
A: Run `pdflatex` twice from the directory containing the `.tex` file:
```bash
pdflatex Bridge_Design_Report.tex
pdflatex Bridge_Design_Report.tex
```

**Q: How does OsdagBridge handle incomplete bridge data?**  
A: OsdagBridge follows a strict zero-fabrication engineering policy. If data for a calculation is missing, the tool reports `"N.A."` with warning diagnostics, rather than fabricating placeholder numbers.
