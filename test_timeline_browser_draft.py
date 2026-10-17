"""Tests for timeline_browser_draft.py -- walking through echo history.

Synthetic echo logs only. Each test builds its own small timeline
in a tmp file and checks ordering, filtering, and display.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline_browser_draft as tb


def iso(dt):
    return dt.isoformat()


def write_log(path, echoes):
    with open(path, "w", encoding="utf-8") as f:
        for e in echoes:
            f.write(json.dumps(e) + "\n")


def echo(obj, event, gb, ga, ts):
    return {"timestamp": iso(ts), "object": obj, "event": event,
            "gravity_before": gb, "gravity_after": ga}


NOW = datetime(2026, 10, 17, 9, 0, tzinfo=timezone.utc)


def test_load_echoes_reads_all(tmp_path):
    log = tmp_path / "e.jsonl"
    write_log(log, [echo("a.txt", "pinned", 0.0, 0.0, NOW),
                    echo("b.txt", "observed", 0.0, 1.0, NOW)])
    echoes = tb.load_echoes(str(log))
    assert len(echoes) == 2


def test_load_echoes_skips_malformed(tmp_path):
    log = tmp_path / "e.jsonl"
    with open(log, "w", encoding="utf-8") as f:
        f.write("not json\n")
        f.write(json.dumps(echo("a.txt", "pinned", 0.0, 0.0, NOW)) + "\n")
        f.write('{"incomplete": true}\n')
    echoes = tb.load_echoes(str(log))
    # Malformed lines are skipped silently by load_echoes (no crash).
    assert len(echoes) == 1
    assert echoes[0]["object"] == "a.txt"


def test_load_echoes_missing_file_exits(tmp_path, capsys):
    with pytest.raises(SystemExit):
        tb.load_echoes(str(tmp_path / "absent.jsonl"))
    assert "No echo log found" in capsys.readouterr().err


def test_default_order_is_oldest_first(tmp_path, capsys, monkeypatch):
    log = tmp_path / "e.jsonl"
    write_log(log, [echo("new.txt", "scanned", 0.0, 0.0, NOW),
                    echo("old.txt", "scanned", 0.0, 0.0,
                         NOW - timedelta(hours=5))])
    monkeypatch.setattr(sys, "argv",
                        ["timeline_browser_draft.py", "--log", str(log)])
    tb.main()
    out = capsys.readouterr().out
    assert out.index("old.txt") < out.index("new.txt")


def test_reverse_shows_newest_first(tmp_path, capsys, monkeypatch):
    log = tmp_path / "e.jsonl"
    write_log(log, [echo("new.txt", "scanned", 0.0, 0.0, NOW),
                    echo("old.txt", "scanned", 0.0, 0.0,
                         NOW - timedelta(hours=5))])
    monkeypatch.setattr(sys, "argv",
                        ["timeline_browser_draft.py", "--log", str(log),
                         "--reverse"])
    tb.main()
    out = capsys.readouterr().out
    assert "newest first" in out
    assert out.index("new.txt") < out.index("old.txt")


def test_event_filter(tmp_path, capsys, monkeypatch):
    log = tmp_path / "e.jsonl"
    write_log(log, [echo("a.txt", "pinned", 0.0, 0.0, NOW),
                    echo("b.txt", "observed", 0.0, 1.0, NOW),
                    echo("c.txt", "pinned", 0.0, 0.0, NOW)])
    monkeypatch.setattr(sys, "argv",
                        ["timeline_browser_draft.py", "--log", str(log),
                         "--event", "pinned"])
    tb.main()
    out = capsys.readouterr().out
    assert "2 echoes" in out
    assert "a.txt" in out and "c.txt" in out
    assert "b.txt" not in out


def test_object_filter_is_substring(tmp_path, capsys, monkeypatch):
    log = tmp_path / "e.jsonl"
    write_log(log, [echo("starscape", "rendered", 8.0, 8.5, NOW),
                    echo("other.txt", "scanned", 0.0, 0.0, NOW)])
    monkeypatch.setattr(sys, "argv",
                        ["timeline_browser_draft.py", "--log", str(log),
                         "--object", "STAR"])  # case-insensitive
    tb.main()
    out = capsys.readouterr().out
    assert "1 echoes" in out
    assert "starscape" in out
    assert "other.txt" not in out


def test_groups_by_date(tmp_path, capsys, monkeypatch):
    log = tmp_path / "e.jsonl"
    write_log(log, [echo("a.txt", "scanned", 0.0, 0.0,
                         NOW - timedelta(days=1)),
                    echo("b.txt", "scanned", 0.0, 0.0, NOW)])
    monkeypatch.setattr(sys, "argv",
                        ["timeline_browser_draft.py", "--log", str(log)])
    tb.main()
    out = capsys.readouterr().out
    yesterday = (NOW - timedelta(days=1)).strftime("%Y-%m-%d")
    today = NOW.strftime("%Y-%m-%d")
    assert f"--- {yesterday} ---" in out
    assert f"--- {today} ---" in out


def test_empty_result_reports_no_match(tmp_path, capsys, monkeypatch):
    log = tmp_path / "e.jsonl"
    write_log(log, [echo("a.txt", "scanned", 0.0, 0.0, NOW)])
    monkeypatch.setattr(sys, "argv",
                        ["timeline_browser_draft.py", "--log", str(log),
                         "--event", "reaped"])
    tb.main()
    out = capsys.readouterr().out
    assert "no echoes match" in out


def test_format_ago():
    now = datetime(2026, 10, 17, 9, 0, tzinfo=timezone.utc)
    assert tb.format_ago(iso(now - timedelta(seconds=30)), now=now) == "30s ago"
    assert tb.format_ago(iso(now - timedelta(minutes=5)), now=now) == "5m ago"
    assert tb.format_ago(iso(now - timedelta(hours=3)), now=now) == "3h ago"
    assert tb.format_ago(iso(now - timedelta(days=2)), now=now) == "2d ago"
    assert tb.format_ago("not-a-timestamp") == "?"
