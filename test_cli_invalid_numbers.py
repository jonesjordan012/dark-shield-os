"""CLI numeric-validation tests for the Temporal Echo recorder.

Gravity values are the payload of an echo: malformed inputs
(NaN, infinity, non-numeric) must never produce a record.

Run from the first-light folder:
    pytest test_cli_invalid_numbers.py -v
"""

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent / "temporal_echo.py"


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def test_rejects_invalid_gravity_before():
    result = run_cli("gravity-log.py", "modified", "not-a-number", "13.1")

    assert result.returncode != 0
    assert "invalid" in result.stderr.lower()
    assert "gravity_before" in result.stderr.lower()


def test_rejects_invalid_gravity_after():
    result = run_cli("gravity-log.py", "modified", "12.4", "abc")

    assert result.returncode != 0
    assert "invalid" in result.stderr.lower()
    assert "gravity_after" in result.stderr.lower()


def test_rejects_two_invalid_gravity_values():
    result = run_cli("gravity-log.py", "modified", "foo", "bar")

    assert result.returncode != 0
    assert "invalid" in result.stderr.lower()


def test_missing_gravity_after_argument():
    result = run_cli("gravity-log.py", "modified", "12.4")

    assert result.returncode != 0
    assert "usage:" in result.stderr.lower()


def test_rejects_nan_gravity():
    result = run_cli("gravity-log.py", "modified", "nan", "13.1")

    assert result.returncode == 1
    assert "cannot be NaN" in result.stderr


def test_rejects_infinite_gravity():
    result = run_cli("gravity-log.py", "modified", "inf", "13.1")

    assert result.returncode == 1
    assert "must be finite" in result.stderr


def test_rejects_negative_infinite_gravity():
    # "--" separates options from positionals so "-inf"
    # isn't mistaken for a flag (standard Unix behavior).
    result = run_cli(
        "--", "gravity-log.py", "modified", "12.4", "-inf",
    )

    assert result.returncode == 1
    assert "must be finite" in result.stderr


def test_no_record_written_on_invalid_input(tmp_path):
    log_file = tmp_path / "echoes.jsonl"

    result = run_cli(
        "--log", str(log_file),
        "gravity-log.py", "modified", "nan", "13.1",
    )

    assert result.returncode == 1
    assert not log_file.exists()
