"""Regression: Galaxy.kind must survive the node round-trip.

Every legal M1 kind (directory/application/workspace) must reload as itself.
Before the fix, application/workspace silently flattened to "directory",
which would have broken the M1 "reload must be identical" exit test.
"""

import pytest

from darkshield.entities import Entity, Galaxy


@pytest.mark.parametrize("kind", ["directory", "application", "workspace"])
def test_galaxy_kind_roundtrip_all_m1_kinds(kind: str) -> None:
    galaxy = Galaxy(id=f"galaxy:{kind}", name=kind.title(), kind=kind, continuity=0.5)
    clone = Entity.from_node_dict(galaxy.to_node_dict())
    assert clone == galaxy
    assert clone.kind == kind


def test_galaxy_kind_visible_in_serialized_properties() -> None:
    galaxy = Galaxy(id="galaxy:app", name="App", kind="application")
    blob = galaxy.to_node_dict()
    assert blob["properties"]["kind"] == "application"
    assert Entity.from_node_dict(blob).to_node_dict() == blob
