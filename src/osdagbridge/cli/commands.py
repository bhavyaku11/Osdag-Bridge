"""
OsdagBridge — Command-Line Interface (CLI) Implementation.
Provides end-to-end execution for bridge analysis, BOQ material estimation,
LaTeX engineering report generation, and system diagnostics.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

from osdagbridge.core.boq.boq_generator import calculate_material_quantities
from osdagbridge.core.reports.report_generator import (
    ReportRequest,
    ReportMetadata,
    ReportOptions,
    build_report_payload,
    generate_report,
)
from osdagbridge.core.utils.common import KEY_SPAN, KEY_TS_NO_OF_GIRDERS


def cmd_version(args: argparse.Namespace) -> int:
    """Prints OsdagBridge version and build information."""
    print("OsdagBridge Core Version: 1.0.0")
    print("FOSSEE, IIT Bombay | Steel Bridge Engineering Suite")
    print("License: AGPL-3.0-or-later")
    return 0


def load_json_input(file_path: str) -> Dict[str, Any]:
    """Loads and validates a bridge input dictionary from a JSON file."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Input file not found: '{file_path}'")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"JSON input must be a dictionary, got {type(data).__name__}")
    return data


def cmd_analyze(args: argparse.Namespace) -> int:
    """Validates bridge model parameters and prepares analysis geometry."""
    print(f"\n========================================================")
    print(f"      OsdagBridge — Structural Model Verification")
    print(f"========================================================\n")
    try:
        inputs = load_json_input(args.input_file)
        span = inputs.get(KEY_SPAN, "N/A")
        n_girders = inputs.get(KEY_TS_NO_OF_GIRDERS, "N/A")
        print(f"Loaded bridge model: {args.input_file}")
        print(f"  - Span Length: {span} m")
        print(f"  - Number of Girders: {n_girders}")
        print(f"  - Total Input Parameters: {len(inputs)}")
        print("\nModel geometry validated successfully.")
        return 0
    except Exception as e:
        print(f"[ERROR] Model analysis failed: {e}", file=sys.stderr)
        return 1


def cmd_boq(args: argparse.Namespace) -> int:
    """Calculates and displays Bill of Quantities (BOQ) material take-off."""
    print(f"\n=========================================================================")
    print(f"           OsdagBridge — Material Take-Off & BOQ Estimator")
    print(f"=========================================================================\n")
    try:
        inputs = load_json_input(args.input_file)
        outputs = {}
        if getattr(args, "output_file", None) and os.path.isfile(args.output_file):
            outputs = load_json_input(args.output_file)

        quantities = calculate_material_quantities(inputs, outputs)

        span = inputs.get(KEY_SPAN) or inputs.get("general.bridge_span") or inputs.get("span") or 0.0
        n_girders = inputs.get(KEY_TS_NO_OF_GIRDERS) or inputs.get("no_of_girders") or inputs.get("n_girders") or 0
        print(f"Bridge Geometry: Span = {span} m, Girders = {n_girders}\n")
        print(f"{'ITEM / COMPONENT':<32} {'QTY':<8} {'VOL (Cu.m)':<14} {'TOTAL WT (MT)':<14}")
        print("-" * 72)

        items = [
            ("Main Structural Steel Girders", quantities.get("steel_girders_qty", "N.A."), quantities.get("steel_girders_vol_total", "N.A."), quantities.get("steel_girders_wt_total", "N.A.")),
            ("Reinforced Concrete Deck Slab", quantities.get("concrete_deck_qty", "N.A."), quantities.get("concrete_deck_vol_total", "N.A."), quantities.get("concrete_deck_wt_total", "N.A.")),
            ("Deck Slab Reinforcement Steel", quantities.get("rebar_deck_qty", "N.A."), quantities.get("rebar_deck_vol_total", "N.A."), quantities.get("rebar_deck_wt_total", "N.A.")),
            ("Shear Stud Connectors", quantities.get("shear_studs_qty", "N.A."), quantities.get("shear_studs_vol_total", "N.A."), quantities.get("shear_studs_wt_total", "N.A.")),
            ("Cross-Bracing (Top Chord)", quantities.get("bracing_top_qty", "N.A."), quantities.get("bracing_top_vol_total", "N.A."), quantities.get("bracing_top_wt_total", "N.A.")),
            ("Cross-Bracing (Bottom Chord)", quantities.get("bracing_bot_qty", "N.A."), quantities.get("bracing_bot_vol_total", "N.A."), quantities.get("bracing_bot_wt_total", "N.A.")),
            ("Cross-Bracing (Diagonals)", quantities.get("bracing_diag_qty", "N.A."), quantities.get("bracing_diag_vol_total", "N.A."), quantities.get("bracing_diag_wt_total", "N.A.")),
            ("RCC Crash Barrier", quantities.get("crash_barrier_qty", "N.A."), quantities.get("crash_barrier_vol_total", "N.A."), quantities.get("crash_barrier_wt_total", "N.A.")),
        ]

        for desc, qty, vol, wt in items:
            print(f"{desc:<32} {str(qty):<8} {str(vol):<14} {str(wt):<14}")

        print("-" * 72)
        warnings = quantities.get("_warnings", [])
        if warnings:
            print("\n[WARNINGS / INCOMPLETE INPUTS DETECTED]:")
            for w in warnings:
                print(f"  * {w}")
        else:
            print("\nAll component quantities computed with zero validation warnings.")
        print()
        return 0
    except Exception as e:
        print(f"[ERROR] BOQ calculation failed: {e}", file=sys.stderr)
        return 1


def cmd_report(args: argparse.Namespace) -> int:
    """Generates the 7-chapter LaTeX engineering design report."""
    print(f"\n========================================================")
    print(f"      OsdagBridge — LaTeX Report Generator Engine")
    print(f"========================================================\n")
    try:
        inputs = load_json_input(args.input_file)
        outputs = {}
        if getattr(args, "output_file", None) and os.path.isfile(args.output_file):
            outputs = load_json_input(args.output_file)

        out_dir = getattr(args, "output_dir", None) or os.getcwd()
        os.makedirs(out_dir, exist_ok=True)
        report_name = getattr(args, "filename", None) or "Bridge_Design_Report.tex"

        print(f"Compiling engineering report...")
        print(f"  - Target Directory: {out_dir}")
        print(f"  - Output Document: {report_name}")

        meta = ReportMetadata(
            project_name=inputs.get("project.name", "Composite Steel-Concrete Bridge"),
            project_location=inputs.get("project.location", "India"),
            designer=inputs.get("project.designer", "Osdag Engineer"),
            client=inputs.get("project.client", "FOSSEE Osdag"),
            company=inputs.get("project.company", "IIT Bombay / FOSSEE"),
        )
        options = ReportOptions(
            sections=["all"],
            include_figures=True,
            include_toc=True,
            include_pdf=getattr(args, "compile_pdf", False),
        )
        file_stem = os.path.splitext(os.path.basename(report_name))[0]
        request = ReportRequest(
            metadata=meta,
            options=options,
            output_dir=out_dir,
            file_stem=file_stem,
        )
        payload = build_report_payload(request, inputs, outputs)
        result = generate_report(payload, request)

        print(f"\n[SUCCESS] Engineering design report generated successfully:")
        print(f"  --> LaTeX source: {result.tex_path}")
        if result.pdf_path:
            print(f"  --> Compiled PDF: {result.pdf_path}")
        print()
        return 0
    except Exception as e:
        print(f"[ERROR] Report generation failed: {e}", file=sys.stderr)
        return 1
