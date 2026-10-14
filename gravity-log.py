#!/usr/bin/env python3
"""
DARK SHIELD 0.1 - gravity log
=============================
The first measurement of Data Gravity.

The First Law says relationships organize reality. This script measures
the simplest relationship of all: files that are used TOGETHER gain
gravity between them. Use two files together often enough, and the
universe should pull them closer.

Tonight "together" means: both touched within the last few hours.
That definition is crude on purpose - everything in the window pairs
with everything. The ranking fixes it: real pairs repeat, accidents
don't. Later, we will teach it finer definitions.

Usage:
    python gravity-log.py scan [--hours N]
        Read your Recent folder and log every pair of files
        touched in the last N hours (default: 6).

    python gravity-log.py note <file-a> <file-b>
        Manually record that two files were used together.

    python gravity-log.py report
        Show every pair ranked by gravity (times seen together).

The log lives in gravity.db, next to this script. It is SQLite -
a whole database in a single file. Your universe's first memory.
"""

import os
import sqlite3
import sys
import time

DB_NAME = "gravity.db"
MAX_FILES = 40  # even gravity has a fire code


def recent_folder():
    """Where the OS keeps 'recently used' breadcrumbs.

    On Windows, every opened file leaves a .lnk shortcut here, stamped
    with the time it was touched. Reading it is reading behavior -
    not folders, not names. Behavior.
    """
    override = os.environ.get("DARKSHIELD_RECENT")  # for testing
    if override:
        return override
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    return os.path.join(appdata, "Microsoft", "Windows", "Recent")


def db():
    here = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(os.path.join(here, DB_NAME))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS pairs ("
        " file_a TEXT NOT NULL,"
        " file_b TEXT NOT NULL,"
        " ts REAL NOT NULL)"
    )
    return conn


def log_pair(conn, a, b):
    """One unit of gravity between two files.

    Pairs are stored in alphabetical order, so (A, B) and (B, A)
    count as the same bond. Gravity has no direction.
    """
    if a == b:
        return  # a file has no gravity with itself
    a, b = sorted([a, b])
    conn.execute(
        "INSERT INTO pairs (file_a, file_b, ts) VALUES (?, ?, ?)",
        (a, b, time.time()),
    )


def scan(hours=6):
    folder = recent_folder()
    if not folder or not os.path.isdir(folder):
        print("Could not find the Recent folder.")
        print(r"On Windows it lives at %APPDATA%\Microsoft\Windows\Recent")
        return
    cutoff = time.time() - hours * 3600
    found = []
    for entry in os.listdir(folder):
        if not entry.lower().endswith(".lnk"):
            continue
        path = os.path.join(folder, entry)
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            continue  # a breadcrumb we cannot read still counts as dark matter
        if mtime >= cutoff:
            # Shortcuts are usually named after their target:
            # "report.docx.lnk" -> "report.docx"
            found.append((mtime, entry[:-4]))
    # Most recent first; cap the working set so the pair count stays sane.
    found.sort(reverse=True)
    names = sorted(set(name for _, name in found[:MAX_FILES]))
    if len(names) < 2:
        print("Not enough recently-used files to form a pair.")
        print("Open a couple of files, then scan again.")
        return
    conn = db()
    n = 0
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            log_pair(conn, names[i], names[j])
            n += 1
    conn.commit()
    conn.close()
    print(f"Logged {n} pairs from {len(names)} files used in the last {hours}h.")
    print("Gravity remembers.")


def note(a, b):
    conn = db()
    log_pair(conn, a, b)
    conn.commit()
    conn.close()
    print(f"Logged: {a} <-> {b}")


def report():
    conn = db()
    rows = conn.execute(
        "SELECT file_a, file_b, COUNT(*) AS g FROM pairs "
        "GROUP BY file_a, file_b ORDER BY g DESC, file_a, file_b"
    ).fetchall()
    conn.close()
    if not rows:
        print("No gravity recorded yet. Run: python gravity-log.py scan")
        return
    print("DATA GRAVITY - strongest bonds first\n")
    for a, b, g in rows[:30]:
        bar = "#" * min(g, 40)
        print(f"{g:>4}  {bar}  {a} <-> {b}")
    print(f"\n{len(rows)} bonds recorded. The universe is learning.")


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return
    cmd = argv[1]
    if cmd == "scan":
        hours = 6
        if "--hours" in argv:
            try:
                hours = float(argv[argv.index("--hours") + 1])
            except (ValueError, IndexError):
                print("Usage: python gravity-log.py scan [--hours N]")
                return
        scan(hours)
    elif cmd == "note":
        if len(argv) < 4:
            print("Usage: python gravity-log.py note <file-a> <file-b>")
            return
        note(argv[2], argv[3])
    elif cmd == "report":
        report()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
