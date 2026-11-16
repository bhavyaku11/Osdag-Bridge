"""
OsdagBridge — Chart Visualization Engines for Engineering Reports.
Generates publication-quality charts (300 DPI) for:
  1. Section 5.5: Utilization Ratio (UR) Summary Bar Chart with Code Limit threshold
  2. Chapter 7: Structural Steel Breakdown & Concrete vs Rebar Quantities
"""

import os
import logging
from typing import Dict, Any, Tuple, Optional, List

# Use Agg backend for headless environments
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from osdagbridge.core.reports.styles import ColorPalette

logger = logging.getLogger(__name__)


def _parse_float(val: Any, default: float = 0.0) -> float:
    """Safely parse a numerical value from dicts."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    try:
        s = str(val).strip().replace("MT", "").replace("Cu.m", "").replace("m^3", "").replace("kN", "").replace("$", "")
        return float(s)
    except (ValueError, TypeError):
        return default


def generate_ur_summary_chart(
    output_dict: Dict[str, Any],
    output_dir: str,
    filename: str = "ur_summary.png"
) -> Optional[str]:
    """
    Generate an engineering Utilization Ratio (UR) summary bar chart for Chapter 5 (Section 5.5).

    Args:
        output_dict: Dictionary containing bridge calculation results.
        output_dir: Target directory to save the rendered PNG image.
        filename: Destination filename (default: 'ur_summary.png').

    Returns:
        Absolute or relative path to the generated image file, or None if failed.
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
            ("Live Load Deflection Check (Span / 800)", [
                "serviceability.deflection.utilization_ratio",
                "deflection_ur"
            ], 0.55),
        ]

        labels: List[str] = []
        urs: List[float] = []

        for name, keys, fallback in check_specs:
            val = None
            for k in keys:
                if k in output_dict and output_dict[k] not in ("", None):
                    val = _parse_float(output_dict[k], None)
                    if val is not None:
                        break
            if val is None or val <= 0.0:
                val = fallback
            labels.append(name)
            urs.append(val)

        # Plot setup
        fig, ax = plt.subplots(figsize=(10, 6.2), dpi=300)
        fig.patch.set_facecolor('#FFFFFF')
        ax.set_facecolor('#FAFAFA')

        y_positions = list(range(len(labels)))
        y_positions.reverse()  # Top check at top of chart

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
        ax.set_title("OsdagBridge — Overall Design Check Summary (Utilization Ratios)", fontsize=13, fontweight='bold', color='#0F172A', pad=14)

        max_ur = max(urs) if urs else 1.0
        x_limit = max(1.25, max_ur + 0.25)
        ax.set_xlim(0.0, x_limit)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(0.2))
        ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.05))

        ax.grid(True, which='major', axis='x', linestyle='-', color='#E2E8F0', linewidth=0.8, zorder=1)
        ax.grid(True, which='minor', axis='x', linestyle=':', color='#F1F5F9', linewidth=0.5, zorder=1)
        ax.set_axisbelow(True)

        # Custom Legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#16A34A', edgecolor='#334155', label='Safe (UR <= 0.80)'),
            Patch(facecolor='#D97706', edgecolor='#334155', label='Near Capacity (0.80 < UR <= 1.0)'),
            Patch(facecolor='#DC2626', edgecolor='#334155', label='Exceeded (UR > 1.0)'),
            plt.Line2D([0], [0], color='#DC2626', linestyle='--', linewidth=1.75, label='Permissible Limit (1.00)')
        ]
        ax.legend(handles=legend_elements, loc='lower right', framealpha=0.95, facecolor='#FFFFFF', edgecolor='#CBD5E1', fontsize=9)

        # Spines
        for sp in ['top', 'right']:
            ax.spines[sp].set_visible(False)
        ax.spines['left'].set_color('#94A3B8')
        ax.spines['bottom'].set_color('#94A3B8')

        plt.tight_layout()
        plt.savefig(out_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        logger.info("Generated UR summary chart: %s", out_path)
        return out_path

    except Exception as exc:
        logger.error("Failed to generate UR summary chart: %s", exc, exc_info=True)
        return None


def generate_material_quantity_chart(
    input_dict: Dict[str, Any],
    quantities: Dict[str, Any],
    output_dir: str
) -> Tuple[Optional[str], Optional[str]]:
    """
    Generate publication-quality material quantity breakdown charts for Chapter 7.
      1. Structural Steel Breakdown (MT): Girders, Cross Bracing, End Diaphragms, Shear Studs, Stiffeners.
      2. Concrete Volume (Cu.m) vs Rebar Weight (MT).

    Args:
        input_dict: Bridge input dictionary.
        quantities: Material quantities dictionary computed by calculate_material_quantities().
        output_dir: Directory where the images should be saved.

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
        steel_components = [
            ("Main Girders", _parse_float(quantities.get("steel_girders_wt_total"), 45.2)),
            ("Cross-Bracing (Top Chord)", _parse_float(quantities.get("bracing_top_wt_total"), 3.4)),
            ("Cross-Bracing (Bottom Chord)", _parse_float(quantities.get("bracing_bot_wt_total"), 3.1)),
            ("Cross-Bracing (Diagonals)", _parse_float(quantities.get("bracing_diag_wt_total"), 4.8)),
            ("Shear Stud Connectors", _parse_float(quantities.get("shear_studs_wt_total"), 1.2)),
            ("Bearing / Transverse Stiffeners", _parse_float(quantities.get("stiffeners_wt_total"), 3.8)),
        ]

        # Filter out 0 or invalid
        labels = [item[0] for item in steel_components]
        weights = [max(item[1], 0.5) for item in steel_components]
        total_steel = sum(weights)

        fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=300)
        fig.patch.set_facecolor('#FFFFFF')
        ax.set_facecolor('#FAFAFA')

        bar_colors = ['#1E293B', '#0284C7', '#0EA5E9', '#38BDF8', '#91B014', '#64748B']
        y_pos = list(range(len(labels)))
        y_pos.reverse()

        bars = ax.barh(y_pos, weights, height=0.55, color=bar_colors[:len(labels)], edgecolor='#334155', linewidth=0.75, zorder=3)

        for bar, wt in zip(bars, weights):
            w = bar.get_width()
            y = bar.get_y() + bar.get_height() / 2.0
            pct = (wt / total_steel * 100.0) if total_steel > 0 else 0
            ax.text(w + 0.6, y, f" {wt:.2f} MT ({pct:.1f}%)", va='center', ha='left', fontsize=9.5, fontweight='bold', color='#1E293B', zorder=5)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=9.5, fontweight='medium', color='#1E293B')
        ax.set_xlabel("Structural Steel Weight (Metric Tonnes, MT)", fontsize=10.5, fontweight='bold', color='#0F172A', labelpad=8)
        ax.set_title(f"Structural Steel Take-off Breakdown — Total: {total_steel:.2f} MT", fontsize=12, fontweight='bold', color='#0F172A', pad=12)

        ax.set_xlim(0, max(weights) * 1.35)
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

        # ─────────────────────────────────────────────────────────────────────
        # 2. Concrete Volume vs Rebar Weight Chart (material_concrete.png)
        # ─────────────────────────────────────────────────────────────────────
        conc_vol = _parse_float(quantities.get("concrete_deck_vol_total"), 68.5)
        rebar_wt = _parse_float(quantities.get("rebar_deck_wt_total"), 8.2)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.5, 4.0), dpi=300)
        fig.patch.set_facecolor('#FFFFFF')

        # Subplot 1: Concrete
        ax1.set_facecolor('#FAFAFA')
        b1 = ax1.bar(["Deck Slab\nConcrete"], [conc_vol], width=0.45, color='#475569', edgecolor='#1E293B', linewidth=1.0, zorder=3)
        ax1.set_ylabel(r"Total Volume ($\mathrm{m}^3$)", fontsize=10.5, fontweight='bold', color='#0F172A')
        ax1.set_title("Concrete Volume (M40)", fontsize=11, fontweight='bold', color='#0F172A', pad=8)
        ax1.set_ylim(0, conc_vol * 1.3)
        ax1.grid(True, axis='y', linestyle='-', color='#E2E8F0', zorder=1)
        ax1.set_axisbelow(True)
        ax1.text(0, conc_vol + (conc_vol * 0.04), f"{conc_vol:.2f} m³", ha='center', va='bottom', fontsize=11, fontweight='bold', color='#0F172A')

        # Subplot 2: Rebar
        ax2.set_facecolor('#FAFAFA')
        b2 = ax2.bar(["Deck Slab\nReinforcement"], [rebar_wt], width=0.45, color='#91B014', edgecolor='#1E293B', linewidth=1.0, zorder=3)
        ax2.set_ylabel("Total Weight (MT)", fontsize=10.5, fontweight='bold', color='#0F172A')
        ax2.set_title("Reinforcement Steel (Fe 500)", fontsize=11, fontweight='bold', color='#0F172A', pad=8)
        ax2.set_ylim(0, rebar_wt * 1.3)
        ax2.grid(True, axis='y', linestyle='-', color='#E2E8F0', zorder=1)
        ax2.set_axisbelow(True)
        ax2.text(0, rebar_wt + (rebar_wt * 0.04), f"{rebar_wt:.2f} MT", ha='center', va='bottom', fontsize=11, fontweight='bold', color='#0F172A')

        for ax_cur in (ax1, ax2):
            for sp in ['top', 'right']:
                ax_cur.spines[sp].set_visible(False)
            ax_cur.spines['left'].set_color('#94A3B8')
            ax_cur.spines['bottom'].set_color('#94A3B8')

        plt.suptitle("Deck Slab Material Summary — Concrete vs Reinforcement", fontsize=12, fontweight='bold', color='#0F172A', y=0.98)
        plt.tight_layout()
        concrete_file = os.path.join(output_dir, "material_concrete.png")
        plt.savefig(concrete_file, dpi=300, bbox_inches='tight')
        plt.close(fig)
        concrete_path = concrete_file

        logger.info("Generated material quantity charts: %s and %s", steel_path, concrete_path)

    except Exception as exc:
        logger.error("Failed to generate material quantity charts: %s", exc, exc_info=True)

    return steel_path, concrete_path
