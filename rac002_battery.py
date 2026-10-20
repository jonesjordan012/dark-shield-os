"""RAC-002 certification battery for the filesystem scanner (v0.2).

Run from the repo root:

    python rac002_battery.py

Executes the RAC-002 acceptance battery against a scratch tree,
loading the universe from disk between scans so all reasoning must
survive in recorded history alone (R2.4):

  RAC-002-A  Rename Explainability
  RAC-002-B  Modification Explainability
  RAC-002-C  Birth Explainability
  RAC-002-D  Departure Explainability
  RAC-002-E  Uncertainty Explainability
  RAC-002-F  Rediscovery (Finding 2 of the adoption ruling)
  SCHEMA     Section 7 envelope sweep over every emitted event
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
ENVELOPE = {
    "event_id", "event_type", "timestamp",
    "schema_version", "scanner_version", "observation_id",
}


def check(label: str, ok: bool, detail: str) -> None:
    RESULTS.append((label, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {detail}")


def scan(root: Path, universe_file: Path, *, hashed: bool = False) -> Universe:
    if universe_file.exists():
        universe = scan_filesystem(
            root, Universe.load(str(universe_file)), hash_files=hashed
        )
    else:
        universe = scan_filesystem(root, hash_files=hashed)
    universe.save(str(universe_file))
    return universe


def events(universe: Universe, kind: str) -> list[dict]:
    return [h for h in universe.history if h.get("event_type") == kind]


def last_scan(universe: Universe) -> dict:
    return events(universe, "observation")[-1]


def main() -> int:
    scratch = Path(tempfile.mkdtemp(prefix="rac002-battery-"))
    root = scratch / "tree"
    root.mkdir()
    universe_file = scratch / "universe.json"
    print(f"Scratch tree: {root}")
    try:
        (root / "README.md").write_text("readme", encoding="utf-8")
        (root / "notes.md").write_text("hello world", encoding="utf-8")
        (root / "a.txt").write_text("alpha", encoding="utf-8")
        (root / "gone.txt").write_text("temporary", encoding="utf-8")

        # --- RAC-002-C: Birth Explainability -------------------------
        print("\nRAC-002-C: Birth Explainability")
        u = scan(root, universe_file)
        births = events(u, "star_birth")
        check("C", last_scan(u)["new"] == 4 and len(births) == 4,
              "every birth produced a star_birth event")
        check("C", all("confidence" not in b for b in births),
              "birth events carry no confidence (observation, not inference)")
        check("C", all(b.get("star_id") for b in births),
              "births reference stars by identity, never by path alone")

        # --- RAC-002-A: Rename Explainability ------------------------
        print("\nRAC-002-A: Rename Explainability")
        os.rename(root / "README.md", root / "README-NEW.md")
        u = scan(root, universe_file)
        claims = events(u, "continuity_claim")
        check("A", last_scan(u)["claims"] == 1 and len(claims) == 1,
              "exactly one continuity claim for the rename")
        claim = claims[0]
        check("A", 0.0 <= claim["confidence"] <= 1.0
              and claim["confidence"] >= CONTINUITY_THRESHOLD,
              f"claim confidence recorded ({claim['confidence']})")
        check("A", bool(claim["evidence"])
              and all(isinstance(e, dict) and "type" in e
                      for e in claim["evidence"]),
              "claim evidence is structured data, not free text")

        # --- RAC-002-B: Modification Explainability ------------------
        print("\nRAC-002-B: Modification Explainability")
        star_ids_before = {n.id for n in u.nodes if n.CLASS_TYPE == "star"}
        with (root / "notes.md").open("a", encoding="utf-8") as handle:
            handle.write("\na new line")
        u = scan(root, universe_file)
        modified = events(u, "star_modified")
        star_ids_after = {n.id for n in u.nodes if n.CLASS_TYPE == "star"}
        check("B", star_ids_before == star_ids_after,
              "identity persists through modification")
        check("B", bool(modified)
              and "size_changed" in modified[-1]["changes"],
              "the modification observation is recorded in history")

        # --- RAC-002-D: Departure Explainability ---------------------
        print("\nRAC-002-D: Departure Explainability")
        gone_id = next(
            b["star_id"] for b in births
            if b["path"].endswith("gone.txt")
        )
        os.remove(root / "gone.txt")
        u = scan(root, universe_file)
        departures = events(u, "star_departure")
        check("D", last_scan(u)["departed"] == 1
              and departures[-1]["star_id"] == gone_id
              and "last_observed_at" in departures[-1],
              "departure recorded with last_observed_at")
        check("D", any(n.id == gone_id for n in u.nodes),
              "departed star is retained, never deleted")

        # --- RAC-002-F: Rediscovery ----------------------------------
        print("\nRAC-002-F: Rediscovery (adoption Finding 2)")
        (root / "gone.txt").write_text("temporary", encoding="utf-8")
        u = scan(root, universe_file)
        rediscoveries = events(u, "star_rediscovery")
        check("F", bool(rediscoveries)
              and rediscoveries[-1]["star_id"] == gone_id,
              "the return is a star_rediscovery, not silent continuity")

        # --- RAC-002-E: Uncertainty Explainability -------------------
        print("\nRAC-002-E: Uncertainty Explainability")
        (root / "sub").mkdir()
        shutil.copy(root / "a.txt", root / "sub" / "a.txt")
        os.remove(root / "a.txt")
        u = scan(root, universe_file)
        unresolved = events(u, "identity_unresolved")
        check("E", last_scan(u)["unresolved"] >= 1 and bool(unresolved),
              "ambiguous continuity produced an identity_unresolved event")
        latest = unresolved[-1]
        check("E", bool(latest["candidate_star_ids"])
              and latest["confidence"] < CONTINUITY_THRESHOLD
              and bool(latest["evidence"]),
              "unresolved event carries candidates, confidence, evidence")

        # --- SCHEMA: Section 7 envelope sweep -------------------------
        print("\nSCHEMA: Section 7 envelope sweep")
        bad = [h for h in u.history if not ENVELOPE <= set(h)]
        check("SCHEMA", not bad,
              f"all {len(u.history)} history events carry the envelope")
        ids = [h["event_id"] for h in u.history]
        check("SCHEMA", len(ids) == len(set(ids)),
              "event identifiers are globally unique")
        check("SCHEMA", all(
            h["observation_id"] for h in u.history
        ), "every event references its observation (lineage, 7.8)")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    passed = sum(1 for _, ok in RESULTS if ok)
    print(f"\nBATTERY: {passed}/{len(RESULTS)} checks passed")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
