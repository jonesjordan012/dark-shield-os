"""DG-0 certification battery: Data Gravity Foundations.

Run from the repo root:

    python dg0_battery.py

Executes the DG-0 acceptance battery (Section 12) against the
existing Relationship object, per the adoption ruling: one object,
weight derived from evidence, relationships have biographies.

  DG-0-A  Relationship Creation
  DG-0-B  Relationship Explainability
  DG-0-C  Independent History
  DG-0-D  Weight Validation
  DG-0-E  Relationship Persistence
  DG-0-F  Removal semantics (removed = absent, never erased)
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from darkshield import Evidence, Relationship, Star, Universe  # noqa: E402

RESULTS: list[tuple[str, bool]] = []


def check(label: str, ok: bool, detail: str) -> None:
    RESULTS.append((label, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {detail}")


def gravity_events(u: Universe, kind: str) -> list[dict]:
    return [h for h in u.history if h.get("event_type") == kind]


def main() -> int:
    u = Universe(universe_id="urn:darkshield:universe:dg0-battery")
    u.add_star(Star(id="star:a", name="a.py", path="a.py", size_bytes=10))
    u.add_star(Star(id="star:b", name="b.py", path="b.py", size_bytes=20))
    edge = u.add_relationship(Relationship(
        id="gravity:battery1",
        source="star:a",
        target="star:b",
        relation="related_to",
        evidence=[Evidence(
            source="dependency", observations=3, confidence=0.9,
            details="a imports b",
        )],
    ))

    print("\nDG-0-A: Relationship Creation")
    check("A", u.get_gravity("gravity:battery1") is edge,
          "relationship possesses an independent identity")
    check("A", bool(gravity_events(u, "gravity_created")),
          "creation is recorded as gravity_created")

    print("\nDG-0-B: Relationship Explainability")
    explanation = u.explain_relationship("gravity:battery1")
    check("B", explanation is not None and bool(explanation.evidence),
          "explain_relationship returns the supporting evidence")
    check("B", explanation is not None
          and explanation.supports(explanation.gravity),
          "the explanation re-derives the weight from evidence alone")

    print("\nDG-0-C: Independent History")
    u.attach_evidence("gravity:battery1", Evidence(
        source="execution", observations=5, confidence=0.8,
        details="a executed b",
    ))
    check("C", bool(gravity_events(u, "gravity_updated")),
          "evidence attachment recorded as gravity_updated")

    print("\nDG-0-D: Weight Validation")
    check("D", 0.0 <= edge.gravity() <= 1.0,
          f"derived weight within the frozen scale ({edge.gravity():.2f})")
    try:
        Relationship(
            id="gravity:bad", source="star:a", target="star:b",
            relation="related_to", weight=1.5,
        )
        rejected = False
    except ValueError:
        rejected = True
    check("D", rejected, "out-of-range stored weight rejected at construction")

    print("\nDG-0-E: Relationship Persistence")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "universe.json"
        u.save(path)
        restored = Universe.load(path)
    check("E", restored.get_gravity("gravity:battery1") is not None,
          "gravity identity persists through save/restore")
    check("E", restored.explain_relationship("gravity:battery1") is not None,
          "restored relationship remains explainable")

    print("\nDG-0-F: Removal Semantics")
    u.remove_relationship("gravity:battery1")
    check("F", u.get_gravity("gravity:battery1") is None,
          "removed relationship is no longer present")
    check("F", bool(gravity_events(u, "gravity_removed"))
          and bool(gravity_events(u, "gravity_created")),
          "biography survives: created and removed both on the record")

    passed = sum(1 for _, ok in RESULTS if ok)
    print(f"\nBATTERY: {passed}/{len(RESULTS)} checks passed")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
