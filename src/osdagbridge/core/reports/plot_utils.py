"""
OsdagBridge — Chart Visualization Engines for Engineering Reports.
Generates publication-quality charts (300 DPI) for:
  1. Section 5.5: Utilization Ratio (UR) Summary Bar Chart with Code Limit threshold
  2. Chapter 7: Structural Steel Breakdown & Concrete vs Rebar Quantities

Integrity Guarantee:
  Never manufactures or substitutes illustrative placeholder numbers into actual
  engineering reports. Unavailable calculations are excluded or explicitly noted.
  Partial quantities display explicit warning annotations and non-fabrication disclaimers.
  Illustrative demonstration data is strictly isolated behind `demo_mode=True`.
"""

import os
import math
import logging
from typing import Dict, Any, Tuple, Optional, List

# Use Agg backend for headless environments
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.patches import Patch

from osdagbridge.core.reports.styles import ColorPalette

logger = logging.getLogger(__name__)


def _parse_float(val: Any, default: Optional[float] = None) -> Optional[float]:
    """Safely parse a finite numerical value from dicts or formulas."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val) if math.isfinite(val) else default
    try:
        s = str(val).strip()
        if s.upper() in ("N.A.", "N/A", "NONE", "", "INCOMPLETE", "NAN", "INF", "-INF"):
            return default
        for unit in ("MT", "Cu.m", "m^3", "kN", "$", "m", "kg"):
            s = s.replace(unit, "")
        f = float(s.strip())
        return f if math.isfinite(f) else default
    except (ValueError, TypeError):
        return default


def generate_ur_summary_chart(
    output_dict: Dict[str, Any],
    output_dir: str,
    filename: str = "ur_summary.png",
    demo_mode: bool = False,
    diagnostics: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Generate an engineering Utilization Ratio (UR) summary bar chart for Chapter 5 (Section 5.5).

    Args:
        output_dict: Dictionary containing bridge calculation results.
        output_dir: Target directory to save the rendered PNG image.
        filename: Destination filename (default: 'ur_summary.png').
        demo_mode: When True, uses illustrative benchmark values if output_dict is empty,
                   watermarking the title as illustrative demonstration data.
                   Defaults to False (strict engineering integrity).
        diagnostics: Optional dictionary to collect generation status, warnings, and errors.

    Returns:
        Path to the generated image file, or None if no valid calculation results are available.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, filename)

        # Standard check items to extract from output_dict
        check_specs = [
            ("Girder Bending Moment (IS 800 Cl. 8.2)", [
                "steeldesign.details.bending.utilization_ratio",
                "steeldesign.girder.bending_ur",
                "girder_bending_ur",
                "bending_ur"
            ], 0.76),
            ("Girder Shear Capacity (IS 800 Cl. 8.4)", [
                "steeldesign.details.shear.utilization_ratio",
                "steeldesign.girder.shear_ur",
                "girder_shear_ur",
                "shear_ur"
            ], 0.62),
            ("Web Buckling / Resistance (IS 800 Cl. 8.4.2.2)", [
                "steeldesign.details.buckling.utilization_ratio",
                "steeldesign.girder.web_buckling_ur",
                "web_buckling_ur"
            ], 0.68),
            ("Bearing Stiffener Capacity (IS 800 Cl. 8.7.4)", [
                "steeldesign.details.stiffener.bearing_ur",
                "stiffener_bearing_ur"
            ], 0.54),
            ("Intermediate Transverse Stiffener (IS 800 Cl. 8.7.2)", [
                "steeldesign.details.stiffener.intermediate_ur",
                "stiffener_intermediate_ur"
            ], 0.48),
            ("Shear Connector Capacity (IRC 22 Cl. 508)", [
                "deckslab.shear_connector_ur",
                "shear_connector_ur"
            ], 0.71),
            ("Deck Slab Transverse Bending (IRC 112)", [
                "deckslab.transverse.bending_ur",
                "deck_slab_transverse_ur"
            ], 0.81),
            ("Deck Slab Longitudinal Bending (IRC 112)", [
                "deckslab.longitudinal.bending_ur",
                "deck_slab_longitudinal_ur"
            ], 0.65),
            ("Cross-Bracing Top Chord (IS 800 Cl. 7.1)", [
                "crossbracing.top_chord_ur",
                "cb_top_chord_ur"
            ], 0.58),
            ("Cross-Bracing Diagonals (IS 800 Cl. 7.1)", [
                "crossbracing.diagonal_ur",
                "cb_diagonal_ur"
            ], 0.72),
            ("End Diaphragm Diagonals (IS 800 Cl. 7.1)", [
                "enddiaphragm.diagonal_ur",
                "ed_diagonal_ur"
            ], 0.69),
            ("Overall Superstructure Governing Check", [
                "governing_ur",
                "overall_ur",
                "dcr_max"
            ], 0.81),
        ]

        labels = []
        urs = []
        missing_checks = []

        for name, keys, fallback in check_specs:
            val = None
            for k in keys:
                if k in output_dict and output_dict[k] not in ("", None):
                    val = _parse_float(output_dict[k], None)
                    if val is not None:
                        break

            # Strictly avoid fabricating engineering numbers unless explicitly in demo_mode
            if val is not None and val >= 0.0:
                labels.append(name)
                urs.append(val)
            elif demo_mode:
                labels.append(f"{name} [DEMO]")
                urs.append(fallback)
            else:
                missing_checks.append(name)

        # If no checks were computed and not in demo mode, refuse to produce fabricated chart
        if not urs:
            logger.info("No calculated utilization ratios present in output_dict; skipping UR chart.")
            if diagnostics is not None:
                diagnostics.setdefault("charts_skipped", []).append(
                    "ur_summary: no calculated utilization ratios present in output_dict"
                )
            return None

        # Plot setup
        fig, ax = plt.subplots(figsize=(10.5, max(4.5, len(labels) * 0.48)), dpi=300)
        fig.patch.set_facecolor('#FFFFFF')
        ax.set_facecolor('#FAFAFA')

        y_positions = list(range(len(labels)))
        y_positions.reverse()

        colors = []
        for ur in urs:
            if ur <= 0.80:
                colors.append('#16A34A')  # Green (Safe)
            elif ur <= 1.00:
                colors.append('#D97706')  # Amber (Warning/High)
            else:
                colors.append('#DC2626')  # Red (Fail)

        bars = ax.barh(y_positions, urs, height=0.62, color=colors, edgecolor='#334155', linewidth=0.75, zorder=3)

        # Threshold limit line at UR = 1.0
        ax.axvline(1.0, color='#DC2626', linestyle='--', linewidth=1.75, label='Design Capacity Limit (UR = 1.0)', zorder=4)

        # Labels on bars
        for bar, ur in zip(bars, urs):
            w = bar.get_width()
            y = bar.get_y() + bar.get_height() / 2.0
            status_text = "Safe" if ur <= 0.80 else ("Near Limit" if ur <= 1.00 else "EXCEEDED")
            text_str = f" {ur:.3f} ({status_text})"
            ax.text(w + 0.015, y, text_str, va='center', ha='left', fontsize=9.5, fontweight='bold', color='#1E293B', zorder=5)

        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels, fontsize=9.5, fontweight='medium', color='#1E293B')
        ax.set_xlabel("Utilization Ratio (UR = Demand / Capacity)", fontsize=11, fontweight='bold', color='#0F172A', labelpad=8)
        
        is_partial = len(missing_checks) > 0 and not demo_mode
        if demo_mode:
            ax.set_title("OsdagBridge — Overall Design Check Summary (Utilization Ratios)\n[DEMO BENCHMARK DATA — ILLUSTRATIVE]", fontsize=12, fontweight='bold', color='#0F172A', pad=14)
        elif is_partial:
            ax.set_title(f"OsdagBridge — Overall Design Check Summary ({len(urs)} of {len(check_specs)} Checks Computed)", fontsize=12, fontweight='bold', color='#0F172A', pad=14)
            ax.text(0.01, -0.14, f"* Note: Showing {len(urs)} calculated checks. {len(missing_checks)} checks uncalculated / not present in output.",
                    transform=ax.transAxes, fontsize=8.5, color='#475569', style='italic')
            if diagnostics is not None:
                diagnostics.setdefault("warnings", []).append(
                    f"ur_summary: Partial chart rendered ({len(urs)}/{len(check_specs)} checks available)"
                )
        else:
            ax.set_title("OsdagBridge — Overall Design Check Summary (All Checks Computed)", fontsize=12, fontweight='bold', color='#0F172A', pad=14)

        max_ur = max(urs) if urs else 1.0
        x_limit = max(1.25, max_ur + 0.25)
        ax.set_xlim(0.0, x_limit)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(0.2))
        ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.05))

        ax.grid(True, which='major', axis='x', linestyle='-', color='#E2E8F0', linewidth=0.8, zorder=1)
        ax.grid(True, which='minor', axis='x', linestyle=':', color='#F1F5F9', linewidth=0.5, zorder=1)
        ax.set_axisbelow(True)

        legend_elements = [
            Patch(facecolor='#16A34A', edgecolor='#334155', label='Safe (UR <= 0.80)'),
            Patch(facecolor='#D97706', edgecolor='#334155', label='Near Capacity (0.80 < UR <= 1.0)'),
            Patch(facecolor='#DC2626', edgecolor='#334155', label='Exceeded (UR > 1.0)'),
            plt.Line2D([0], [0], color='#DC2626', linestyle='--', linewidth=1.75, label='Permissible Limit (1.00)')
        ]
        ax.legend(handles=legend_elements, loc='lower right', framealpha=0.92, edgecolor='#CBD5E1', fontsize=9)

        for sp in ['top', 'right']:
            ax.spines[sp].set_visible(False)
        ax.spines['left'].set_color('#94A3B8')
        ax.spines['bottom'].set_color('#94A3B8')

        plt.tight_layout()
        plt.savefig(out_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        logger.info("Generated UR summary chart: %s (%d checks plotted)", out_path, len(urs))
        if diagnostics is not None:
            diagnostics.setdefault("charts_generated", []).append("ur_summary")
        return out_path

    except Exception as exc:
        logger.error("Failed to generate UR summary chart: %s", exc, exc_info=True)
        if diagnostics is not None:
            diagnostics.setdefault("errors", []).append(f"ur_summary generation error: {exc}")
        return None


def generate_material_quantity_chart(
    input_dict: Dict[str, Any],
    quantities: Dict[str, Any],
    output_dir: str,
    demo_mode: bool = False,
    diagnostics: Optional[Dict[str, Any]] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Generate publication-quality material quantity breakdown charts for Chapter 7.
      1. Structural Steel Breakdown (MT): Girders, Cross Bracing, End Diaphragms, Shear Studs, Stiffeners.
      2. Concrete Volume (Cu.m) vs Rebar Weight (MT).

    Integrity Safeguards:
      - When material quantities are incomplete, the chart displays an explicit partial-quantity
        warning banner stating how many components are missing.
      - Never presents a partial sum as a complete total without prominent disclaimers.
      - Distinguishes between zero quantity (0.0 MT), missing quantity (None), and demo placeholders.

    Args:
        input_dict: Bridge input dictionary.
        quantities: Material quantities dictionary computed by calculate_material_quantities().
        output_dir: Directory where the images should be saved.
        demo_mode: When True, uses illustrative benchmark values if quantities are unpopulated.
                   Defaults to False (strict engineering integrity).
        diagnostics: Optional dictionary to collect generation status, warnings, and errors.

    Returns:
        Tuple of (steel_chart_path, concrete_chart_path).
    """
    steel_path = None
    concrete_path = None

    try:
        os.makedirs(output_dir, exist_ok=True)

        # ─────────────────────────────────────────────────────────────────────
        # 1. Structural Steel Breakdown Chart (material_steel.png)
        # ─────────────────────────────────────────────────────────────────────
        raw_components = [
            ("Main Girders", _parse_float(quantities.get("steel_girders_wt_total"), None), 45.2),
            ("Cross-Bracing (Top Chord)", _parse_float(quantities.get("bracing_top_wt_total"), None), 3.4),
            ("Cross-Bracing (Bottom Chord)", _parse_float(quantities.get("bracing_bot_wt_total"), None), 3.1),
            ("Cross-Bracing (Diagonals)", _parse_float(quantities.get("bracing_diag_wt_total"), None), 4.8),
            ("Shear Stud Connectors", _parse_float(quantities.get("shear_studs_wt_total"), None), 1.2),
            ("Bearing / Transverse Stiffeners", _parse_float(quantities.get("stiffeners_wt_total"), None), 3.8),
        ]

        steel_labels = []
        steel_weights = []
        unavailable_components = []

        for name, wt, demo_val in raw_components:
            if wt is not None and wt >= 0:
                steel_labels.append(name)
                steel_weights.append(wt)
            elif demo_mode:
                steel_labels.append(f"{name} [DEMO]")
                steel_weights.append(demo_val)
            else:
                unavailable_components.append(name)

        total_steel = sum(steel_weights)
        is_partial = len(unavailable_components) > 0 and not demo_mode

        # Only generate steel chart if actual (or explicitly demo) weights exist
        if steel_weights and total_steel > 0:
            fig, ax = plt.subplots(figsize=(8.8, max(4.2, len(steel_labels) * 0.65)), dpi=300)
            fig.patch.set_facecolor('#FFFFFF')
            ax.set_facecolor('#FAFAFA')

            bar_colors = ['#1E293B', '#0284C7', '#0EA5E9', '#38BDF8', '#91B014', '#64748B']
            y_pos = list(range(len(steel_labels)))
            y_pos.reverse()

            bars = ax.barh(
                y_pos,
                steel_weights,
                height=0.55,
                color=bar_colors[:len(steel_labels)],
                edgecolor='#334155',
                linewidth=0.75,
                zorder=3
            )

            pct_suffix = "% of resolved" if is_partial else "%"
            for bar, wt in zip(bars, steel_weights):
                w = bar.get_width()
                y = bar.get_y() + bar.get_height() / 2.0
                pct = (wt / total_steel * 100.0) if total_steel > 0 else 0
                ax.text(w + (max(steel_weights) * 0.02), y, f" {wt:.2f} MT ({pct:.1f}{pct_suffix})",
                        va='center', ha='left', fontsize=9.0, fontweight='bold', color='#1E293B', zorder=5)

            ax.set_yticks(y_pos)
            ax.set_yticklabels(steel_labels, fontsize=9.5, fontweight='medium', color='#1E293B')
            ax.set_xlabel("Structural Steel Weight (Metric Tonnes, MT)", fontsize=10.5, fontweight='bold', color='#0F172A', labelpad=8)
            
            if demo_mode:
                ax.set_title(f"Structural Steel Take-off Breakdown — Total: {total_steel:.2f} MT [DEMO DATA]", fontsize=12, fontweight='bold', color='#0F172A', pad=12)
            elif is_partial:
                n_miss = len(unavailable_components)
                ax.set_title(f"Structural Steel Take-off Breakdown — Resolved Total: {total_steel:.2f} MT\n[PARTIAL BREAKDOWN: {n_miss} COMPONENT(S) UNAVAILABLE]",
                             fontsize=11, fontweight='bold', color='#B91C1C', pad=12)
                ax.text(0.01, -0.16, f"* Note: Partial quantities. Excluded unmodeled components: {', '.join(unavailable_components)}",
                        transform=ax.transAxes, fontsize=8.0, color='#B91C1C', fontweight='medium', style='italic')
                if diagnostics is not None:
                    diagnostics.setdefault("warnings", []).append(
                        f"material_steel: Partial breakdown plotted ({n_miss} components unavailable: {', '.join(unavailable_components)})"
                    )
            else:
                ax.set_title(f"Structural Steel Take-off Breakdown — Total: {total_steel:.2f} MT (Complete)", fontsize=12, fontweight='bold', color='#0F172A', pad=12)

            ax.set_xlim(0, max(steel_weights) * 1.38)
            ax.grid(True, which='major', axis='x', linestyle='-', color='#E2E8F0', linewidth=0.8, zorder=1)
            ax.set_axisbelow(True)

            for sp in ['top', 'right']:
                ax.spines[sp].set_visible(False)
            ax.spines['left'].set_color('#94A3B8')
            ax.spines['bottom'].set_color('#94A3B8')

            plt.tight_layout()
            steel_file = os.path.join(output_dir, "material_steel.png")
            plt.savefig(steel_file, dpi=300, bbox_inches='tight')
            plt.close(fig)
            steel_path = steel_file
            if diagnostics is not None:
                diagnostics.setdefault("charts_generated", []).append("material_steel")
        else:
            if diagnostics is not None:
                diagnostics.setdefault("charts_skipped", []).append("material_steel: no positive steel quantities available")

        # ─────────────────────────────────────────────────────────────────────
        # 2. Concrete Volume vs Rebar Weight Chart (material_concrete.png)
        # ─────────────────────────────────────────────────────────────────────
        conc_vol = _parse_float(quantities.get("concrete_deck_vol_total"), None)
        rebar_wt = _parse_float(quantities.get("rebar_deck_wt_total"), None)

        if demo_mode:
            conc_vol = conc_vol if conc_vol is not None else 68.5
            rebar_wt = rebar_wt if rebar_wt is not None else 8.2

        has_conc = conc_vol is not None and conc_vol > 0
        has_rebar = rebar_wt is not None and rebar_wt > 0

        if has_conc or has_rebar:
            # Resolve concrete grade label dynamically from input_dict (no invented defaults)
            inp_data = input_dict or {}
            concrete_grade = None
            for k in ["material.concrete.grade", "material.deck", "Deck Concrete Grade", "concrete_grade", "deck_concrete_grade"]:
                if inp_data.get(k):
                    val = str(inp_data[k]).strip()
                    if val.lower() == "custom" and inp_data.get("material.concrete.fck"):
                        concrete_grade = f"M{inp_data['material.concrete.fck']}"
                    elif val and val.lower() != "custom":
                        concrete_grade = val
                    break
            conc_title = f"Concrete Volume ({concrete_grade})" if concrete_grade else "Concrete Volume"

            # Resolve rebar grade label dynamically from input_dict (no invented defaults)
            rebar_grade = None
            for k in ["material.rebar.grade", "material.rebar", "Rebar Grade", "rebar_grade"]:
                if inp_data.get(k):
                    val = str(inp_data[k]).strip()
                    if val:
                        rebar_grade = val
                        break
            rebar_title = f"Reinforcement Steel ({rebar_grade})" if rebar_grade else "Reinforcement Steel"

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.8, 4.0), dpi=300)
            fig.patch.set_facecolor('#FFFFFF')

            # Subplot 1: Concrete
            ax1.set_facecolor('#FAFAFA')
            val1 = conc_vol or 0.0
            if has_conc:
                ax1.bar(["Deck Slab\nConcrete"], [val1], width=0.45, color='#475569', edgecolor='#1E293B', linewidth=1.0, zorder=3)
                ax1.set_ylabel(r"Total Volume ($\mathrm{m}^3$)", fontsize=10.5, fontweight='bold', color='#0F172A')
                ax1.set_title(conc_title, fontsize=11, fontweight='bold', color='#0F172A', pad=8)
                ax1.set_ylim(0, max(val1 * 1.3, 1.0))
                ax1.text(0, val1 + (val1 * 0.04), f"{val1:.2f} m³", ha='center', va='bottom', fontsize=11, fontweight='bold', color='#0F172A')
            else:
                ax1.text(0.5, 0.5, "Concrete Volume\nData Unavailable", ha='center', va='center', fontsize=10, color='#94A3B8', style='italic')
                ax1.set_title(conc_title, fontsize=11, fontweight='bold', color='#0F172A', pad=8)
                ax1.set_xticks([])
                ax1.set_yticks([])
            ax1.grid(True, axis='y', linestyle='-', color='#E2E8F0', zorder=1)
            ax1.set_axisbelow(True)

            # Subplot 2: Rebar
            ax2.set_facecolor('#FAFAFA')
            val2 = rebar_wt or 0.0
            if has_rebar:
                ax2.bar(["Deck Slab\nReinforcement"], [val2], width=0.45, color='#91B014', edgecolor='#1E293B', linewidth=1.0, zorder=3)
                ax2.set_ylabel("Total Weight (MT)", fontsize=10.5, fontweight='bold', color='#0F172A')
                ax2.set_title(rebar_title, fontsize=11, fontweight='bold', color='#0F172A', pad=8)
                ax2.set_ylim(0, max(val2 * 1.3, 1.0))
                ax2.text(0, val2 + (val2 * 0.04), f"{val2:.2f} MT", ha='center', va='bottom', fontsize=11, fontweight='bold', color='#0F172A')
            else:
                ax2.text(0.5, 0.5, "Reinforcement\nData Unavailable", ha='center', va='center', fontsize=10, color='#94A3B8', style='italic')
                ax2.set_title(rebar_title, fontsize=11, fontweight='bold', color='#0F172A', pad=8)
                ax2.set_xticks([])
                ax2.set_yticks([])
            ax2.grid(True, axis='y', linestyle='-', color='#E2E8F0', zorder=1)
            ax2.set_axisbelow(True)

            for ax_cur in (ax1, ax2):
                for sp in ['top', 'right']:
                    ax_cur.spines[sp].set_visible(False)
                ax_cur.spines['left'].set_color('#94A3B8')
                ax_cur.spines['bottom'].set_color('#94A3B8')

            title_suffix = " [DEMO DATA]" if demo_mode else ""
            plt.suptitle(f"Deck Slab Material Summary — Concrete vs Reinforcement{title_suffix}", fontsize=12, fontweight='bold', color='#0F172A', y=0.98)
            plt.tight_layout()
            concrete_file = os.path.join(output_dir, "material_concrete.png")
            plt.savefig(concrete_file, dpi=300, bbox_inches='tight')
            plt.close(fig)
            concrete_path = concrete_file
            if diagnostics is not None:
                diagnostics.setdefault("charts_generated", []).append("material_concrete")
        else:
            if diagnostics is not None:
                diagnostics.setdefault("charts_skipped", []).append("material_concrete: no concrete or rebar quantities available")

        logger.info("Generated material quantity charts: %s and %s", steel_path, concrete_path)

    except Exception as exc:
        logger.error("Failed to generate material quantity charts: %s", exc, exc_info=True)
        if diagnostics is not None:
            diagnostics.setdefault("errors", []).append(f"material charts error: {exc}")

    return steel_path, concrete_path
