#!/usr/bin/env python3
"""
ATTENTION MAP - draft v0.1 (PROPOSAL, not yet installed)
========================================================
The first reader of echo history.

The recorder gave Dark Shield memory. This is the first thing that
reads that memory and LEARNS from it instead of just showing it.

Jordan's ruled formula (2026-10-16):

    attention = gravity + recency + repetition

Each term is a different dimension:

    gravity    = how connected?   (measured bond strength, from the echoes)
    recency    = how recent?      (echoes weighted by the ruled 7-day half-life;
                                   a week-old echo counts half, a fresh one ~1)
    repetition = how often?       (raw echo count: what keeps happening?)

The combined score begins to answer: "how important right now?"

Sections:
    TOP ATTENTION   - ranked by the full score (what matters)
    ORBITING LATELY - ranked by recency (what you've been circling)
    COOLING OFF     - strong gravity, faint recent echoes (what's fading)
    HEATING UP      - strong recent echoes, weak gravity (unexpectedly active)

Design notes:
- ONE input: the echo log. This component reads history; it does not
  re-measure gravity.db. (Fusing both is the decay visualizer's job.)
- "gravity" for an object = the strongest gravity_after ever recorded
  for it. That number was MEASURED when the echo was written -- the
  reader never manufactures observations, it only remembers them.
- Never writes to the log. Readers look; they don't touch.
- Thresholds for cooling/heating are first guesses (tunable), not law.

Usage:
    python attention_map_draft.py [--log PATH] [--half-life DAYS] [--limit N]

Standard library only.
"""

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LOG = os.path.join(SCRIPT_DIR, "temporal-echoes.jsonl")

HALF_LIFE_DAYS = 7.0   # ruled default 2026-10-16, tunable by observation
LIMIT = 15

# First guesses for the cooling/heating sections. Tunable, not law.
COOL_GRAVITY = 2.0     # at least this connected...
COOL_RECENCY = 0.5     # ...but barely touched lately -> cooling off
HEAT_RECENCY = 2.0     # touched this much lately...
                       # ...while gravity stays below it -> heating up


def parse_ts(ts_str):
    """Parse an ISO timestamp from the echo log. Returns epoch seconds."""
    try:
        dt = datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def read_echoes(log_path):
    """Read the echo log. Forgiving: a reader skips lines it can't read
    and says how many it skipped. History is append-only; readers adapt."""
    echoes, skipped = [], 0
    if not os.path.isfile(log_path):
        return echoes, skipped
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                ts = parse_ts(e["timestamp"])
                if ts is None:
                    raise ValueError("bad timestamp")
                gb = float(e["gravity_before"])
                ga = float(e["gravity_after"])
                if not (math.isfinite(gb) and math.isfinite(ga)):
                    raise ValueError("non-finite gravity")
                echoes.append({
                    "ts": ts,
                    "object": str(e["object"]),
                    "event": str(e["event"]),
                    "gravity_before": gb,
                    "gravity_after": ga,
                })
            except (ValueError, KeyError, TypeError):
                skipped += 1
    return echoes, skipped


def attention_scores(echoes, half_life_days=HALF_LIFE_DAYS, now=None):
    """Fuse gravity + recency + repetition into one score per object."""
    now = now if now is not None else datetime.now(timezone.utc).timestamp()
    stats = {}
    for e in echoes:
        s = stats.setdefault(e["object"], {
            "count": 0, "recency": 0.0, "gravity": 0.0, "last_seen": 0.0,
        })
        s["count"] += 1
        age_days = max(0.0, (now - e["ts"]) / 86400.0)
        s["recency"] += 0.5 ** (age_days / half_life_days)
        # The strongest gravity ever MEASURED for this object.
        # Measured then, remembered now -- never manufactured.
        s["gravity"] = max(s["gravity"], e["gravity_after"])
        s["last_seen"] = max(s["last_seen"], e["ts"])
    for s in stats.values():
        s["attention"] = s["gravity"] + s["recency"] + s["count"]
    return stats


def ago(ts, now):
    """Plain-language age: '3h ago', '2d ago'."""
    secs = max(0, now - ts)
    if secs < 3600:
        return f"{int(secs // 60)}m ago"
    if secs < 86400:
        return f"{int(secs // 3600)}h ago"
    return f"{secs / 86400:.1f}d ago"


def report(log_path=DEFAULT_LOG, half_life_days=HALF_LIFE_DAYS, limit=LIMIT,
           now=None):
    echoes, skipped = read_echoes(log_path)
    now = now if now is not None else datetime.now(timezone.utc).timestamp()
    if not echoes:
        print("No echoes yet. The universe has no memory to read.")
        return
    stats = attention_scores(echoes, half_life_days, now)
    ranked = sorted(stats.items(), key=lambda kv: kv[1]["attention"],
                    reverse=True)

    print("ATTENTION MAP v0.1 -- what keeps happening?\n")
    print(f"{'attn':>6}  {'grav':>5}  {'rec':>5}  {'rep':>3}  last seen   object")
    for obj, s in ranked[:limit]:
        print(f"{s['attention']:>6.1f}  {s['gravity']:>5.1f}  "
              f"{s['recency']:>5.1f}  {s['count']:>3}  "
              f"{ago(s['last_seen'], now):<9}  {obj}")

    orbiting = sorted(stats.items(), key=lambda kv: kv[1]["recency"],
                      reverse=True)[:limit]
    print("\n-- ORBITING LATELY (most recent attention) --")
    for obj, s in orbiting:
        if s["recency"] > 0:
            print(f"  rec={s['recency']:.1f}  {ago(s['last_seen'], now):<9}  {obj}")

    cooling = [(o, s) for o, s in ranked
               if s["gravity"] >= COOL_GRAVITY and s["recency"] <= COOL_RECENCY]
    print("\n-- COOLING OFF (was connected, fading now) --")
    if cooling:
        for obj, s in cooling[:limit]:
            print(f"  grav={s['gravity']:.1f} rec={s['recency']:.1f}  {obj}")
    else:
        print("  nothing cooling -- every bond is still warm")

    heating = [(o, s) for o, s in ranked
               if s["recency"] >= HEAT_RECENCY and s["recency"] > s["gravity"]]
    print("\n-- HEATING UP (active now, bonds still weak) --")
    if heating:
        for obj, s in heating[:limit]:
            print(f"  rec={s['recency']:.1f} grav={s['gravity']:.1f}  {obj}")
    else:
        print("  nothing heating -- the active stars already have bonds")

    print(f"\n{len(echoes)} echoes, {len(stats)} objects, "
          f"half-life {half_life_days} days.", end="")
    if skipped:
        print(f" {skipped} unreadable line(s) skipped.", end="")
    print("\nThe recorder gave memory. This gives it meaning.")


def main(argv):
    parser = argparse.ArgumentParser(
        description="Dark Shield Attention Map v0.1 (draft)")
    parser.add_argument("--log", default=DEFAULT_LOG,
                        help="JSONL echo log path")
    parser.add_argument("--half-life", type=float, default=HALF_LIFE_DAYS,
                        help="recency half-life in days (default: 7.0, ruled)")
    parser.add_argument("--limit", type=int, default=LIMIT,
                        help="rows per section")
    args = parser.parse_args(argv[1:])
    if args.half_life <= 0:
        print("ERROR: --half-life must be positive", file=sys.stderr)
        sys.exit(1)
    report(args.log, args.half_life, args.limit)


if __name__ == "__main__":
    main(sys.argv)
