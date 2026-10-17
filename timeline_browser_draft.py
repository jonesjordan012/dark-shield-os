#!/usr/bin/env python3
"""
timeline_browser_draft.py -- walk through Temporal Echoes in chronological order.

Reads temporal-echoes.jsonl and displays echoes oldest-first, so you can
watch the universe's history unfold. This is the first real implementation
of Temporal Echoes as a navigable memory, not just a log.

Usage:
    python timeline_browser_draft.py
    python timeline_browser_draft.py --log my-echoes.jsonl
    python timeline_browser_draft.py --reverse         # newest first
    python timeline_browser_draft.py --event pinned   # filter by event
    python timeline_browser_draft.py --object starscape  # filter by object
"""

import argparse
import json
import sys
from datetime import datetime, timezone


def parse_args():
    p = argparse.ArgumentParser(
        description="Walk through Temporal Echoes in chronological order."
    )
    p.add_argument("--log", default="temporal-echoes.jsonl",
                   help="Path to echo log (default: temporal-echoes.jsonl)")
    p.add_argument("--reverse", action="store_true",
                   help="Show newest first instead of oldest first")
    p.add_argument("--event", default=None,
                   help="Only show echoes with this event type")
    p.add_argument("--object", default=None,
                   help="Only show echoes for this object (substring match)")
    return p.parse_args()


REQUIRED_FIELDS = ("timestamp", "object", "event",
                   "gravity_before", "gravity_after")


def load_echoes(path):
    """Read all echoes from the JSONL log. Returns list of dicts.

    Skips lines that are not valid JSON or do not have the echo schema.
    A reader must not crash on a corrupt log; history is append-only
    and readers adapt.
    """
    echoes = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    if not isinstance(e, dict):
                        raise ValueError("not a JSON object")
                    for field in REQUIRED_FIELDS:
                        if field not in e:
                            raise ValueError(f"missing field: {field}")
                    echoes.append(e)
                except (json.JSONDecodeError, ValueError) as exc:
                    print(f"Warning: skipping malformed line {line_num}: {exc}",
                          file=sys.stderr)
    except FileNotFoundError:
        print(f"No echo log found at {path}", file=sys.stderr)
        sys.exit(1)
    return echoes


def format_time(iso_str):
    """Convert ISO timestamp to HH:MM:SS local time."""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%H:%M:%S")
    except (ValueError, TypeError):
        return "?"


def format_ago(iso_str, now=None):
    """Human-readable relative time ('3h ago').

    `now` is a datetime for testability; defaults to the actual present.
    """
    try:
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = now if now is not None else datetime.now(timezone.utc)
        delta = now - dt
        seconds = int(delta.total_seconds())
        if seconds < 0:
            return "just now"
        if seconds < 60:
            return f"{seconds}s ago"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        elif seconds < 86400:
            return f"{seconds // 3600}h ago"
        else:
            return f"{seconds // 86400}d ago"
    except (ValueError, TypeError):
        return "?"


def main():
    args = parse_args()
    echoes = load_echoes(args.log)

    # Filter by event type and/or object substring.
    if args.event:
        echoes = [e for e in echoes if e.get("event") == args.event]
    if args.object:
        needle = args.object.lower()
        echoes = [e for e in echoes
                  if needle in str(e.get("object", "")).lower()]

    # Sort chronologically (oldest first by default).
    echoes.sort(key=lambda e: e.get("timestamp", ""), reverse=args.reverse)

    direction = "newest first" if args.reverse else "oldest first"
    print(f"TIMELINE -- {len(echoes)} echoes ({direction})")

    if not echoes:
        print("  (no echoes match)")
        return

    # Group by calendar date so multi-day histories stay readable.
    current_date = None
    for e in echoes:
        ts = e.get("timestamp", "")
        try:
            date_str = datetime.fromisoformat(ts).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            date_str = "?"

        if date_str != current_date:
            current_date = date_str
            print(f"\n--- {date_str} ---")

        obj = str(e.get("object", "?"))
        event = str(e.get("event", "?"))
        gb = e.get("gravity_before", "?")
        ga = e.get("gravity_after", "?")

        # Truncate very long object names so columns stay aligned.
        obj_display = obj if len(obj) <= 40 else obj[:37] + "..."

        print(f"  {format_time(ts)}  {format_ago(ts):>8}  "
              f"{obj_display:<43} {event:<10} {gb} -> {ga}")

    print(f"\n{len(echoes)} echoes shown.")
    print("The recorder gave memory. The timeline lets you walk through it.")


if __name__ == "__main__":
    main()
