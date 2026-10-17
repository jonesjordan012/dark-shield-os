#!/usr/bin/env python3
"""
possibility_gain_draft.py -- measure what exploration produces.

Possibility Gain evaluates exploratory events per object:
    PossibilityGain = (bonds x 1) + (returns x 3) + (pins x 10)

RULED 2026-10-15 (canon). Weights and thresholds are universe policy,
tunable from birth. This draft implements what is measurable today:
  - bonds_created: from gravity.db (implemented)
  - pins_received: from temporal-echoes.jsonl (implemented)
  - returns:       PENDING INSTRUMENTATION (sensor not built yet)

Lifecycle:
    Candidate  (score 0 -- introduced, no evidence yet)
    Observed   (score > 0 but below graduation threshold)
    Graduated  (score >= threshold -- enters stable gravity)

Validation belongs to the Citizen alone. The system reports;
the Citizen decides.

Usage:
    python possibility_gain_draft.py
    python possibility_gain_draft.py --log my-echoes.jsonl --db my-gravity.db
"""

import argparse
import json
import os
import sqlite3
import sys

# --- Universe policy (tunable from birth, per the ruled spec) ---
BOND_WEIGHT = 1
RETURN_WEIGHT = 3
PIN_WEIGHT = 10
GRADUATION_THRESHOLD = 25
OBSERVATION_WINDOW_DAYS = 30  # not enforced in v0.1; recorded for the reaper

DEFAULT_LOG = "temporal-echoes.jsonl"


def here():
    return os.path.dirname(os.path.abspath(__file__))


def gravity_db_path(explicit=None):
    if explicit and os.path.isfile(explicit):
        return explicit
    for name in ("gravity.db", "gravity"):
        guess = os.path.join(here(), name)
        if os.path.isfile(guess):
            return guess
    return None


def bond_counts(gpath):
    """Per-basename gravity: total bonds each file participates in."""
    counts = {}
    if not gpath:
        return counts
    conn = sqlite3.connect(gpath)
    try:
        rows = conn.execute(
            "SELECT file_a, file_b, COUNT(*) FROM pairs "
            "GROUP BY file_a, file_b").fetchall()
    except sqlite3.Error:
        rows = []
    conn.close()
    for a, b, c in rows:
        for name in (a, b):
            base = os.path.basename(name)
            counts[base] = counts.get(base, 0) + c
    return counts


def pin_counts(log_path):
    """Count pinned events per object from the echo log."""
    pins = {}
    if not os.path.isfile(log_path):
        return pins
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                if e.get("event") == "pinned":
                    obj = str(e.get("object", ""))
                    base = os.path.basename(obj)
                    pins[base] = pins.get(base, 0) + 1
                    # Also count the full object name, in case it differs.
                    if obj != base:
                        pins[obj] = pins.get(obj, 0) + 1
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
    return pins


def lifecycle_state(score):
    if score >= GRADUATION_THRESHOLD:
        return "GRADUATED"
    if score > 0:
        return "OBSERVED"
    return "CANDIDATE"


def main():
    p = argparse.ArgumentParser(
        description="Compute Possibility Gain per object.")
    p.add_argument("--log", default=DEFAULT_LOG,
                   help="Path to echo log (default: temporal-echoes.jsonl)")
    p.add_argument("--db", default=None,
                   help="Path to gravity.db (auto-detected if omitted)")
    args = p.parse_args()

    gpath = gravity_db_path(args.db)
    bonds = bond_counts(gpath)
    pins = pin_counts(args.log)

    # Every object known to either source gets a score.
    objects = set(bonds) | set(pins)

    rows = []
    for obj in objects:
        b = bonds.get(obj, 0)
        r = 0  # returns: pending instrumentation
        pn = pins.get(obj, 0)
        score = b * BOND_WEIGHT + r * RETURN_WEIGHT + pn * PIN_WEIGHT
        rows.append((obj, b, r, pn, score, lifecycle_state(score)))

    rows.sort(key=lambda row: row[4], reverse=True)

    print("POSSIBILITY GAIN v0.1 -- what did exploration produce?\n")
    print(f"Weights: bonds x{BOND_WEIGHT}  returns x{RETURN_WEIGHT}  "
          f"pins x{PIN_WEIGHT}   |   Graduation threshold: "
          f"{GRADUATION_THRESHOLD}")
    print("Returns: pending instrumentation (counted as 0).\n")

    print(f"{'score':>6}  {'state':<9}  {'bnd':>3}  {'ret':>3}  "
          f"{'pin':>3}  object")
    for obj, b, r, pn, score, state in rows:
        obj_display = obj if len(obj) <= 45 else obj[:42] + "..."
        print(f"{score:>6}  {state:<9}  {b:>3}  {r:>3}  "
              f"{pn:>3}  {obj_display}")

    graduated = sum(1 for row in rows if row[5] == "GRADUATED")
    observed = sum(1 for row in rows if row[5] == "OBSERVED")
    candidate = sum(1 for row in rows if row[5] == "CANDIDATE")

    print(f"\n{len(rows)} objects: {graduated} graduated, "
          f"{observed} observed, {candidate} candidate.")
    if gpath:
        print(f"Gravity db: {gpath}")
    else:
        print("Gravity db: not found (bond counts = 0).")
    print("Gravity preserves. Antigravity proposes. The Citizen decides.")


if __name__ == "__main__":
    main()
