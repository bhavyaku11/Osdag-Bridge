r"""
Centralized Style & Formatting System for OsdagBridge Reports.
Single Source of Truth for:
  - Document geometry, margins, and page layout (fixing footer overlap)
  - Color palettes (Osdag brand, status highlights, table shading)
  - Table typography, row heights, cell padding, and column specifications
  - LongTable header/footer repetition macros (\endfirsthead, \endhead)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ColorPalette:
    """Color definitions for text, rules, and backgrounds."""
    PRIMARY: str = "91B014"       # Osdag Green
    SECONDARY: str = "1E293B"     # Slate Navy
    ACCENT: str = "0284C7"        # Sky Blue
    PASS: str = "16A34A"          # Forest Green
    WARN: str = "D97706"          # Amber
    FAIL: str = "DC2626"          # Crimson Red
    TABLE_HEADER_BG: str = "E2E8F0"  # Light gray-blue header
    TABLE_ALT_ROW: str = "F8FAFC"    # Subtle alternate row
    BORDER: str = "94A3B8"        # Subtle border rule
    TEXT_MUTED: str = "64748B"    # Gray explanatory text


@dataclass(frozen=True)
class GeometryConfig:
    """Page geometry and spacing to prevent header/footer overlap."""
    PAPER: str = "a4paper"
    TOP_MARGIN: str = "2.5cm"
    BOTTOM_MARGIN: str = "2.8cm"  # Generous bottom clearance to prevent footer bleed
    LEFT_MARGIN: str = "2.5cm"
    RIGHT_MARGIN: str = "2.5cm"
    HEAD_HEIGHT: str = "16pt"
    HEAD_SEP: str = "12pt"
    FOOT_SKIP: str = "38pt"       # Keeps footer separated from table contents


@dataclass(frozen=True)
class TableFormatting:
    """Table layout, cell padding, and LongTable vertical skips."""
    TABCOLSEP: str = "6pt"
    ARRAY_STRETCH: float = 1.15
    LT_PRE_SKIP: str = "2pt"
    LT_POST_SKIP: str = "6pt"
    RULE_WIDTH: str = "0.5pt"
    EXTRA_ROW_HEIGHT: str = "0.6pt"
    NEEDSPACE_LINES: int = 5


class ReportStyle:
    """Master style coordinator providing LaTeX definitions and helper macros."""

    colors = ColorPalette()
    geometry = GeometryConfig()
    tables = TableFormatting()

    @classmethod
    def get_latex_color_definitions(cls) -> str:
        """Returns standard xcolor definitions."""
        return (
            f"\\definecolor{{osdagGreen}}{{HTML}}{{{cls.colors.PRIMARY}}}\n"
            f"\\definecolor{{osdagNavy}}{{HTML}}{{{cls.colors.SECONDARY}}}\n"
            f"\\definecolor{{osdagPass}}{{HTML}}{{{cls.colors.PASS}}}\n"
            f"\\definecolor{{osdagWarn}}{{HTML}}{{{cls.colors.WARN}}}\n"
            f"\\definecolor{{osdagFail}}{{HTML}}{{{cls.colors.FAIL}}}\n"
            f"\\definecolor{{tableHeaderBg}}{{HTML}}{{{cls.colors.TABLE_HEADER_BG}}}\n"
            f"\\definecolor{{tableAltRow}}{{HTML}}{{{cls.colors.TABLE_ALT_ROW}}}\n"
        )

    @classmethod
    def get_geometry_preamble(cls) -> str:
        """Returns LaTeX geometry package configuration."""
        g = cls.geometry
        return (
            f"\\usepackage[{g.PAPER}, top={g.TOP_MARGIN}, bottom={g.BOTTOM_MARGIN}, "
            f"left={g.LEFT_MARGIN}, right={g.RIGHT_MARGIN}, headheight={g.HEAD_HEIGHT}, "
            f"headsep={g.HEAD_SEP}, footskip={g.FOOT_SKIP}]{{geometry}}\n"
        )

    @classmethod
    def get_table_preamble(cls) -> str:
        """Returns column definitions and padding rules."""
        t = cls.tables
        return (
            f"\\setlength{{\\tabcolsep}}{{{t.TABCOLSEP}}}\n"
            f"\\renewcommand{{\\arraystretch}}{{{t.ARRAY_STRETCH}}}\n"
            f"\\setlength{{\\LTpre}}{{{t.LT_PRE_SKIP}}}\n"
            f"\\setlength{{\\LTpost}}{{{t.LT_POST_SKIP}}}\n"
            f"\\setlength{{\\arrayrulewidth}}{{{t.RULE_WIDTH}}}\n"
            f"\\setlength{{\\extrarowheight}}{{{t.EXTRA_ROW_HEIGHT}}}\n"
            f"\\BeforeBeginEnvironment{{table}}{{\\needspace{{{t.NEEDSPACE_LINES}\\baselineskip}}}}\n"
            f"\\BeforeBeginEnvironment{{longtable}}{{\\needspace{{{t.NEEDSPACE_LINES}\\baselineskip}}}}\n"
            # Define column types with explicit alignments
            "\\newcolumntype{L}[1]{>{\\raggedright\\arraybackslash}p{#1}}\n"
            "\\newcolumntype{C}[1]{>{\\centering\\arraybackslash}p{#1}}\n"
            "\\newcolumntype{R}[1]{>{\\raggedleft\\arraybackslash}p{#1}}\n"
        )

    @classmethod
    def build_longtable_header(
        cls,
        col_spec: str,
        header_row: str,
        caption: Optional[str] = None,
        label: Optional[str] = None,
        continued_caption: Optional[str] = None
    ) -> str:
        """
        Builds a standard, clean LongTable header/footer structure ensuring
        headers repeat properly across all page breaks.
        """
        cap_str = f"\\caption{{{caption}}}" if caption else ""
        lbl_str = f"\\label{{{label}}}" if label else ""
        first_caption = f"{cap_str}{lbl_str} \\\\\n" if (caption or label) else ""

        cont_cap = continued_caption or (f"{caption} (Continued)" if caption else "Continued from previous page")
        cont_caption = f"\\caption[]{{{cont_cap}}} \\\\\n"

        return (
            f"\\begin{{longtable}}{{{col_spec}}}\n"
            f"{first_caption}"
            f"\\hline\n"
            f"\\rowcolor{{tableHeaderBg}}\n"
            f"{header_row} \\\\\n"
            f"\\hline\n"
            f"\\endfirsthead\n\n"
            f"% Header for subsequent pages\n"
            f"{cont_caption}"
            f"\\hline\n"
            f"\\rowcolor{{tableHeaderBg}}\n"
            f"{header_row} \\\\\n"
            f"\\hline\n"
            f"\\endhead\n\n"
            f"% Footer for split pages\n"
            f"\\hline\n"
            f"\\multicolumn{{1}}{{r}}{{\\footnotesize\\textit{{Continued on next page...}}}} \\\\\n"
            f"\\endfoot\n\n"
            f"% Final footer\n"
            f"\\hline\n"
            f"\\endlastfoot\n"
        )

    @classmethod
    def format_status_badge(cls, status_text: str) -> str:
        """Renders color-coded status badges for check tables."""
        st = status_text.strip().upper()
        if "PASS" in st:
            return f"\\textcolor{{osdagPass}}{{\\textbf{{{status_text}}}}}"
        elif "WARN" in st:
            return f"\\textcolor{{osdagWarn}}{{\\textbf{{{status_text}}}}}"
        elif "FAIL" in st:
            return f"\\textcolor{{osdagFail}}{{\\textbf{{{status_text}}}}}"
        return status_text
