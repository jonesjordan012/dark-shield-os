"""Universe query API tests: explainability (M2-C) + ranking (M2-D).

Completion criteria for M2: the system can truthfully answer — using
evidence stored in the universe itself — why a star is important, why
a pulsar is connected, and why two entities are near each other.
"""

from __future__ import annotations

from darkshield import (
    Evidence,
    Galaxy,
    ImportEvidence,
    Relationship,
    Star,
    Universe,
)


def _universe() -> Universe:
    u = Universe(universe_id="urn:darkshield:universe:test")
    u.add_galaxy(Galaxy(id="galaxy:dev", name="dark-shield-os", kind="directory"))
    u.add_star(Star(id="star:main", name="main.py", path="main.py", size_bytes=100))
    u.add_star(
        Star(id="star:validator", name="validator.py", path="validator.py", size_bytes=80)
    )
    rel = Relationship(
        id="rel:1",
        source="star:main",
        target="star:validator",
        relation="depends_on",
    )
    rel.attach_evidence(
        ImportEvidence(
            observations=12, confidence=0.75, details={"imported_name": "validator"}
        )
    )
    u.add_relationship(rel)
    u.add_relationship(
        Relationship(
            id="rel:2",
            source="galaxy:dev",
            target="star:main",
            relation="contains",
        )
    )
    return u


def test_explain_returns_verifiable_explanation() -> None:
    u = _universe()
    explanation = u.explain("star:main", "star:validator")
    assert explanation is not None
    rel = u.find_relationship("star:main", "star:validator")
    assert rel is not None
    assert explanation.supports(rel.gravity())


def test_explain_none_when_unrelated() -> None:
    u = _universe()
    assert u.explain("galaxy:dev", "star:validator") is None
    assert u.explain("star:missing", "star:main") is None


def test_explain_finds_reverse_direction() -> None:
    u = _universe()
    assert u.explain("star:validator", "star:main") is not None


def test_related_to_covers_both_directions() -> None:
    u = _universe()
    rels = u.related_to("star:main")
    assert {r.id for r in rels} == {"rel:1", "rel:2"}
    assert u.related_to("star:unknown") == []


def test_most_connected() -> None:
    u = _universe()
    ranked = u.most_connected()
    assert ranked[0] == ("star:main", 2)
    assert dict(ranked)["star:validator"] == 1


def test_top_gravity() -> None:
    u = _universe()
    ranked = u.top_gravity()
    # star:main touches the evidence-bearing relationship; it must lead.
    assert ranked[0][0] == "star:main"
    assert ranked[0][1] > 0.0


def test_most_gravitational_matches_top_gravity() -> None:
    u = _universe()
    assert u.most_gravitational() == u.top_gravity()


def test_explain_entity() -> None:
    u = _universe()
    text = u.explain_entity("star:main")
    assert text is not None
    assert "main.py" in text
    assert "gravity" in text
    assert u.explain_entity("star:unknown") is None
