"""
OsdagBridge — Command-Line Interface Entry Point.
"""

import argparse
import sys

from osdagbridge.cli.commands import cmd_analyze, cmd_boq, cmd_report, cmd_version


def main():
    parser = argparse.ArgumentParser(
        prog="osdagbridge",
        description="OsdagBridge — Automated Analysis, Design, BOQ, and LaTeX Reporting for Steel-Concrete Composite Bridges"
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available commands")

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Validate bridge input model and geometry")
    p_analyze.add_argument("input_file", help="Path to bridge input JSON file")
    p_analyze.set_defaults(func=cmd_analyze)

    # boq
    p_boq = subparsers.add_parser("boq", help="Compute and print Bill of Quantities (BOQ) material take-off")
    p_boq.add_argument("input_file", help="Path to bridge input JSON file")
    p_boq.add_argument("--output-file", help="Optional path to analysis output JSON file")
    p_boq.set_defaults(func=cmd_boq)

    # report
    p_report = subparsers.add_parser("report", help="Generate publication-quality 7-chapter LaTeX design report")
    p_report.add_argument("input_file", help="Path to bridge input JSON file")
    p_report.add_argument("--output-file", help="Optional path to analysis output JSON file")
    p_report.add_argument("--output-dir", help="Directory where the .tex report and charts will be written")
    p_report.add_argument("--filename", help="Report filename (default: Bridge_Design_Report.tex)")
    p_report.set_defaults(func=cmd_report)

    # version
    p_version = subparsers.add_parser("version", help="Show OsdagBridge version information")
    p_version.set_defaults(func=cmd_version)

    # gui
    def _cmd_gui(args):
        from osdagbridge.desktop.__main__ import main as desktop_main
        return desktop_main()

    p_gui = subparsers.add_parser("gui", help="Launch the OsdagBridge desktop graphical user interface")
    p_gui.set_defaults(func=_cmd_gui)

    args = parser.parse_args()
    if not args.subcommand:
        parser.print_help()
        sys.exit(0)
    else:
        sys.exit(args.func(args))


if __name__ == "__main__":
    main()
