"""Universe: the canonical reality layer (M1).

A Universe holds entities (nodes), relationships, and history.
It serializes directly to universe.json and reconstructs from it:

    universe = Universe(universe_id="urn:darkshield:universe:primary")
    universe.add(Star(...))
    universe.add(Galaxy(...))
    universe.add_relationship(Relationship(...))
    path = universe.save("universe.json")

    universe2 = Universe.load(path)
    assert universe == universe2
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .entities import Entity
from .relations import Relationship

SCHEMA_VERSION = "0.1"


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Universe:
    universe_id: str
    nodes: list[Entity] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)
    meta: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)
    snapshot_at: datetime = field(default_factory=_now)

    def add(self, entity: Entity) -> Entity:
        """Add a node. Duplicate ids are rejected."""
        if any(n.id == entity.id for n in self.nodes):
            raise ValueError(f"duplicate node id: {entity.id}")
        self.nodes.append(entity)
        self.snapshot_at = _now()
        return entity

    def add_star(self, star: Entity) -> Entity:
        return self.add(star)

    def add_galaxy(self, galaxy: Entity) -> Entity:
        return self.add(galaxy)

    def add_relationship(self, rel: Relationship) -> Relationship:
        """Add a relationship. Endpoints must exist (UC-3)."""
        node_ids = {n.id for n in self.nodes}
        if rel.source not in node_ids:
            raise ValueError(f"relationship source missing: {rel.source}")
        if rel.target not in node_ids:
            raise ValueError(f"relationship target missing: {rel.target}")
        if any(r.id == rel.id for r in self.relationships):
            raise ValueError(f"duplicate relationship id: {rel.id}")
        self.relationships.append(rel)
        self.snapshot_at = _now()
        return rel

    def record(self, entity_id: str, event: str, data: dict | None = None) -> dict:
        """Append a history fact (facts, not visualizations)."""
        entry = {
            "timestamp": _now().isoformat(),
            "entity_id": entity_id,
            "event": event,
            "data": data or {},
        }
        self.history.append(entry)
        return entry

    def to_dict(self) -> dict:
        """Serialize to the universe.json document shape."""
        return {
            "schema_version": SCHEMA_VERSION,
            "universe_id": self.universe_id,
            "created_at": self.created_at.isoformat(),
            "snapshot_at": self.snapshot_at.isoformat(),
            "meta": self.meta,
            "nodes": [n.to_node_dict() for n in self.nodes],
            "relationships": [r.to_rel_dict() for r in self.relationships],
            "history": self.history,
            "metrics": {
                "nodes": len(self.nodes),
                "relationships": len(self.relationships),
            },
            "validators": {},
        }

    def save(self, path: str | Path) -> Path:
        """Write universe.json. Returns the path."""
        p = Path(path)
        with open(p, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
            f.write("\n")
        return p

    @classmethod
    def load(cls, path: str | Path) -> Universe:
        """Reconstruct a Universe from universe.json."""
        with open(path) as f:
            data = json.load(f)

        def _parse_dt(value: str | None) -> datetime:
            if not value:
                return _now()
            return datetime.fromisoformat(value)

        universe = cls(
            universe_id=data["universe_id"],
            meta=data.get("meta", {}),
            history=data.get("history", []),
            created_at=_parse_dt(data.get("created_at")),
            snapshot_at=_parse_dt(data.get("snapshot_at")),
        )
        for node in data.get("nodes", []):
            universe.nodes.append(Entity.from_node_dict(node))
        for rel in data.get("relationships", []):
            universe.relationships.append(Relationship.from_rel_dict(rel))
        return universe
