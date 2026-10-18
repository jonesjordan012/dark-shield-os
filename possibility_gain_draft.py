#!/usr/bin/env python3
"""
possibility_gain_draft.py -- measure what exploration produces.

Possibility Gain evaluates exploratory events per object:
    PossibilityGain = (bonds x 1) + (returns x 3) + (pins x 10)

RULED 2026-10-15 (canon). Weights and thresholds are universe policy,
tunable from birth. All three inputs are now measured:
  - bonds_created: from gravity.db (bond counts)
  - pins_received: from temporal-echoes.jsonl (pinned events)
  - returns:       from temporal-echoes.jsonl (attention sessions)

RULED 2026-10-17: a return is any observation of an object in a new
attention session after its initial session. Sessions are grouped by
inactivity gap (default 60 minutes). return_count = session_count - 1.
No new event types. No watchers. Derived from echoes alone.

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
from datetime import datetime, timezone

# --- Universe policy (tunable from birth, per the ruled spec) ---
BOND_WEIGHT = 1
RETURN_WEIGHT = 3
PIN_WEIGHT = 10
GRADUATION_THRESHOLD = 25
OBSERVATION_WINDOW_DAYS = 30  # not enforced in v0.1; recorded for the reaper
SESSION_GAP_MINUTES = 60  # inactivity gap that starts a new attention session

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


def all_observed_objects(log_path):
    """Every object name ever seen in the echo log (by basename).

    RULED 2026-10-17: observation creates visibility, not score.
    Objects with no bonds and no pins appear as CANDIDATE with score 0,
    rather than vanishing from the possibility ontology.
    """
    objects = set()
    if not os.path.isfile(log_path):
        return objects
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                obj = str(e.get("object", ""))
                if obj:
                    objects.add(os.path.basename(obj))
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
    return objects


def lifecycle_state(score):
    if score >= GRADUATION_THRESHOLD:
        return "GRADUATED"
    if score > 0:
        return "OBSERVED"
    return "CANDIDATE"


def session_counts(log_path, gap_minutes=SESSION_GAP_MINUTES):
    """Group each object's echoes into attention sessions.

    RULED 2026-10-17: a return is an observation in a new session after
    the initial session. A new session starts when the gap between
    consecutive echoes for the same object exceeds gap_minutes.

    Returns {basename: (session_count, return_count)} where
    return_count = max(0, session_count - 1).
    """
    # Collect timestamps per object.
    times = {}
    if not os.path.isfile(log_path):
        return {}
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                obj = str(e.get("object", ""))
                ts_raw = e.get("timestamp", "")
                if not obj or not ts_raw:
                    continue
                dt = datetime.fromisoformat(ts_raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                base = os.path.basename(obj)
                times.setdefault(base, []).append(dt.timestamp())
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue

    gap_seconds = gap_minutes * 60
    result = {}
    for base, stamps in times.items():
        stamps.sort()
        sessions = 1
        for prev, curr in zip(stamps, stamps[1:]):
            if curr - prev > gap_seconds:
                sessions += 1
        result[base] = (sessions, max(0, sessions - 1))
    return result


def main():
    p = argparse.ArgumentParser(
        description="Compute Possibility Gain per object.")
    p.add_argument("--log", default=DEFAULT_LOG,
                   help="Path to echo log (default: temporal-echoes.jsonl)")
    p.add_argument("--db", default=None,
                   help="Path to gravity.db (auto-detected if omitted)")
    p.add_argument("--session-gap", type=int, default=SESSION_GAP_MINUTES,
                   help="Minutes of inactivity that start a new attention "
                        f"session (default: {SESSION_GAP_MINUTES})")
    args = p.parse_args()

    gpath = gravity_db_path(args.db)
    bonds = bond_counts(gpath)
    pins = pin_counts(args.log)
    sessions = session_counts(args.log, gap_minutes=args.session_gap)

    # RULED 2026-10-17: the population is every object ever observed,
    # not just those with bonds or pins. Observation creates visibility
    # (CANDIDATE state), not score. The formula is unchanged.
    objects = set(bonds) | set(pins) | all_observed_objects(args.log)

    rows = []
    for obj in objects:
        b = bonds.get(obj, 0)
        _, r = sessions.get(obj, (1, 0))
        pn = pins.get(obj, 0)
        score = b * BOND_WEIGHT + r * RETURN_WEIGHT + pn * PIN_WEIGHT
        rows.append((obj, b, r, pn, score, lifecycle_state(score)))

    rows.sort(key=lambda row: row[4], reverse=True)

    print("POSSIBILITY GAIN v0.1 -- what did exploration produce?\n")
    print(f"Weights: bonds x{BOND_WEIGHT}  returns x{RETURN_WEIGHT}  "
          f"pins x{PIN_WEIGHT}   |   Graduation threshold: "
          f"{GRADUATION_THRESHOLD}")
    print(f"Sessions: {args.session_gap}-minute inactivity gap; "
          f"returns = sessions - 1.\n")

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
