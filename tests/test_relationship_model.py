"""Relationship model tests: evidence authoritative, gravity derived.

The headline contract (Citizen ruling 2026-10-19): gravity is derived
from evidence, and the explanation must reconstruct it — so the formula
can change without breaking the architecture.
"""

from __future__ import annotations

import json

import pytest

from darkshield import (
    Evidence,
    ExecutionEvidence,
    Explanation,
    ImportEvidence,
    Relationship,
)


def _rel() -> Relationship:
    return Relationship(
        id="rel:1", source="star:a", target="star:b", relation="depends_on"
    )


def test_no_evidence_no_gravity() -> None:
    """DG-6: a relationship with no evidence has 0 gravity."""
    rel = _rel()
    assert rel.gravity() == 0.0
    assert rel.confidence == 0.0


def test_dependency_increases_gravity() -> None:
    """DG-1: attaching dependency evidence increases gravity."""
    rel = _rel()
    before = rel.gravity()
    rel.attach_evidence(ImportEvidence(observations=12, confidence=0.75))
    assert rel.gravity() > before


def test_more_observations_more_gravity() -> None:
    """DG-2: more observations increase gravity."""
    low = _rel().attach_evidence(
        Evidence(source="temporal", observations=5, confidence=1.0)
    )
    high = _rel().attach_evidence(
        Evidence(source="temporal", observations=40, confidence=1.0)
    )
    assert high.gravity() > low.gravity() > 0.0


def test_gravity_stays_in_range() -> None:
    """DG-3: gravity remains within 0.0–1.0 even for extreme evidence."""
    rel = _rel()
    for _ in range(10):
        rel.attach_evidence(
            Evidence(source="temporal", observations=100000, confidence=1.0)
        )
    assert 0.0 <= rel.gravity() <= 1.0


def test_equal_evidence_equal_gravity() -> None:
    """DG-5: equal evidence produces equal gravity."""
    kwargs = dict(source="temporal", observations=18, confidence=0.82)
    a = _rel().attach_evidence(Evidence(**kwargs))
    b = _rel().attach_evidence(Evidence(**kwargs))
    assert a.gravity() == b.gravity()


def test_explanation_supports_gravity() -> None:
    """Headline contract: the explanation reconstructs the gravity."""
    rel = _rel().attach_evidence(
        ImportEvidence(
            observations=12,
            confidence=0.75,
            details={"imported_name": "validator"},
        )
    ).attach_evidence(
        ExecutionEvidence(
            observations=7, confidence=0.6, details={"executable": "pytest"}
        )
    )
    explanation = rel.explain()
    assert isinstance(explanation, Explanation)
    assert explanation.supports(rel.gravity())
    # ...and rejects a wrong number.
    assert not explanation.supports(rel.gravity() + 0.5)


def test_explanation_reconstructs_evidence() -> None:
    """DG-4: the explanation carries the evidence it was derived from."""
    rel = _rel().attach_evidence(
        Evidence(
            source="temporal",
            observations=18,
            confidence=0.82,
            details={"reason": "opened_together"},
        )
    )
    explanation = rel.explain()
    assert len(explanation.evidence) == 1
    assert explanation.evidence[0]["observations"] == 18
    assert "opened together" in explanation.describe()


def test_confidence_aggregates_evidence() -> None:
    """Aggregate confidence rises with each supporting evidence."""
    rel = _rel()
    c0 = rel.confidence
    rel.attach_evidence(Evidence(source="temporal", observations=5, confidence=0.5))
    c1 = rel.confidence
    rel.attach_evidence(Evidence(source="temporal", observations=5, confidence=0.5))
    c2 = rel.confidence
    assert c0 == 0.0 < c1 < c2 <= 1.0


def test_evidence_subtype_roundtrip() -> None:
    """ImportEvidence keeps its kind through serialization."""
    rel = _rel().attach_evidence(ImportEvidence(observations=3, confidence=0.9))
    blob = json.loads(json.dumps(rel.to_dict()))
    rel2 = Relationship.from_dict(blob)
    assert isinstance(rel2.evidence[0], ImportEvidence)
    assert rel2.evidence[0].source == "dependency"
    assert rel2.gravity() == rel.gravity()


def test_evidence_list_validates_against_schema() -> None:
    """Serialized evidence lists validate against the evolved schema."""
    pytest.importorskip("jsonschema")
    import jsonschema
    from pathlib import Path

    schema = json.loads(
        (
            Path(__file__).parent.parent
            / "schemas"
            / "universe.schema.json"
        ).read_text()
    )
    rel = _rel().attach_evidence(
        Evidence(source="temporal", observations=18, confidence=0.82)
    )
    blob = rel.to_rel_dict()
    # Validate just the evidence fragment against the schema's evidence def.
    fragment_schema = {
        "$ref": "#/definitions/relationship/properties/evidence",
        "definitions": schema["definitions"],
    }
    jsonschema.validate(instance=blob["evidence"], schema=fragment_schema)
