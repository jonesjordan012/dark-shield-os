#!/usr/bin/env python3
"""
DARK SHIELD - skyrank.py
========================
The selection engine: how the sky chooses its stars.

Implements the fire-code ruling (canon 2026-10-15) and Amendment 1.
When the sky overflows its limit, selection proceeds in phases:

  PHASE 1  Pinned files. Always included; gravity can never displace
           a pin. Pinning is a Citizen declaration (sovereign act).
  PHASE 2  Remaining slots = limit - pinned.
  PHASE 3  85% of remaining slots go to the highest-gravity files.
           Gravity = measured bond counts from gravity.db (v1: the only
           factor with a real measurement behind it).
  PHASE 4  15% of remaining slots go to antigravity candidates --
           actual reserved slots, so exploration survives monopoly.
  PHASE 5  Every newly discovered file gets a first-encounter
           antigravity bonus: priority consideration for a slot.
  PHASE 6  After first presentation the bonus decays each selection
           pass. Never used -> fades. Used -> builds bonds.
  PHASE 7  Alphabetical order only when everything else ties.

"Dark Shield decides" means the Citizen's own remembered behavior
decides. The engine reveals; it never judges. (NPU invariant holds.)

Tunable universe constants live at the top. Nothing here is canon
except the phase structure and the tie-break hierarchy.

Usage:
    python skyrank.py scan <dir> [--limit N] [--depth N]
                                [--gravitydb PATH]
    python skyrank.py pin <name>        pin a star (always visible)
    python skyrank.py unpin <name>
    python skyrank.py report            pins, ratios, tracked stars

Standard library only. State lives in skyrank.db, next to this script.
"""

import math
import os
import sqlite3
import sys
import time
from temporal_echo import record_echo


# ---------------------------------------------------------------------------
# Tunable universe constants. First guesses, not law.
# ---------------------------------------------------------------------------
LIMIT = 250
GRAVITY_RATIO = 0.85
ANTIGRAVITY_RATIO = 0.15   # = 1 - GRAVITY_RATIO; the other slot share

BONUS_NEW = 100            # never presented
BONUS_SEEN_ONCE = 50       # presented once
BONUS_SEEN_MULTI = 10      # presented 2+ times, still bondless
BONUS_EMERGING = 25        # 1-2 bonds: deliberate double-count, a thumb
                           # on the scale for the young (tunable)
ESTABLISHED_AT = 3         # bonds >= this: established, antigravity 0
DECAY = 0.8                # bonus multiplier per selection pass after
                           # first presentation

SKY_DB = "skyrank.db"


# ---------------------------------------------------------------------------
# The recursive walk (lesson two, reused).
# ---------------------------------------------------------------------------
def walk_files(root, max_depth=3):
    found = []

    def walk(path, depth):
        if depth > max_depth:
            return
        try:
            entries = sorted(os.listdir(path))
        except OSError:
            return
        for name in entries:
            full = os.path.join(path, name)
            try:
                if os.path.isfile(full) and not os.path.islink(full):
                    rel = os.path.relpath(full, root)
                    try:
                        size = os.path.getsize(full)
                    except OSError:
                        size = 0  # a star we cannot weigh still counts
                    found.append((rel, size))
                elif os.path.isdir(full) and not os.path.islink(full):
                    walk(full, depth + 1)
            except OSError:
                continue

    walk(root, 0)
    return found


# ---------------------------------------------------------------------------
# State: skyrank.db next to the script.
# ---------------------------------------------------------------------------
def here():
    return os.path.dirname(os.path.abspath(__file__))


def sky_db():
    conn = sqlite3.connect(os.path.join(here(), SKY_DB))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS pins (name TEXT PRIMARY KEY)")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS stars ("
        " name TEXT PRIMARY KEY,"          # relpath within scanned root
        " first_seen REAL NOT NULL,"       # tie-break #4
        " presentations INTEGER NOT NULL)" # drives bonus tiers + decay
    )
    return conn


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


