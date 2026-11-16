# =============================================================================
# Chapter 7: Material Take-off & Quantity Summary
# Refactored for FOSSEE OsdagBridge Standards:
#   - Embeds visual charts for Structural Steel and Concrete vs Rebar take-offs
#   - LongTable headers repeated on page breaks (\endhead, \endfirsthead)
#   - Color shaded header matching ReportStyle (tableHeaderBg)
#   - Resolves unmatched LaTeX group scope
# =============================================================================

from osdagbridge.core.reports.report_utils import _fig_embed


def ch7_quantities(input_dict, fig_paths=None):
    steel_fig = ""
    conc_fig = ""
    if fig_paths:
        if fig_paths.get('material_steel'):
            steel_fig = _fig_embed(
                fig_paths.get('material_steel'),
                'Structural Steel Take-off Breakdown across Superstructure Components (Metric Tonnes, MT)',
                width=r'0.88\textwidth'
            ) + "\n\\vspace{1em}\n"
        if fig_paths.get('material_concrete'):
            conc_fig = _fig_embed(
                fig_paths.get('material_concrete'),
                'Deck Slab Material Summary --- Concrete Volume (Cu.m) vs Reinforcement Steel (MT)',
                width=r'0.88\textwidth'
            ) + "\n\\vspace{1.5em}\n"

    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

This chapter summarizes the Bill of Materials (BOM) and total structural material quantities estimated for the bridge superstructure, including structural steel (IS 2062), deck concrete (M40), high-yield strength deformed reinforcement bars (Fe 500), and mechanical shear connectors.

\vspace{0.5em}
""" + steel_fig + conc_fig + r"""
\begingroup
\setlength{\tabcolsep}{4.0pt}
\begin{longtable}{|C{1.0cm}|L{3.6cm}|C{2.6cm}|C{1.6cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|}
\caption{\textbf{Bill of Materials --- Steel, Concrete, and Reinforcement Quantities}}
\label{tab:bom} \\
\hline
\rowcolor{tableHeaderBg}
\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume Formula} & \textbf{Qty} & \textbf{Vol. ($\text{m}^3$)} & \textbf{Unit Wt (MT)} & \textbf{Total Wt (MT)} \\[4pt]
\hline
\endfirsthead
\caption[]{\textbf{Bill of Materials --- Quantities (Continued)}} \\
\hline
\rowcolor{tableHeaderBg}
\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume Formula} & \textbf{Qty} & \textbf{Vol. ($\text{m}^3$)} & \textbf{Unit Wt (MT)} & \textbf{Total Wt (MT)} \\[4pt]
\hline
\endhead
\hline
\multicolumn{7}{r}{\footnotesize\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
1 & Structural Steel (IS 2062) for Girders & """ + str(input_dict.get("steel_girders_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_qty", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_wt_total", "N.A.")) + r""" \\[4pt]
\hline
2(a) & Cross Bracing -- Top Chord & """ + str(input_dict.get("bracing_top_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_wt_total", "N.A.")) + r""" \\[4pt]
\hline
2(b) & Cross Bracing -- Bottom Chord & """ + str(input_dict.get("bracing_bot_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_wt_total", "N.A.")) + r""" \\[4pt]
\hline
2(c) & Cross Bracing -- Diagonal Chord & """ + str(input_dict.get("bracing_diag_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_wt_total", "N.A.")) + r""" \\[4pt]
\hline
3 & Concrete (M40) for Deck Slab & """ + str(input_dict.get("concrete_deck_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_qty", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_wt_total", "N.A.")) + r""" \\[4pt]
\hline
4 & Reinforcement Steel (Fe 500) & """ + str(input_dict.get("rebar_deck_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_qty", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_wt_total", "N.A.")) + r""" \\[4pt]
\hline
5 & Shear Stud Connectors & """ + str(input_dict.get("shear_studs_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_qty", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_wt_total", "N.A.")) + r""" \\[4pt]
\hline
6 & Crash Barrier & """ + str(input_dict.get("crash_barrier_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_qty", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_wt_total", "N.A.")) + r""" \\[4pt]
\hline
\end{longtable}
\endgroup
"""
