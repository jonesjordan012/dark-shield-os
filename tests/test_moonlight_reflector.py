"""ML-P1 tests: the Moonlight Reflection Engine.

Covers the ML-P1 acceptance battery (Section 11) at unit level:

  ML-P1-A  Reflection            -- a Moon exists, fully registered
  ML-P1-B  Identity Preservation -- reflected stars keep their ids;
                                    global identity is (universe, id)
  ML-P1-C  Isolation             -- Moon mutation leaves Sun unchanged
  ML-P1-D  Shared-State Detection-- no mutable object is shared
  ML-P1-E  Archive Before Delete -- delete refuses without archive
  ML-P1-F  Biography Preservation-- the biography survives the Moon

Plus the ruling clarifications: moon_type is mandatory and closed,
the registry is explicit/serializable, reflection events carry the
RAC-002 envelope, and moon_modified is recorded at store boundaries.
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from darkshield import Evidence, Galaxy, Relationship, Star, Universe
from darkshield.moonlight import MOON_TYPES, MoonlightError, Reflector


def make_sun() -> Universe:
    u = Universe(universe_id="sun")
    u.add_galaxy(Galaxy(id="galaxy:root", name="root", kind="directory"))
    u.add_star(Star(id="star:a", name="a.md", path="a.md", size_bytes=3))
    u.add_star(Star(id="star:b", name="b.md", path="b.md", size_bytes=5))
    u.add_relationship(Relationship(
        id="gravity:ab", source="star:a", target="star:b",
        relation="same_directory",
        evidence=[Evidence(source="same_directory", observations=1,
                           confidence=1.0,
                           details={"value": ".", "group_size": 2})],
    ))
    return u


def mutable_ids(obj) -> set[int]:
    """Ids of every mutable object reachable from `obj`."""
    found: set[int] = set()
    stack = [obj]
    while stack:
        o = stack.pop()
        if isinstance(o, (str, int, float, bool, type(None), datetime)):
            continue
        if id(o) in found:
            continue
        found.add(id(o))
        if isinstance(o, dict):
            stack.extend(o.keys())
            stack.extend(o.values())
        elif isinstance(o, (list, tuple, set, frozenset)):
            stack.extend(o)
        elif hasattr(o, "__dict__"):
            stack.extend(vars(o).values())
    return found


def test_a_reflection_creates_registered_moon() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sun = make_sun()
        reflector = Reflector(tmp)
        moon = reflector.create_moon(sun, "research", "gravity-analysis")
        meta = moon.meta["moon"]
        assert meta["moon_id"] == moon.universe_id
        assert meta["moon_type"] == "research"
        assert meta["parent_universe"] == "sun"
        assert meta["purpose"] == "gravity-analysis"
        assert meta["snapshot_id"].startswith("snap:")
        record = reflector.list_moons()[0]
        assert record["status"] == "active"
        assert record["moon_type"] == "research"
        # the snapshot artifact exists: evidence of origin
        snapshot = Path(tmp) / "snapshots" / (
            meta["snapshot_id"].replace(":", "_") + ".json")
        assert snapshot.exists()
        # the Sun recorded the Moon's existence (Section 10)
        assert any(e["event_type"] == "moon_created"
                   for e in sun.history)


def test_moon_type_is_mandatory_and_closed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        reflector = Reflector(tmp)
        for moon_type in MOON_TYPES:
            moon = reflector.create_moon(make_sun(), moon_type, "p")
            assert moon.meta["moon"]["moon_type"] == moon_type
        with pytest.raises(MoonlightError):
            reflector.create_moon(make_sun(), "party", "p")


def test_b_identity_preservation_and_envelope() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sun = make_sun()
        moon = Reflector(tmp).create_moon(sun, "research", "p")
        # reflected stars keep their ids (SI-001 continuity claim)
        assert {n.id for n in moon.nodes} == {n.id for n in sun.nodes}
        # global identity is (universe_id, object_id): related, distinct
        assert moon.universe_id != sun.universe_id
        events = [e for e in moon.history
                  if e["event_type"] == "reflection_created"]
        assert len(events) == 1
        event = events[0]
        # RAC-002 envelope (ML-P1 ruling, Finding 5)
        assert event["event_id"].startswith("evt:")
        assert event["schema_version"] == "1.0"
        assert event["timestamp"]
        assert event["producer"] == "moonlight-reflector"
        # reflection lineage
        assert event["origin_universe"] == "sun"
        assert event["lineage"]["snapshot_id"] == event["snapshot_id"]


def test_c_isolation_moon_mutation_leaves_sun_unchanged() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sun = make_sun()
        moon = Reflector(tmp).create_moon(sun, "research", "p")
        before = json.dumps(sun.to_dict(), sort_keys=True, default=str)
        moon.add_star(Star(id="star:new", name="new.md",
                           path="new.md", size_bytes=1))
        next(n for n in moon.nodes if n.id == "star:a").name = "renamed"
        moon.history.append({"event_type": "experiment_executed"})
        after = json.dumps(sun.to_dict(), sort_keys=True, default=str)
        assert before == after


def test_d_no_shared_mutable_state() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sun = make_sun()
        moon = Reflector(tmp).create_moon(sun, "research", "p")
        assert mutable_ids(sun).isdisjoint(mutable_ids(moon))


def test_registry_is_visible_and_serializable() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        reflector = Reflector(tmp)
        reflector.create_moon(make_sun(), "development", "p")
        raw = json.loads((Path(tmp) / "registry.json").read_text())
        record = next(iter(raw["moons"].values()))
        assert record["moon_type"] == "development"
        assert record["storage_path"]
        assert record["status"] == "active"
        # a second Reflector over the same store sees the same registry
        assert Reflector(tmp).list_moons()[0]["moon_id"] == record["moon_id"]


def test_load_and_save_moon_modified_at_store_boundary() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        reflector = Reflector(tmp)
        moon = reflector.create_moon(make_sun(), "research", "p")
        loaded = reflector.load_moon(moon.universe_id)
        assert any(e["event_type"] == "moon_loaded"
                   for e in loaded.history)
        # an unchanged save records nothing
        assert reflector.save_moon(loaded) is False
        # a changed save records moon_modified exactly once
        next(n for n in loaded.nodes if n.id == "star:a").name = "a2.md"
        assert reflector.save_moon(loaded) is True
        assert sum(1 for e in loaded.history
                   if e["event_type"] == "moon_modified") == 1
        with pytest.raises(MoonlightError):
            reflector.load_moon("moon:does-not-exist")


def test_e_delete_refuses_without_archive() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        reflector = Reflector(tmp)
        moon = reflector.create_moon(make_sun(), "research", "p")
        with pytest.raises(MoonlightError):
            reflector.delete_moon(moon.universe_id)
        reflector.archive_moon(moon.universe_id)
        record = reflector.delete_moon(moon.universe_id)
        assert record["status"] == "deleted"
        moon_file = Path(tmp) / record["storage_path"]
        assert not moon_file.exists()
        with pytest.raises(MoonlightError):
            reflector.load_moon(moon.universe_id)


def test_f_biography_survives_the_moon() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sun = make_sun()
        reflector = Reflector(tmp)
        moon = reflector.create_moon(sun, "hallucination", "hai-cradle")
        reflector.archive_moon(moon.universe_id, sun=sun)
        reflector.delete_moon(moon.universe_id)
        # the archive bundle retains the full biography
        bundle = reflector.load_archive(moon.universe_id)
        types = [e["event_type"] for e in bundle["history"]]
        assert "reflection_created" in types
        assert "moon_created" in types
        assert "moon_archived" in types
        assert bundle["moon_type"] == "hallucination"
        assert bundle["parent_universe"] == "sun"
        # the Sun's own history retains the lifecycle pair (Section 10)
        sun_types = [e["event_type"] for e in sun.history]
        assert "moon_created" in sun_types
        assert "moon_archived" in sun_types
        # and the registry still remembers the Moon existed
        assert reflector.list_moons()[0]["status"] == "deleted"