def is_pinned(pins, rel):
    base = os.path.basename(rel)
    return rel in pins or base in pins


# ---------------------------------------------------------------------------
# The selection engine.
# ---------------------------------------------------------------------------
def select_sky(files, counts, pins, limit, conn, now):
    """Run the seven phases. Returns (pinned, gravity_sel, anti_sel)."""
    # Register newcomers: first encounter.
    for rel, _size in files:
        row = conn.execute(
            "SELECT presentations FROM stars WHERE name=?", (rel,)).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO stars (name, first_seen, presentations)"
                " VALUES (?, ?, 0)", (rel, now))

    def state(rel):
        row = conn.execute(
            "SELECT first_seen, presentations FROM stars WHERE name=?",
            (rel,)).fetchone()
        return row  # (first_seen, presentations)

    def gravity_of(rel):
        return counts.get(os.path.basename(rel), 0)

    def antibonus(rel, pres, bonds):
        # Amendment 1 tiers + decay. Established files compete on
        # gravity alone; the newcomer boost is over for them.
        if bonds >= ESTABLISHED_AT:
            return 0.0
        if pres == 0:
            base = BONUS_NEW
        elif pres == 1:
            base = BONUS_SEEN_ONCE
        else:
            base = BONUS_SEEN_MULTI
        if 0 < bonds < ESTABLISHED_AT:
            base += BONUS_EMERGING  # deliberate double-count
        return base * (DECAY ** max(0, pres - 1))

    scored = []
    for rel, size in files:
        first_seen, pres = state(rel)
        bonds = gravity_of(rel)
        scored.append({
            "name": rel, "size": size,
            "pinned": is_pinned(pins, rel),
            "gravity": bonds,
            "anti": antibonus(rel, pres, bonds),
            "first_seen": first_seen, "pres": pres,
        })

    # PHASE 1: pins sit outside the gravity system entirely.
    pinned = [s for s in scored if s["pinned"]]
    pool = [s for s in scored if not s["pinned"]]

    # PHASE 2: remaining slots.
    remaining = limit - len(pinned)
    overflow = remaining < 0
    remaining = max(0, remaining)

    # PHASES 3+4: reserved slots (floor/ceil so shares never vanish).
    g_slots = math.floor(remaining * GRAVITY_RATIO)
    a_slots = remaining - g_slots

    # PHASE 3: gravity ranking. Ties -> antigravity -> first seen -> name.
    by_gravity = sorted(pool, key=lambda s: (
        -s["gravity"], -s["anti"], s["first_seen"], s["name"]))
    gravity_sel = by_gravity[:g_slots]
    rest = by_gravity[g_slots:]

    # PHASE 4: antigravity ranking over what's left.
    by_anti = sorted(rest, key=lambda s: (
        -s["anti"], -s["gravity"], s["first_seen"], s["name"]))
    anti_sel = by_anti[:a_slots]

    # PHASE 6 bookkeeping: this selection pass counts as a presentation.
    for s in pinned + gravity_sel + anti_sel:
        conn.execute("UPDATE stars SET presentations = presentations + 1 "
                     "WHERE name=?", (s["name"],))
    conn.commit()
    return pinned, gravity_sel, anti_sel, overflow


