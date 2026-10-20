"""Evidence tests: M2-A relationship evidence layer.

Every relationship must be explainable. Evidence carries measured
observations (source, count, confidence, details) with constructor
guards, JSON-safe round-trips, and a human-readable description.
"""

from __future__ import annotations

import json

import pytest

from darkshield import Evidence, ImportEvidence, Relationship


def test_evidence_creation() -> None:
    ev = Evidence(source="filesystem", observations=35, confidence=0.93)
    assert ev.source == "filesystem"
    assert ev.observations == 35
    assert ev.confidence == 0.93
    assert ev.details == {}


def test_evidence_rejects_negative_observations() -> None:
    with pytest.raises(ValueError):
        Evidence(source="filesystem", observations=-1)


def test_evidence_rejects_bad_confidence() -> None:
    with pytest.raises(ValueError):
        Evidence(source="filesystem", confidence=1.5)
    with pytest.raises(ValueError):
        Evidence(source="filesystem", confidence=-0.1)


def test_evidence_dict_roundtrip() -> None:
    ev = Evidence(
        source="temporal",
        observations=18,
        confidence=0.82,
        details={"reason": "opened_together"},
    )
    assert Evidence.from_dict(ev.to_dict()) == ev


def test_evidence_json_roundtrip() -> None:
    ev = Evidence(source="dependency", observations=12, confidence=0.75)
    assert Evidence.from_dict(json.loads(json.dumps(ev.to_dict()))) == ev


def test_evidence_describe() -> None:
    ev = Evidence(
        source="temporal",
        observations=18,
        confidence=0.82,
        details={"reason": "opened_together"},
    )
    text = ev.describe()
    assert "opened together" in text
    assert "18" in text


def test_relationship_attach_evidence() -> None:
    rel = Relationship(
        id="rel:1", source="star:a", target="star:b", relation="related_to"
    )
    assert rel.evidence == []
    assert rel.primary_evidence() is None
    rel.attach_evidence(
        Evidence(
            source="temporal",
            observations=18,
            confidence=0.82,
            details={"reason": "opened_together"},
        )
    ).attach_evidence(
        ImportEvidence(
            observations=12,
            confidence=0.75,
            details={"imported_name": "validator"},
        )
    )
    assert len(rel.evidence) == 2
    assert rel.primary_evidence() is not None
    assert rel.primary_evidence().source == "temporal"
    assert isinstance(rel.evidence[1], ImportEvidence)
    # Serialized as a list of evidence objects: schema-compatible, JSON-safe
    blob = rel.to_rel_dict()
    assert json.dumps(blob["evidence"])
    assert blob["evidence"][0]["observations"] == 18
    assert blob["evidence"][1]["kind"] == "ImportEvidence"
