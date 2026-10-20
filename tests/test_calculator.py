"""Gravity calculator tests (M2-B).

Formula m2b-v1: per-source base weights, strongest evidence wins per
source, total clamped to [0.0, 1.0].
"""

from __future__ import annotations

import pytest

from darkshield import (
    FORMULA_M2A_V1,
    FORMULA_M2B_V1,
    Evidence,
    Explanation,
    GravityCalculator,
    Relationship,
    calculate_gravity,
    derive_gravity,
)
from darkshield.gravity.validators import validate_gravity


def _rel() -> Relationship:
    return Relationship(
        id="rel:1", source="star:a", target="star:b", relation="depends_on"
    )


def test_full_strength_source_gives_base_weight() -> None:
    """A source at full strength contributes exactly its base weight."""
    calc = GravityCalculator()
    got = calc.contributions(
        [Evidence(source="dependency", observations=50, confidence=1.0).to_dict()]
    )
    assert got == {"dependency": pytest.approx(0.40)}


def test_strongest_evidence_wins_per_source() -> None:
    """Two dependency evidences: the source contributes once (max)."""
    calc = GravityCalculator()
    got = calc.contributions(
        [
            Evidence(source="dependency", observations=50, confidence=1.0).to_dict(),
            Evidence(source="dependency", observations=10, confidence=0.5).to_dict(),
        ]
    )
    assert got["dependency"] == pytest.approx(0.40)


def test_total_clamped_to_one() -> None:
    """All five sources at full strength: clamped, never above 1.0."""
    calc = GravityCalculator()
    evidence = [
        Evidence(source=s, observations=50, confidence=1.0).to_dict()
        for s in ("containment", "dependency", "execution", "temporal", "attention")
    ]
    assert calc.calculate(evidence) == 1.0


def test_unknown_source_gets_small_default() -> None:
    """Unrecognized provenance is weak evidence, not no evidence."""
    calc = GravityCalculator()
    got = calc.calculate(
        [Evidence(source="migrated", observations=50, confidence=1.0).to_dict()]
    )
    assert got == pytest.approx(0.10)


def test_filesystem_aliases_to_containment() -> None:
    calc = GravityCalculator()
    assert "containment" in calc.contributions(
        [Evidence(source="filesystem", observations=3, confidence=0.9).to_dict()]
    )


def test_explanation_records_current_formula() -> None:
    rel = _rel().attach_evidence(
        Evidence(source="temporal", observations=18, confidence=0.82)
    )
    explanation = rel.explain()
    assert explanation.formula == FORMULA_M2B_V1
    assert explanation.supports(rel.gravity())


def test_old_formula_explanations_still_verify() -> None:
    """Explanations recorded under m2a-v1 verify after the formula changed."""
    snapshots = [
        Evidence(source="temporal", observations=18, confidence=0.82).to_dict()
    ]
    old_gravity = derive_gravity(snapshots, FORMULA_M2A_V1)
    explanation = Explanation(
        relationship_id="rel:old",
        source="star:a",
        target="star:b",
        relation="related_to",
        evidence=snapshots,
        gravity=old_gravity,
        confidence=0.82,
        formula=FORMULA_M2A_V1,
    )
    assert explanation.supports(old_gravity)
    # And the new formula gives a (possibly) different, still valid value.
    new_gravity = derive_gravity(snapshots, FORMULA_M2B_V1)
    assert 0.0 <= new_gravity <= 1.0


def test_relationship_gravity_matches_calculator() -> None:
    rel = _rel().attach_evidence(
        Evidence(source="dependency", observations=25, confidence=0.8)
    )
    snapshots = [e.to_dict() for e in rel.evidence]
    assert rel.gravity() == calculate_gravity(snapshots)


def test_validators_reject_bad_gravity() -> None:
    with pytest.raises(ValueError):
        validate_gravity(1.5)
    with pytest.raises(ValueError):
        validate_gravity(float("nan"))
    with pytest.raises(TypeError):
        validate_gravity("high")
    assert validate_gravity(0.85) == 0.85
