"""ML-P1 certification battery: Moonlight Reflection Engine.

Run from the repo root:

    python mlp1_battery.py

Executes the ML-P1 acceptance battery (ML-P1 Section 11). Phase 1
does not prove experimentation; it proves containment (ML-001 /
ML-P1, Citizen ruling 2026-10-20).

  ML-P1-A  Reflection
  ML-P1-B  Identity Preservation
  ML-P1-C  Isolation
  ML-P1-D  Shared-State Detection
  ML-P1-E  Archive Before Delete
  ML-P1-F  Biography Preservation
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from darkshield import Evidence, Galaxy, Relationship, Star, Universe  # noqa: E402
from darkshield.moonlight import MoonlightError, Reflector  # noqa: E402

RESULTS: list[tuple[str, bool]] = []


def check(label: str, ok: bool, detail: str) -> None:
    RESULTS.append((label, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {detail}")


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


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="mlp1-battery-")
    sun = make_sun()
    reflector = Reflector(tmp)
    moon = reflector.create_moon(sun, "research", "mlp1-battery")

    print("\nML-P1-A: Reflection")
    meta = moon.meta.get("moon", {})
    check("A", moon.universe_id.startswith("moon:")
          and meta.get("moon_type") == "research"
          and meta.get("parent_universe") == "sun"
          and bool(meta.get("snapshot_id")),
          "Moon exists with complete mandatory metadata "
          "(moon_id, moon_type, parent_universe, snapshot_id, purpose)")
    check("A", len(reflector.list_moons()) == 1
          and reflector.list_moons()[0]["status"] == "active",
          "Moon is recorded in the explicit, serializable registry")

    print("\nML-P1-B: Identity Preservation")
    check("B", {n.id for n in moon.nodes} == {n.id for n in sun.nodes},
          "Reflected stars keep their Sun identities (SI-001)")
    event = next(e for e in moon.history
                 if e["event_type"] == "reflection_created")
    check("B", event["origin_universe"] == "sun"
          and event["lineage"]["snapshot_id"] == event["snapshot_id"]
          and event["event_id"].startswith("evt:")
          and event["schema_version"] == "1.0",
          "Reflection is a continuity claim: RAC-002 envelope, "
          "snapshot evidence, reflection lineage")

    print("\nML-P1-C: Isolation")
    before = json.dumps(sun.to_dict(), sort_keys=True, default=str)
    moon.add_star(Star(id="star:new", name="new.md",
                       path="new.md", size_bytes=1))
    next(n for n in moon.nodes if n.id == "star:a").name = "renamed"
    moon.history.append({"event_type": "experiment_executed"})
    after = json.dumps(sun.to_dict(), sort_keys=True, default=str)
    check("C", before == after,
          "Moon mutation (add, rename, history) leaves the Sun unchanged")

    print("\nML-P1-D: Shared-State Detection")
    check("D", mutable_ids(sun).isdisjoint(mutable_ids(moon)),
          "No mutable object reference is shared between Sun and Moon "
          "(isolation by construction)")

    print("\nML-P1-E: Archive Before Delete")
    try:
        reflector.delete_moon(moon.universe_id)
        refused = False
    except MoonlightError:
        refused = True
    check("E", refused,
          "delete_moon() on an unarchived Moon fails (refusal model)")
    reflector.archive_moon(moon.universe_id, sun=sun)
    record = reflector.delete_moon(moon.universe_id)
    check("E", record["status"] == "deleted"
          and not (Path(tmp) / record["storage_path"]).exists(),
          "Archived Moon deletes successfully, in constitutional order")

    print("\nML-P1-F: Biography Preservation")
    bundle = reflector.load_archive(moon.universe_id)
    types = [e["event_type"] for e in bundle["history"]]
    check("F", "reflection_created" in types and "moon_created" in types
          and "moon_archived" in types,
          "Archive bundle retains the Moon's biography after deletion")
    sun_types = [e["event_type"] for e in sun.history]
    check("F", "moon_created" in sun_types and "moon_archived" in sun_types,
          "Sun history retains moon_created / moon_archived: the Moon "
          "ended; its biography did not")

    passed = sum(1 for _, ok in RESULTS if ok)
    print(f"\nML-P1 battery: {passed}/{len(RESULTS)} checks passed")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
