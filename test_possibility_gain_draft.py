"""Tests for possibility_gain_draft.py -- what did exploration produce?

Synthetic gravity.db and echo logs only. Each test builds its own
small universe. Returns are pending instrumentation and must read 0.
"""
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import possibility_gain_draft as pg


def iso(dt):
    return dt.isoformat()


NOW = datetime(2026, 10, 17, 9, 0, tzinfo=timezone.utc)


def make_db(path, pairs):
    """Create a gravity.db with the given (file_a, file_b) pairs."""
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE pairs (file_a TEXT, file_b TEXT)")
    for a, b in pairs:
        conn.execute("INSERT INTO pairs VALUES (?, ?)", (a, b))
    conn.commit()
    conn.close()


def write_log(path, echoes):
    with open(path, "w", encoding="utf-8") as f:
        for e in echoes:
            f.write(json.dumps(e) + "\n")


def echo(obj, event, gb, ga):
    return {"timestamp": iso(NOW), "object": obj, "event": event,
            "gravity_before": gb, "gravity_after": ga}


def test_formula_is_bonds_plus_pins(tmp_path, capsys, monkeypatch):
    """Ruled formula: bonds x1 + returns x3 + pins x10. Returns pending = 0."""
    db = tmp_path / "gravity.db"
    make_db(db, [("a.txt", "b.txt"), ("a.txt", "c.txt")])  # a.txt: 2 bonds
    log = tmp_path / "e.jsonl"
    write_log(log, [echo("a.txt", "pinned", 0.0, 0.0)])    # a.txt: 1 pin
    monkeypatch.setattr(sys, "argv",
                        ["possibility_gain_draft.py",
                         "--log", str(log), "--db", str(db)])
    pg.main()
    out = capsys.readouterr().out
    # a.txt: 2 bonds x1 + 0 returns x3 + 1 pin x10 = 12
    assert "12" in out
    assert "a.txt" in out


def test_returns_are_zero_and_disclosed(tmp_path, capsys, monkeypatch):
    """The spec says returns are pending instrumentation. The tool must
    say so, not silently compute them."""
    db = tmp_path / "gravity.db"
    make_db(db, [])
    log = tmp_path / "e.jsonl"
    write_log(log, [])
    monkeypatch.setattr(sys, "argv",
                        ["possibility_gain_draft.py",
                         "--log", str(log), "--db", str(db)])
    pg.main()
    out = capsys.readouterr().out
    assert "pending instrumentation" in out


def test_lifecycle_graduated(tmp_path):
    assert pg.lifecycle_state(25) == "GRADUATED"
    assert pg.lifecycle_state(100) == "GRADUATED"


def test_lifecycle_observed(tmp_path):
    assert pg.lifecycle_state(1) == "OBSERVED"
    assert pg.lifecycle_state(24) == "OBSERVED"


def test_lifecycle_candidate(tmp_path):
    assert pg.lifecycle_state(0) == "CANDIDATE"


def test_pin_weight_dominates(tmp_path, capsys, monkeypatch):
    """One pin (x10) outweighs nine bonds (x1). Deliberate acts count."""
    db = tmp_path / "gravity.db"
    make_db(db, [("busy.txt", f"f{i}.txt") for i in range(9)])
    log = tmp_path / "e.jsonl"
    write_log(log, [echo("chosen.txt", "pinned", 0.0, 0.0)])
    monkeypatch.setattr(sys, "argv",
                        ["possibility_gain_draft.py",
                         "--log", str(log), "--db", str(db)])
    pg.main()
    out = capsys.readouterr().out
    # chosen.txt (10) must rank above busy.txt (9)
    assert out.index("chosen.txt") < out.index("busy.txt")


def test_bond_counts_per_basename(tmp_path):
    db = tmp_path / "gravity.db"
    make_db(db, [("C:/dir/a.txt", "b.txt"), ("a.txt", "c.txt")])
    counts = pg.bond_counts(str(db))
    # Both pairs involve basename a.txt -> 2 bonds
    assert counts["a.txt"] == 2
    assert counts["b.txt"] == 1


def test_bond_counts_missing_db(tmp_path):
    assert pg.bond_counts(str(tmp_path / "absent.db")) == {}
    assert pg.bond_counts(None) == {}


def test_pin_counts_from_echo_log(tmp_path):
    log = tmp_path / "e.jsonl"
    write_log(log, [echo("a.txt", "pinned", 0.0, 0.0),
                    echo("a.txt", "pinned", 0.0, 0.0),
                    echo("b.txt", "observed", 0.0, 1.0)])
    pins = pg.pin_counts(str(log))
    assert pins["a.txt"] == 2
    assert "b.txt" not in pins


def test_pin_counts_missing_log(tmp_path):
    assert pg.pin_counts(str(tmp_path / "absent.jsonl")) == {}


def test_report_counts_lifecycle(tmp_path, capsys, monkeypatch):
    db = tmp_path / "gravity.db"
    # rich.txt: 30 bonds -> 30 points -> GRADUATED
    make_db(db, [("rich.txt", f"f{i}.txt") for i in range(30)])
    log = tmp_path / "e.jsonl"
    write_log(log, [echo("poor.txt", "pinned", 0.0, 0.0)])  # 10 pts OBSERVED
    monkeypatch.setattr(sys, "argv",
                        ["possibility_gain_draft.py",
                         "--log", str(log), "--db", str(db)])
    pg.main()
    out = capsys.readouterr().out
    assert "GRADUATED" in out
    assert "OBSERVED" in out
    assert "1 graduated" in out


def test_observed_but_bondless_object_is_candidate(tmp_path, capsys,
                                                  monkeypatch):
    """RULED 2026-10-17: observation creates visibility, not score.
    An object seen in the echo log with no bonds and no pins appears
    as CANDIDATE with score 0, rather than vanishing."""
    db = tmp_path / "gravity.db"
    make_db(db, [])
    log = tmp_path / "e.jsonl"
    # merely observed -- no bonds, no pins
    write_log(log, [echo("noticed.txt", "observed", 1.0, 2.0)])
    monkeypatch.setattr(sys, "argv",
                        ["possibility_gain_draft.py",
                         "--log", str(log), "--db", str(db)])
    pg.main()
    out = capsys.readouterr().out
    assert "noticed.txt" in out
    assert "CANDIDATE" in out


def test_all_observed_objects(tmp_path):
    log = tmp_path / "e.jsonl"
    write_log(log, [echo("a.txt", "observed", 0.0, 1.0),
                    echo("b.txt", "pinned", 0.0, 0.0),
                    echo("a.txt", "scanned", 0.0, 0.0)])
    objects = pg.all_observed_objects(str(log))
    assert objects == {"a.txt", "b.txt"}


def test_all_observed_objects_missing_log(tmp_path):
    assert pg.all_observed_objects(str(tmp_path / "absent.jsonl")) == set()
