"""DG-2 certification battery: Gravity Valuation.

Run from the repo root:

    python dg2_battery.py

Executes the DG-2 acceptance battery (Section 12). DG-2 measures
structural strength only (CQ-00Y) — never significance.

  DG-2-A  Evidence Consistency
  DG-2-B  Multi-Source Dominance
  DG-2-C  Explainable Valuation
  DG-2-D  Saturation Protection
  DG-2-E  Revaluation
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from darkshield import Evidence, Relationship, Star, Universe  # noqa: E402
from darkshield.gravity.generate import generate_root_gravity  # noqa: E402
from darkshield.gravity.models import Explanation, derive_gravity  # noqa: E402
from darkshield.scanners import scan_filesystem  # noqa: E402

RESULTS: list[tuple[str, bool]] = []


def check(label: str, ok: bool, detail: str) -> None:
    RESULTS.append((label, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {detail}")


def dg1_evidence(source: str, value: str, group_size: int) -> Evidence:
    return Evidence(
        source=source, observations=1, confidence=1.0,
        details={"value": value, "group_size": group_size},
    )


def universe_with(evidence: list[Evidence]) -> tuple[Universe, Relationship]:
    u = Universe(universe_id="urn:darkshield:universe:dg2-battery")
    u.add_star(Star(id="star:a", name="a.md", path="a.md", size_bytes=1))
    u.add_star(Star(id="star:b", name="b.md", path="b.md", size_bytes=1))
    rel = u.add_relationship(Relationship(
        id="gravity:battery", source="star:a", target="star:b",
        relation=evidence[0].source, evidence=evidence,
    ))
    return u, rel


def main() -> int:
    print("\nDG-2-A: Evidence Consistency")
    _, rel = universe_with([dg1_evidence("same_directory", "/docs", 4)])
    explanation = rel.explain()
    check("A", explanation.supports(rel.gravity()),
          "gravity derives entirely from recorded evidence")
    check("A", abs(sum(explanation.contributions.values()) - rel.gravity()) < 1e-9,
          "per-source contributions account for the whole value")

    print("\nDG-2-B: Multi-Source Dominance")
    _, single = universe_with([dg1_evidence("same_directory", "/docs", 4)])
    _, multi = universe_with([
        dg1_evidence("same_directory", "/docs", 4),
        dg1_evidence("shared_name_stem", "report", 4),
        dg1_evidence("shared_extension", ".md", 4),
    ])
    check("B", multi.gravity() > single.gravity(),
          f"three sources ({multi.gravity():.3f}) pull stronger "
          f"than one ({single.gravity():.3f})")

    print("\nDG-2-C: Explainable Valuation")
    u, _ = universe_with([
        dg1_evidence("same_directory", "/docs", 4),
        dg1_evidence("shared_extension", ".md", 9),
    ])
    exp = u.explain_relationship("gravity:battery")
    check("C", exp is not None
          and set(exp.contributions) == {"same_directory", "shared_extension"},
          "explain_relationship returns all valuation contributors")
    check("C", exp is not None and exp.valuation_version == "dg2-v1",
          "the valuation version is exposed")

    print("\nDG-2-D: Saturation Protection")
    root = Path(tempfile.mkdtemp(prefix="dg2-battery-"))
    try:
        small, big = root / "small", root / "big"
        small.mkdir()
        big.mkdir()
        for i, name in enumerate(["an", "bo", "cy"]):
            (small / f"{name}.x{i:02d}").write_bytes(b"s")
        for i in range(40):
            (big / f"d{i:02d}.y{i:02d}").write_bytes(b"b")
        scanned = scan_filesystem(root)
        generate_root_gravity(scanned, root)

        def pair_gravity(directory: str) -> float:
            for r in scanned.relationships:
                for e in r.evidence:
                    if (e.source == "same_directory"
                            and isinstance(e.details, dict)
                            and directory in str(e.details.get("value", ""))):
                        return r.gravity()
            return -1.0

        small_g, big_g = pair_gravity("small"), pair_gravity("big")
        check("D", small_g > big_g > 0,
              f"small-directory pair ({small_g:.3f}) outpulls "
              f"large-clique pair ({big_g:.3f})")
        check("D", all(r.gravity() <= 1.0 for r in scanned.relationships),
              "valuation remains bounded on the frozen scale")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print("\nDG-2-E: Revaluation")
    evidence = [
        dg1_evidence("same_directory", "/docs", 4).to_dict(),
        dg1_evidence("shared_extension", ".md", 9).to_dict(),
    ]
    snapshot = [dict(e) for e in evidence]
    old = derive_gravity(evidence, "m2b-v1")
    new = derive_gravity(evidence, "dg2-v1")
    check("E", old != new and evidence == snapshot,
          "version change recomputes gravity; evidence untouched")
    historical = Explanation(
        relationship_id="gravity:battery", source="star:a", target="star:b",
        relation="same_directory", evidence=evidence, gravity=old,
        formula="m2b-v1",
    )
    check("E", historical.supports(old),
          "explanations recorded under m2b-v1 still verify under DG-2")

    passed = sum(1 for _, ok in RESULTS if ok)
    print(f"\nBATTERY: {passed}/{len(RESULTS)} checks passed")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
