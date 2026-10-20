"""Galaxy M3-A tests: state/fate axes, declared labels, derived membership.

Constitutional guards under test:
- State (reversible condition) and Fate (historical outcome) are two
  separate axes with separate vocabularies.
- REMOVED is rejected as a fate (Retention Doctrine / RAC-001).
- Labels are declared by the user only — never inferred from structure.
- Membership is derived from relationships, never stored.
"""

from __future__ import annotations

import pytest

from darkshield import (
    GALAXY_FATES,
    GALAXY_STATES,
    Galaxy,
    Relationship,
    Star,
    Universe,
)


def _universe() -> Universe:
    u = Universe(universe_id="urn:darkshield:universe:m3a")
    u.add_galaxy(Galaxy(id="galaxy:dev", name="dark-shield-os", kind="directory"))
    u.add_star(Star(id="star:a", name="a.py", path="a.py", size_bytes=10))
    u.add_star(Star(id="star:b", name="b.py", path="b.py", size_bytes=20))
    u.add_relationship(
        Relationship(
            id="rel:1", source="galaxy:dev", target="star:a", relation="contains"
        )
    )
    u.add_relationship(
        Relationship(
            id="rel:2", source="star:b", target="galaxy:dev", relation="belongs_to"
        )
    )
    return u


def test_galaxy_defaults() -> None:
    g = Galaxy(id="galaxy:x", name="x")
    assert g.state == "ACTIVE"
    assert g.fate == "UNKNOWN"
    assert g.labels == []
    assert g.evidence_refs == []
    assert g.parent_id is None
    assert GALAXY_STATES == {"ACTIVE", "DORMANT", "ARCHIVED"}


def test_galaxy_rejects_bad_state() -> None:
    with pytest.raises(ValueError):
        Galaxy(id="galaxy:x", name="x", state="SLEEPING")


def test_galaxy_rejects_removed_fate() -> None:
    """REMOVED is rejected: Concluded != Deleted, Weakened != Removed."""
    with pytest.raises(ValueError):
        Galaxy(id="galaxy:x", name="x", fate="REMOVED")
    assert "REMOVED" not in GALAXY_FATES


def test_galaxy_node_roundtrip_preserves_m3a_fields() -> None:
    g = Galaxy(
        id="galaxy:x",
        name="x",
        kind="workspace",
        state="DORMANT",
        fate="SPLIT",
        labels=["Development"],
        evidence_refs=["ev:001"],
        parent_id="galaxy:parent",
    )
    restored = Galaxy.from_node_dict(g.to_node_dict())
    assert restored == g
    assert restored.state == "DORMANT"
    assert restored.labels == ["Development"]


def test_members_are_derived_not_stored() -> None:
    u = _universe()
    galaxy = u._find_galaxy("galaxy:dev")
    assert galaxy is not None
    assert galaxy.members(u) == ["star:a", "star:b"]
    # Nothing about membership lives on the entity itself.
    assert "member_ids" not in galaxy.to_dict()


def test_labels_only_enter_by_declaration() -> None:
    """Constitutional: structure alone never produces a label."""
    u = _universe()
    # The galaxy has members, relationships, gravity — and no labels.
    assert u.labels("galaxy:dev") == []
    u.declare_label("galaxy:dev", "Development")
    assert u.labels("galaxy:dev") == ["Development"]
    # Declaring twice does not duplicate.
    u.declare_label("galaxy:dev", "Development")
    assert u.labels("galaxy:dev") == ["Development"]


def test_declare_label_unknown_galaxy() -> None:
    u = _universe()
    with pytest.raises(ValueError):
        u.declare_label("galaxy:missing", "Nope")
    assert u.labels("galaxy:missing") is None


def test_declare_label_rejects_empty() -> None:
    u = _universe()
    with pytest.raises(ValueError):
        u.declare_label("galaxy:dev", "   ")


def test_describe_is_observational() -> None:
    u = _universe()
    galaxy = u._find_galaxy("galaxy:dev")
    assert galaxy is not None
    text = galaxy.describe(u)
    assert "ACTIVE" in text
    assert "2 members (derived)" in text
    # No meaning is claimed: an undeclared galaxy shows no label line.
    assert "declared labels" not in text
    u.declare_label("galaxy:dev", "Development")
    assert "Development" in galaxy.describe(u)