def cmd_scan(args):
    if not args:
        print("Usage: python skyrank.py scan <dir> [--limit N] [--depth N]"
              " [--gravitydb PATH]")
        return
    root = args[0]
    limit, depth, gpath = LIMIT, 3, None
    i = 1
    while i < len(args):
        if args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1]); i += 2
        elif args[i] == "--depth" and i + 1 < len(args):
            depth = int(args[i + 1]); i += 2
        elif args[i] == "--gravitydb" and i + 1 < len(args):
            gpath = args[i + 1]; i += 2
        else:
            i += 1
    if not os.path.isdir(root):
        print(f"Not a directory: {root}")
        return

    files = walk_files(root, depth)
    gpath = gravity_db_path(gpath)
    counts = bond_counts(gpath)
    conn = sky_db()
    pins = {r[0] for r in conn.execute("SELECT name FROM pins").fetchall()}
    now = time.time()

    pinned, gsel, asel, overflow = select_sky(
        files, counts, pins, limit, conn, now)
    n_tracked = conn.execute("SELECT COUNT(*) FROM stars").fetchone()[0]
    for s in pinned + gsel + asel:
        record_echo(s["name"], "evaluated", s["gravity"], s["gravity"])
    conn.close()

    print(f"SELECTION ENGINE  ({len(files)} files found, limit {limit})")
    if gpath:
        print(f"gravity source: {gpath} "
              f"({sum(counts.values()) // 2} bonds)")
    else:
        print("gravity source: none found -- running on first-encounter "
              "fallback (all scores zero, ties by first seen, then name)")
    if overflow:
        print(f"note: {len(pinned)} pins exceed the limit of {limit}; "
              "sovereign acts outrank the fire code, all pins shown")
    print(f"\n-- PINNED ({len(pinned)}) --")
    for s in pinned:
        print(f"  {s['name']}")
    print(f"\n-- GRAVITY ({len(gsel)}) --")
    for s in gsel:
        print(f"  g={s['gravity']:>4}  {s['name']}")
    print(f"\n-- ANTIGRAVITY ({len(asel)}) --")
    for s in asel:
        why = ("new" if s["pres"] == 0
               else f"seen {s['pres']}x, no bonds yet")
        print(f"  a={s['anti']:>7.1f}  {s['name']}  ({why})")
    print(f"\n{n_tracked} stars tracked in {SKY_DB}. "
          "Bonuses decay each pass; bonds graduate stars to gravity.")


def cmd_pin(args, remove=False):
    if not args:
        print("Usage: python skyrank.py pin <name>")
        return
    conn = sky_db()
    for name in args:
        if remove:
            conn.execute("DELETE FROM pins WHERE name=?", (name,))
            print(f"unpinned: {name}")
        else:
            conn.execute("INSERT OR IGNORE INTO pins (name) VALUES (?)",
                     (name,))
            print(f"pinned: {name}  (always visible; gravity cannot "
              "displace a pin)")
        counts = bond_counts(gravity_db_path())
        g = counts.get(os.path.basename(name), 0)
        record_echo(name, "pinned" if not remove else "unpinned", g, g)
    conn.commit()
    conn.close()


def cmd_report(_args):
    conn = sky_db()
    pins = [r[0] for r in conn.execute(
        "SELECT name FROM pins ORDER BY name").fetchall()]
    n = conn.execute("SELECT COUNT(*) FROM stars").fetchone()[0]
    new = conn.execute(
        "SELECT COUNT(*) FROM stars WHERE presentations=0").fetchone()[0]
    conn.close()
    print("SELECTION ENGINE REPORT")
    print(f"  limit:            {LIMIT}")
    print(f"  gravity share:    {GRAVITY_RATIO}  (tunable)")
    print(f"  antigravity share:{ANTIGRAVITY_RATIO}  (tunable)")
    print(f"  bonuses:          new {BONUS_NEW} / once {BONUS_SEEN_ONCE} / "
          f"multi {BONUS_SEEN_MULTI} / emerging {BONUS_EMERGING}")
    print(f"  decay:            x{DECAY} per pass after first presentation")
    print(f"  established at:   {ESTABLISHED_AT} bonds")
    print(f"  pinned ({len(pins)}):")
    for p in pins:
        print(f"    {p}")
    print(f"  tracked stars:    {n} ({new} never presented)")


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return
    cmd, args = argv[1], argv[2:]
    if cmd == "scan":
        cmd_scan(args)
    elif cmd == "pin":
        cmd_pin(args)
    elif cmd == "unpin":
        cmd_pin(args, remove=True)
    elif cmd == "report":
        cmd_report(args)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
