"""DG-1 certification battery: Root-Scoped Gravity.

Run from the repo root:

    python dg1_battery.py

Executes the DG-1 acceptance battery (Section 10) against real
temporary directory trees, scanning first and generating gravity as
the separate, explicit phase Section 11 requires.

  DG-1-A  Same Directory
  DG-1-B  Source Explainability
  DG-1-C  Source Disablement
  DG-1-D  Root Boundary
  DG-1-E  Lifecycle Preservation
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from darkshield import Star, Universe  # noqa: E402
from darkshield.gravity.generate import generate_root_gravity  # noqa: E402
from darkshield.scanners import scan_filesystem  # noqa: E402

RESULTS: list[tuple[str, bool]] = []


def check(label: str, ok: bool, detail: str) -> None:
    RESULTS.append((label, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {detail}")


def tree(files: dict[str, bytes]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="dg1-battery-"))
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return root


def pair_edges(u: Universe) -> list:
    stars = {n.id for n in u.nodes if isinstance(n, Star)}
    return [
        r for r in u.relationships
        if r.source in stars and r.target in stars and r.relation != "contains"
    ]


def main() -> int:
    root = tree({"a.txt": b"a", "b.txt": b"b", "c.md": b"c"})
    other_root = tree({"x.txt": b"x", "y.txt": b"y"})
    try:
        u = scan_filesystem(root)
        u = scan_filesystem(other_root, u)

        print("\nDG-1-A: Same Directory")
        stats = generate_root_gravity(u, root)
        edges = pair_edges(u)
        check("A", stats["created"] == 3 and len(edges) == 3,
              "three stars in one directory produced the full clique")
        check("A", all(
            any(e.source == "same_directory" for e in r.evidence)
            for r in edges
        ), "every generated relationship carries same_directory evidence")

        print("\nDG-1-B: Source Explainability")
        explanation = u.explain_relationship(edges[0].id)
        check("B", explanation is not None and bool(explanation.evidence),
              "explain_relationship returns the contributing evidence")
        check("B", explanation is not None
              and "same_directory" in explanation.sources,
              "the explanation names its gravity sources")

        print("\nDG-1-C: Source Disablement")
        generate_root_gravity(u, root, sources=["shared_extension"])
        remaining = pair_edges(u)
        check("C", not [
            e for r in remaining for e in r.evidence
            if e.source == "same_directory"
        ], "with same_directory disabled, its evidence ceases")
        check("C", len(remaining) == 1,
              "the pair held by shared_extension continues; others removed")

        print("\nDG-1-D: Root Boundary")
        other_ids = {
            n.id for n in u.nodes
            if isinstance(n, Star) and n.path.startswith(str(other_root))
        }
        check("D", not [
            r for r in pair_edges(u)
            if r.source in other_ids or r.target in other_ids
        ], "no gravity generated from files outside the scan root")

        print("\nDG-1-E: Lifecycle Preservation")
        generate_root_gravity(u, root)  # restore all sources
        edge = pair_edges(u)[0]
        edge_id = edge.id
        victim = next(
            n for n in u.nodes
            if isinstance(n, Star) and n.id in (edge.source, edge.target)
        )
        os.remove(victim.path)
        u = scan_filesystem(root, u)
        generate_root_gravity(u, root)
        kinds = [h.get("event_type") for h in u.history]
        check("E", u.get_gravity(edge_id) is None,
              "the relationship ceased when its evidence disappeared")
        check("E", "gravity_created" in kinds and "gravity_removed" in kinds,
              "created and removed both remain in history")
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(other_root, ignore_errors=True)

    passed = sum(1 for _, ok in RESULTS if ok)
    print(f"\nBATTERY: {passed}/{len(RESULTS)} checks passed")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
