"""DG-0 acceptance tests: relationships are first-class, with biographies.

DG-0 (adopted as draft 2026-10-20): the existing Relationship object
is the canonical gravity representation; weight is DERIVED from
evidence (never stored as fact); every relationship possesses an
independent identity and an independent history — gravity_created,
gravity_updated, gravity_removed — where "removed" means no longer
present, never erased.
"""

from __future__ import annotations

import pytest

from darkshield import Evidence, Relationship, Star, Universe


def _universe() -> Universe:
    u = Universe(universe_id="urn:darkshield:universe:dg0")
    u.add_star(Star(id="star:a", name="a.py", path="a.py", size_bytes=10))
    u.add_star(Star(id="star:b", name="b.py", path="b.py", size_bytes=20))
    return u


def _edge(u: Universe) -> Relationship:
    return u.add_relationship(Relationship(
        id="gravity:test1",
        source="star:a",
        target="star:b",
        relation="related_to",
        evidence=[Evidence(
            source="dependency", observations=3, confidence=0.9,
            details="a imports b",
        )],
    ))


def _gravity_events(u: Universe, kind: str) -> list[dict]:
    return [h for h in u.history if h.get("event_type") == kind]


def test_dg0_a_creation_gives_independent_identity_and_event() -> None:
    u = _universe()
    edge = _edge(u)
    assert edge.id == "gravity:test1"
    assert u.get_gravity("gravity:test1") is edge
    created = _gravity_events(u, "gravity_created")
    assert created and created[0]["gravity_id"] == "gravity:test1"
    assert created[0]["relationship_type"] == "related_to"


def test_dg0_b_explain_relationship_by_id() -> None:
    u = _universe()
    _edge(u)
    explanation = u.explain_relationship("gravity:test1")
    assert explanation is not None
    assert explanation.evidence, "explainability must return evidence"
    assert explanation.supports(explanation.gravity)
    assert u.explain_relationship("gravity:missing") is None


def test_dg0_c_evidence_attachment_records_gravity_updated() -> None:
    u = _universe()
    edge = _edge(u)
    before = edge.gravity()
    u.attach_evidence("gravity:test1", Evidence(
        source="execution", observations=5, confidence=0.8,
        details="a executed b",
    ))
    updated = _gravity_events(u, "gravity_updated")
    assert updated and updated[0]["gravity_id"] == "gravity:test1"
    # The derived weight moved because the evidence grew — and the
    # event records the new derived value.
    assert edge.gravity() != before
    assert updated[0]["gravity"] == edge.gravity()


def test_dg0_d_weight_is_derived_and_bounded() -> None:
    u = _universe()
    edge = _edge(u)
    assert 0.0 <= edge.gravity() <= 1.0
    # A stored out-of-range weight is still rejected at construction.
    with pytest.raises(ValueError):
        Relationship(
            id="gravity:bad", source="star:a", target="star:b",
            relation="related_to", weight=1.5,
        )


def test_dg0_e_identities_persist_through_save_load(tmp_path=None) -> None:
    import tempfile
    from pathlib import Path

    u = _universe()
    _edge(u)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "universe.json"
        u.save(path)
        restored = Universe.load(path)
    assert restored.get_gravity("gravity:test1") is not None
    assert restored.explain_relationship("gravity:test1") is not None


def test_removed_means_absent_never_erased() -> None:
    u = _universe()
    _edge(u)
    removed = u.remove_relationship("gravity:test1")
    assert removed is not None
    assert u.get_gravity("gravity:test1") is None
    assert u.get_relationships("star:a") == []
    events = _gravity_events(u, "gravity_removed")
    assert events and events[0]["gravity_id"] == "gravity:test1"
    # The biography survives the removal: created AND removed are
    # both still on the record.
    assert _gravity_events(u, "gravity_created")


def test_get_relationships_by_entity() -> None:
    u = _universe()
    _edge(u)
    assert [r.id for r in u.get_relationships("star:a")] == ["gravity:test1"]
    assert [r.id for r in u.get_relationships("star:b")] == ["gravity:test1"]
    assert u.get_relationships("star:missing") == []
