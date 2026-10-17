"""Tests for the Temporal Echo recorder's path validation.

Run from the first-light folder:
    pytest test_temporal_echo.py -v
"""

import os
import stat
from pathlib import Path

import pytest

from temporal_echo import validate_log_path


def test_accepts_valid_jsonl_path(tmp_path):
    log_path = tmp_path / "echoes.jsonl"

    result = validate_log_path(str(log_path))

    assert result == log_path


def test_creates_missing_parent_directories(tmp_path):
    log_path = tmp_path / "galaxies" / "dev" / "echoes.jsonl"

    validate_log_path(str(log_path))

    assert log_path.parent.exists()


def test_rejects_directory_path(tmp_path):
    directory = tmp_path / "logs"
    directory.mkdir()

    with pytest.raises(ValueError, match="directory"):
        validate_log_path(str(directory))


def test_rejects_non_jsonl_extension(tmp_path):
    log_path = tmp_path / "echoes.txt"

    with pytest.raises(ValueError, match=r"\.jsonl"):
        validate_log_path(str(log_path))


def test_accepts_uppercase_jsonl_extension(tmp_path):
    log_path = tmp_path / "echoes.JSONL"

    result = validate_log_path(str(log_path))

    assert result == log_path


def test_accepts_nested_log_path(tmp_path):
    log_path = (
        tmp_path
        / "moonlight"
        / "experiment-001"
        / "echoes.jsonl"
    )

    result = validate_log_path(str(log_path))

    assert result == log_path


@pytest.mark.skipif(
    os.name == "nt",
    reason="Permission semantics differ on Windows",
)
def test_rejects_unwritable_directory(tmp_path):
    readonly = tmp_path / "readonly"
    readonly.mkdir()
    readonly.chmod(stat.S_IREAD)

    log_path = readonly / "echoes.jsonl"

    try:
        with pytest.raises(ValueError, match="Cannot write"):
            validate_log_path(str(log_path))
    finally:
        readonly.chmod(stat.S_IWRITE | stat.S_IREAD)
