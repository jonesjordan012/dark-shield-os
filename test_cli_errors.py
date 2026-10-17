"""CLI error-output tests for the Temporal Echo recorder.

Verifies that failures surface correctly: non-zero exit codes,
human-readable errors on stderr, and clean stdout separation.

Run from the first-light folder:
    pytest test_cli_errors.py -v
"""

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent / "temporal_echo.py"


def assert_cli_error(result, fragment):
    assert result.returncode == 1
    assert "ERROR:" in result.stderr
    assert fragment in result.stderr
    assert result.stdout == ""


def test_cli_rejects_non_jsonl_extension():
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--log",
            "echoes.txt",
            "gravity-log.py",
            "modified",
            "12.4",
            "13.1",
        ],
        capture_output=True,
        text=True,
    )

    assert_cli_error(result, ".jsonl")


def test_cli_rejects_directory_path(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--log",
            str(log_dir),
            "gravity-log.py",
            "modified",
            "12.4",
            "13.1",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "ERROR:" in result.stderr
    assert "directory" in result.stderr.lower()
    assert result.stdout == ""


def test_cli_missing_arguments():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "usage:" in result.stderr.lower()


def test_cli_success_has_empty_stderr(tmp_path):
    log_file = tmp_path / "echoes.jsonl"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--log",
            str(log_file),
            "gravity-log.py",
            "modified",
            "12.4",
            "13.1",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert "echo recorded" in result.stdout.lower()
    assert log_file.exists()
