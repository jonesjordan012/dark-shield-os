"""DG-2 acceptance tests: gravity valuation.

DG-2 (adopted as draft 2026-10-20, constitutional amendments applied):
valuation compares STRUCTURAL STRENGTH among relationships — never
significance (CQ-00Y). Group size is recorded as evidence; dg2-v1
attenuates by it; identical evidence may legitimately remain tied.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from darkshield import Evidence, Relationship, Star, Universe
from darkshield.gravity.generate import generate_root_gravity
from darkshield.gravity.models import derive_gravity
from darkshield.scanners import scan_filesystem


def _dg1_evidence(source: str, value: str, group_size: int) -> Evidence:
    return Evidence(
        source=source, observations=1, confidence=1.0,
        details={"value": value, "group_size": group_size},
    )


def _pair(u: Universe, rid: str, evidence: list[Evidence]) -> Relationship:
    return u.add_relationship(Relationship(
        id=rid, source="star:a", target="star:b",
        relation=evidence[0].source if evidence else "related_to",
        evidence=evidence,
    ))


def _universe() -> Universe:
    u = Universe(universe_id="urn:darkshield:universe:dg2")
    u.add_star(Star(id="star:a", name="a.md", path="a.md", size_bytes=1))
    u.add_star(Star(id="star:b", name="b.md", path="b.md", size_bytes=1))
    return u


def test_dg2_a_evidence_consistency() -> None:
    u = _universe()
    rel = _pair(u, "gravity:a", [_dg1_evidence("same_directory", "/docs", 4)])
    explanation = rel.explain()
    assert explanation.supports(rel.gravity())
    total = sum(explanation.contributions.values())
    assert abs(total - rel.gravity()) < 1e-9  # unclamped: fully accounted


def test_dg2_b_multi_source_dominance() -> None:
    u = _universe()
    a = _pair(u, "gravity:a", [_dg1_evidence("same_directory", "/docs", 4)])
    u2 = _universe()
    b = _pair(u2, "gravity:b", [
        _dg1_evidence("same_directory", "/docs", 4),
        _dg1_evidence("shared_name_stem", "report", 4),
        _dg1_evidence("shared_extension", ".md", 4),
    ])
    assert b.gravity() > a.gravity()


def test_dg2_c_explainable_valuation() -> None:
    u = _universe()
    rel = _pair(u, "gravity:c", [
        _dg1_evidence("same_directory", "/docs", 4),
        _dg1_evidence("shared_extension", ".md", 9),
    ])
    explanation = u.explain_relationship("gravity:c")
    assert explanation is not None
    assert set(explanation.contributions) == {"same_directory", "shared_extension"}
    assert explanation.valuation_version == "dg2-v1"
    assert all(v > 0 for v in explanation.contributions.values())


def test_dg2_d_saturation_protection() -> None:
    root = Path(tempfile.mkdtemp(prefix="ds-dg2-"))
    try:
        small = root / "small"
        big = root / "big"
        small.mkdir()
        big.mkdir()
        for i, name in enumerate(["an", "bo", "cy"]):
            (small / f"{name}.x{i:02d}").write_bytes(b"s")
        for i in range(40):
            (big / f"d{i:02d}.y{i:02d}").write_bytes(b"b")
        u = scan_filesystem(root)
        generate_root_gravity(u, root)

        def pair_gravity(directory: str) -> float:
            values = [
                r.gravity() for r in u.relationships
                if any(
                    e.source == "same_directory"
                    and isinstance(e.details, dict)
                    and directory in str(e.details.get("value", ""))
                    for e in r.evidence
                )
            ]
            assert values
            return values[0]

        small_g = pair_gravity("small")
        big_g = pair_gravity("big")
        assert small_g > big_g, "the small directory's pairs must pull stronger"
        assert all(r.gravity() <= 1.0 for r in u.relationships)
        strongest = u.strongest_relationships(1)[0]
        assert strongest.gravity() == max(r.gravity() for r in u.relationships)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dg2_e_revaluation_preserves_evidence() -> None:
    evidence = [
        _dg1_evidence("same_directory", "/docs", 4).to_dict(),
        _dg1_evidence("shared_extension", ".md", 9).to_dict(),
    ]
    snapshot = [dict(e) for e in evidence]
    old = derive_gravity(evidence, "m2b-v1")
    new = derive_gravity(evidence, "dg2-v1")
    assert old != new, "the valuation version changes the derived strength"
    assert evidence == snapshot, "revaluation never rewrites evidence"
    # An explanation recorded under the old version still verifies.
    from darkshield.gravity.models import Explanation

    historical = Explanation(
        relationship_id="gravity:x", source="star:a", target="star:b",
        relation="same_directory", evidence=evidence, gravity=old,
        formula="m2b-v1",
    )
    assert historical.supports(old)


def test_identical_evidence_may_remain_tied() -> None:
    # DG-2 shall NOT guarantee unique ordering — and shall not
    # fabricate distinctions it cannot support.
    evidence = [_dg1_evidence("same_directory", "/docs", 4)]
    u = _universe()
    a = _pair(u, "gravity:t1", list(evidence))
    u2 = _universe()
    b = _pair(u2, "gravity:t2", list(evidence))
    assert a.gravity() == b.gravity()


def test_dg2_queries() -> None:
    u = _universe()
    _pair(u, "gravity:q", [_dg1_evidence("same_directory", "/docs", 2)])
    assert u.strongest_relationships(1)[0].id == "gravity:q"
    assert u.weakest_relationships(1)[0].id == "gravity:q"
    neighbors = u.related_stars("star:a")
    assert [n.id for n in neighbors] == ["star:b"]
