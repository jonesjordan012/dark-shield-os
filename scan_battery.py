"""SI-001 live test battery for the filesystem scanner.

Run from the repo root:

    python scan_battery.py

The script builds a scratch folder, scans it, then performs the four
mutations from the SI-001 test plan — rename, edit, duplicate,
ambiguous move — rescanning after each one and grading the result.

Expected doctrine behavior:
  1. Rename    -> new 0, claims 1 (inode evidence, confidence 0.95)
  2. Edit      -> new 0, claims 0 (identity survives change silently)
  3. Duplicate -> new 1 (two stars; the relationship is preserved,
                  not collapsed into one star)
  4. Ambiguous -> new 1, unresolved 1 (the scanner declines to guess
                  and records the uncertainty instead)
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from darkshield import Universe  # noqa: E402
from darkshield.scanners import CONTINUITY_THRESHOLD, scan_filesystem  # noqa: E402

RESULTS: list[tuple[str, bool]] = []


def check(label: str, ok: bool, detail: str) -> None:
    RESULTS.append((label, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {detail}")


def scan(root: Path, universe_file: Path) -> dict:
    if universe_file.exists():
        universe = scan_filesystem(root, Universe.load(str(universe_file)))
    else:
        universe = scan_filesystem(root)
    universe.save(str(universe_file))
    observations = [
        h for h in universe.history if h.get("event_type") == "observation"
    ]
    return observations[-1]


def events(universe_file: Path, kind: str) -> list[dict]:
    universe = Universe.load(str(universe_file))
    return [h for h in universe.history if h.get("event_type") == kind]


def main() -> int:
    scratch = Path(tempfile.mkdtemp(prefix="scan-battery-"))
    root = scratch / "tree"
    root.mkdir()
    universe_file = scratch / "universe.json"
    print(f"Scratch tree: {root}")
    try:
        (root / "README.md").write_text("readme", encoding="utf-8")
        (root / "notes.md").write_text("hello world", encoding="utf-8")
        (root / "a.txt").write_text("alpha", encoding="utf-8")

        print("\nBaseline scan")
        data = scan(root, universe_file)
        print(f"  observed={data['observed']} new={data['new']} "
              f"claims={data['claims']} unresolved={data['unresolved']}")
        check("baseline", data["observed"] == 3 and data["new"] == 3
              and data["claims"] == 0, "3 births, no claims possible yet")

        print("\nTest 1: Rename README.md -> README-NEW.md")
        os.rename(root / "README.md", root / "README-NEW.md")
        data = scan(root, universe_file)
        print(f"  observed={data['observed']} new={data['new']} "
              f"claims={data['claims']} unresolved={data['unresolved']}")
        claims = events(universe_file, "continuity_claim")
        check("rename", data["new"] == 0 and data["claims"] == 1,
              "no births; exactly one inference was needed")
        check("rename", bool(claims)
              and claims[-1]["confidence"] >= CONTINUITY_THRESHOLD
              and any(e.get("type") == "same_inode"
                      for e in claims[-1]["evidence"]),
              "claim carries its evidence and confidence")

        print("\nTest 2: Edit notes.md (append a line)")
        with (root / "notes.md").open("a", encoding="utf-8") as handle:
            handle.write("\na new line")
        data = scan(root, universe_file)
        print(f"  observed={data['observed']} new={data['new']} "
              f"claims={data['claims']} unresolved={data['unresolved']}")
        check("edit", data["new"] == 0 and data["claims"] == 0,
              "identity survives change; no belief was required")

        print("\nTest 3: Duplicate notes.md -> notes-copy.md")
        shutil.copy(root / "notes.md", root / "notes-copy.md")
        data = scan(root, universe_file)
        print(f"  observed={data['observed']} new={data['new']} "
              f"claims={data['claims']} unresolved={data['unresolved']}")
        check("duplicate", data["new"] == 1 and data["claims"] == 0,
              "two stars now; sameness is a relationship, not a collapse")

        print("\nTest 4: Ambiguous move (copy a.txt into sub/, delete original)")
        (root / "sub").mkdir()
        shutil.copy(root / "a.txt", root / "sub" / "a.txt")
        os.remove(root / "a.txt")
        data = scan(root, universe_file)
        print(f"  observed={data['observed']} new={data['new']} "
              f"claims={data['claims']} unresolved={data['unresolved']}")
        unresolved = events(universe_file, "identity_unresolved")
        check("ambiguous", data["new"] == 1 and data["unresolved"] == 1,
              "scanner mints a new star instead of guessing")
        check("ambiguous", bool(unresolved)
              and unresolved[-1]["confidence"] < CONTINUITY_THRESHOLD,
              "uncertainty is on the record, with its confidence")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    passed = sum(1 for _, ok in RESULTS if ok)
    print(f"\nBATTERY: {passed}/{len(RESULTS)} checks passed")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
