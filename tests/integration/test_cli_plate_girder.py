"""
Integration test suite for OsdagBridge Command Line Interface (CLI).
Covers:
  - CLI commands: version, analyze, boq, report
  - Subprocess execution and direct handler invocation
  - Error handling on missing/corrupt model files
  - Report emission via CLI
"""

import argparse
import os
import subprocess
import sys
import pytest

from osdagbridge.cli.commands import (
    cmd_version,
    cmd_analyze,
    cmd_boq,
    cmd_report
)


@pytest.fixture
def sample_model_path():
    """Returns absolute path to sample bridge model."""
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(repo_root, "resources", "sample_bridge_model.json")
    assert os.path.isfile(path), f"Sample bridge model not found at {path}"
    return path


def test_cli_version_command(capsys):
    """Verify version command executes cleanly and displays version info."""
    args = argparse.Namespace()
    ret = cmd_version(args)
    assert ret == 0
    captured = capsys.readouterr()
    assert "OsdagBridge Core Version" in captured.out


def test_cli_analyze_command(sample_model_path, capsys):
    """Verify analyze command validates sample model."""
    args = argparse.Namespace(input_file=sample_model_path)
    ret = cmd_analyze(args)
    assert ret == 0
    captured = capsys.readouterr()
    assert "Model geometry validated successfully." in captured.out
    assert "Span Length: 24.0 m" in captured.out


def test_cli_boq_command(sample_model_path, capsys):
    """Verify boq command computes quantities and prints formatted table."""
    args = argparse.Namespace(input_file=sample_model_path, output_file=None)
    ret = cmd_boq(args)
    assert ret == 0
    captured = capsys.readouterr()
    assert "Material Take-Off & BOQ Estimator" in captured.out
    assert "Main Structural Steel Girders" in captured.out
    assert "Reinforced Concrete Deck Slab" in captured.out


def test_cli_report_command(sample_model_path, tmp_path, capsys):
    """Verify report command generates LaTeX source in specified directory."""
    out_dir = str(tmp_path / "cli_report")
    args = argparse.Namespace(
        input_file=sample_model_path,
        output_file=None,
        output_dir=out_dir,
        filename="CLI_Report.tex",
        compile_pdf=False
    )
    ret = cmd_report(args)
    assert ret == 0
    captured = capsys.readouterr()
    assert "LaTeX Report Generator Engine" in captured.out
    assert "[SUCCESS] Engineering design report generated successfully" in captured.out
    assert os.path.isfile(os.path.join(out_dir, "CLI_Report.tex"))


def test_cli_missing_file_handling():
    """Verify CLI commands gracefully handle non-existent files."""
    args = argparse.Namespace(input_file="/non/existent/bridge.json", output_file=None)
    assert cmd_analyze(args) != 0
    assert cmd_boq(args) != 0
    assert cmd_report(args) != 0


def test_cli_subprocess_invocation():
    """Verify running the CLI as a module via python -m osdagbridge.cli."""
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(repo_root, "src")

    res = subprocess.run(
        [sys.executable, "-m", "osdagbridge.cli", "version"],
        capture_output=True,
        text=True,
        env=env
    )
    assert res.returncode == 0
    assert "OsdagBridge Core Version" in res.stdout
