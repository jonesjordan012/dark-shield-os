"""Inspect the strongest gravity in a saved universe.

Run from the repo root:

    python inspect_gravity.py            # top 20 relationships
    python inspect_gravity.py 5          # top 5
    python inspect_gravity.py 10 other.json

An observational exercise, not a test (DG-1): for each of the
strongest relationships, print its full explanation — the evidence
that created it and the gravity derived from that evidence. The
question to hold while reading: can every relationship explain
itself? (CQ-00Y: gravity describes structure, not significance —
an unfashionable ranking with honest evidence is a PASS.)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from darkshield import Universe  # noqa: E402


def main() -> int:
    top_n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    filename = sys.argv[2] if len(sys.argv) > 2 else "observed-universe.json"
    path = Path(filename)
    if not path.exists():
        print(f"{filename} not found in this directory.")
        print("Run the scan + generate step first, from the repo root.")
        return 1

    u = Universe.load(path)
    stars = [n for n in u.nodes if n.id.startswith("star:")]
    pairs = [
        r for r in u.relationships
        if r.source.startswith("star:") and r.target.startswith("star:")
    ]
    possible = len(stars) * (len(stars) - 1) // 2
    density = (len(pairs) / possible * 100) if possible else 0.0
    print(f"Universe: {len(stars)} stars, {len(pairs)} star-star "
          f"relationships ({density:.1f}% of {possible} possible pairs)")
    print(f"History:  {len(u.history)} events")

    ranked = sorted(pairs, key=lambda r: r.gravity(), reverse=True)
    names = {n.id: n.name for n in u.nodes}
    print(f"\nTop {min(top_n, len(ranked))} relationships by derived gravity:\n")
    for rel in ranked[:top_n]:
        explanation = rel.explain()
        print(f"{names.get(rel.source, rel.source)} "
              f"--[{rel.relation}]--> {names.get(rel.target, rel.target)}")
        print(f"gravity {explanation.gravity:.2f} "
              f"(confidence {explanation.confidence:.2f})")
        for line in explanation.describe().splitlines()[2:]:
            print(line)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
