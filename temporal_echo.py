#!/usr/bin/env python3
"""
TEMPORAL ECHO - minimal recorder (v0.1)
=======================================
The first version's job is capture, not analysis.

Every echo is append-only: no updates, no deletion.
Gravity describes the universe now.
Echoes preserve how it became that way.

    "A living universe is not defined by where things are.
     It is defined by how they got there."

Usage:
    python temporal_echo.py <object> [event] <gravity_before> <gravity_after>
    python temporal_echo.py --log <path> <object> [event] <gravity_before> <gravity_after>
    python temporal_echo.py --report [--log <path>]

Each echo records:
    timestamp, object, event, gravity_before, gravity_after
"""

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LOG = Path(__file__).parent / "temporal-echoes.jsonl"


def validate_log_path(path_str, check_writable=True):
    """Fail early on bad log paths. Returns the resolved Path."""
    path = Path(path_str)

    if path.exists() and path.is_dir():
        raise ValueError(f"Log path is a directory: {path}")

    if path.suffix.lower() != ".jsonl":
        raise ValueError(f"Log file must end with .jsonl: {path}")

    if check_writable:
        parent = path.parent
        try:
            parent.mkdir(parents=True, exist_ok=True)
            probe = parent / ".write_test"
            probe.touch(exist_ok=True)
            probe.unlink()
        except Exception as e:
            raise ValueError(f"Cannot write to directory '{parent}': {e}")

    return path


def validate_gravity(name, value):
    """Gravity values must be finite numbers. NaN and infinity
    would corrupt the JSONL stream, so they are rejected."""
    value = float(value)
    if math.isnan(value):
        raise ValueError(f"{name} cannot be NaN")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def record_echo(obj_name, event, gravity_before, gravity_after, log_path=None):
    """Append one echo. Returns (echo, resolved log path).

    log_path is optional: library callers who don't specify one
    get the default log. The CLI always passes its validated path.
    """
    log_path = Path(log_path) if log_path else DEFAULT_LOG
    gravity_before = validate_gravity("gravity_before", gravity_before)
    gravity_after = validate_gravity("gravity_after", gravity_after)
    echo = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "object": obj_name,
        "event": event,
        "gravity_before": gravity_before,
        "gravity_after": gravity_after,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(echo) + "\n")
    return echo, log_path


def report(log_path, limit=20):
    """Show the most recent echoes, oldest first."""
    if not log_path.exists():
        print("No echoes yet. The universe has no memory.")
        return
    lines = [l for l in log_path.read_text(encoding="utf-8").strip().split("\n") if l]
    if not lines:
        print("No echoes yet. The universe has no memory.")
        return
    for line in lines[-limit:]:
        e = json.loads(line)
        print(f"{e['timestamp']}  {e['object']:<22} {e['event']:<12} "
              f"{e['gravity_before']:.1f} -> {e['gravity_after']:.1f}")


def main():
    parser = argparse.ArgumentParser(
        description="Dark Shield Temporal Echo Recorder"
    )
    parser.add_argument(
        "--log",
        default=str(DEFAULT_LOG),
        help="JSONL echo log path (default: temporal-echoes.jsonl)",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Show recent echoes instead of recording",
    )
    parser.add_argument(
        "object",
        nargs="?",
        default=None,
        help="Star, pulsar, galaxy, or other object name",
    )
    parser.add_argument(
        "event",
        nargs="?",
        default="observed",
        help="Event type (opened, modified, rendered, evaluated, etc.)",
    )
    parser.add_argument(
        "gravity_before",
        nargs="?",
        type=float,
        help="Gravity value before event (required when recording; must be finite)",
    )
    parser.add_argument(
        "gravity_after",
        nargs="?",
        type=float,
        help="Gravity value after event (required when recording; must be finite)",
    )
    args = parser.parse_args()

    try:
        log_path = validate_log_path(args.log, check_writable=not args.report)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if args.report:
        report(log_path)
        return

    if not args.object:
        parser.error("object is required when recording an echo")

    if args.gravity_before is None or args.gravity_after is None:
        parser.error(
            "gravity_before and gravity_after are required when recording an echo"
        )

    try:
        echo, log_path = record_echo(
            args.object,
            args.event,
            args.gravity_before,
            args.gravity_after,
            log_path=log_path,
        )
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print("\nEcho Recorded")
    print("-------------")
    print(f"log: {log_path}")
    for k, v in echo.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
