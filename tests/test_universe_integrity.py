"""Universe integrity tests: does the universe make sense?

Layer 2 of universe testing. (Layer 1 — schema conformance — lives in
test_universe_schema.py.) This is where most bugs will occur.

Checks are numbered UC-1..UC-13 (Universe Checks). The UC prefix avoids
collision with the Reduction Test framework's IC-1..IC-5
(Inconclusive Criteria).
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FIXTURE_PATH = HERE / "fixtures" / "universe.json"


def load_universe() -> dict:
    with open(FIXTURE_PATH) as f:
        return json.load(f)


# UC-1: IDs must be unique
def test_unique_node_ids() -> None:
    universe = load_universe()
    ids = [n["id"] for n in universe["nodes"]]
    assert len(ids) == len(set(ids))


# UC-2: Relationship IDs unique
def test_unique_relationship_ids() -> None:
    universe = load_universe()
    ids = [r["id"] for r in universe["relationships"]]
    assert len(ids) == len(set(ids))


# UC-3: Relationship endpoints exist
# Probably the single most important validator.
def test_relationship_targets_exist() -> None:
    universe = load_universe()
    node_ids = {n["id"] for n in universe["nodes"]}
    for rel in universe["relationships"]:
        assert rel["source"] in node_ids
        assert rel["target"] in node_ids


# UC-4: No self-loops (optional)
def test_no_self_relationships() -> None:
    universe = load_universe()
    for rel in universe["relationships"]:
        assert rel["source"] != rel["target"]


# UC-5: Relationship weights valid
def test_relationship_weights() -> None:
    universe = load_universe()
    for rel in universe["relationships"]:
        if "weight" not in rel:
            continue
        weight = rel["weight"]
        assert 0.0 <= weight <= 1.0


# UC-6: At least one galaxy
def test_at_least_one_galaxy() -> None:
    universe = load_universe()
    galaxies = [n for n in universe["nodes"] if n["type"] == "galaxy"]
    assert len(galaxies) > 0


# UC-7: Known node types only
VALID_TYPES = {
    "star",
    "pulsar",
    "neutron_star",
    "galaxy",
    "temporal_echo",
}


def test_known_node_types() -> None:
    universe = load_universe()
    for node in universe["nodes"]:
        assert node["type"] in VALID_TYPES


# UC-8: History timestamps present
def test_history_timestamps() -> None:
    universe = load_universe()
    for event in universe["history"]:
        assert event["timestamp"]


# UC-9: History entity references valid
def test_history_entities_exist() -> None:
    universe = load_universe()
    node_ids = {n["id"] for n in universe["nodes"]}
    for event in universe["history"]:
        assert event["entity_id"] in node_ids


# UC-10: Split events sum to 1.0
def test_split_inheritance_balances() -> None:
    universe = load_universe()
    for event in universe["history"]:
        if event["event"] != "split":
            continue
        data = event["data"]
        total = data["primary_share"] + data["secondary_share"]
        assert math.isclose(total, 1.0, abs_tol=0.01)


# UC-11: Fate confidence valid
def test_fate_confidence_range() -> None:
    universe = load_universe()
    for node in universe["nodes"]:
        fate = node.get("properties", {}).get("fate")
        if not fate:
            continue
        confidence = fate.get("confidence")
        if confidence is not None:
            assert 0 <= confidence <= 1


# UC-12: Snapshot newer than creation (Persistent Boot)
def test_snapshot_after_creation() -> None:
    universe = load_universe()
    if "created_at" not in universe or "snapshot_at" not in universe:
        return
    created = datetime.fromisoformat(
        universe["created_at"].replace("Z", "+00:00")
    )
    snapshot = datetime.fromisoformat(
        universe["snapshot_at"].replace("Z", "+00:00")
    )
    assert snapshot >= created


# UC-13: Universe reconstructible as a graph
# The most important architecture test.
def test_graph_reconstruction() -> None:
    nx = pytest.importorskip("networkx")
    universe = load_universe()

    graph = nx.MultiDiGraph()
    for node in universe["nodes"]:
        graph.add_node(node["id"])
    for rel in universe["relationships"]:
        graph.add_edge(rel["source"], rel["target"])

    assert graph.number_of_nodes() == len(universe["nodes"])
    assert graph.number_of_edges() == len(universe["relationships"])


# UC-14: Canonical and derived are mutually exclusive
def test_canonical_not_derived() -> None:
    universe = load_universe()
    for node in universe["nodes"]:
        assert not (node.get("canonical") and node.get("derived"))


# UC-15: Entity ID prefixes are known
def test_id_prefixes() -> None:
    universe = load_universe()
    prefixes = {"star", "galaxy", "pulsar", "core", "echo"}
    for node in universe["nodes"]:
        prefix = node["id"].split(":")[0]
        assert prefix in prefixes


# UC-16: Temporal Echoes must be derived (Entry 002)
def test_echoes_are_derived() -> None:
    universe = load_universe()
    for node in universe["nodes"]:
        if node["type"] == "temporal_echo":
            assert node["derived"] is True
            assert node.get("canonical") is not True


# UC-17: Canonical nodes exist (the universe is not all cache)
def test_canonical_nodes_exist() -> None:
    universe = load_universe()
    canonical = [n for n in universe["nodes"] if n.get("canonical")]
    assert canonical
