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
from uuid import uuid4

from .entities import Entity
from .relations import Relationship
from darkshield.gravity.models import Explanation

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

    def _emit_history(
        self,
        event_type: str,
        entity_id: str,
        fields: dict,
        context: dict | None = None,
    ) -> dict:
        """Append an enveloped history event (DG-0 / RAC-002 shape)."""
        entry: dict = {
            "event_id": f"evt:{uuid4().hex}",
            "event_type": event_type,
            "timestamp": _now().isoformat(),
            "schema_version": "1.0",
            "entity_id": entity_id,
        }
        entry.update(fields)
        if context:
            entry.update(context)
        self.history.append(entry)
        return entry

    def add_relationship(
        self, rel: Relationship, *, context: dict | None = None
    ) -> Relationship:
        """Add a relationship. Endpoints must exist (UC-3).

        DG-0: relationships have biographies — creation is recorded
        as a gravity_created history event.
        """
        node_ids = {n.id for n in self.nodes}
        if rel.source not in node_ids:
            raise ValueError(f"relationship source missing: {rel.source}")
        if rel.target not in node_ids:
            raise ValueError(f"relationship target missing: {rel.target}")
        if any(r.id == rel.id for r in self.relationships):
            raise ValueError(f"duplicate relationship id: {rel.id}")
        self.relationships.append(rel)
        self._emit_history(
            "gravity_created",
            rel.id,
            {
                "gravity_id": rel.id,
                "source_id": rel.source,
                "target_id": rel.target,
                "relationship_type": rel.relation,
            },
            context,
        )
        self.snapshot_at = _now()
        return rel

    def attach_evidence(
        self, relationship_id: str, evidence, *, context: dict | None = None
    ) -> Relationship:
        """Attach evidence to a relationship, recording gravity_updated.

        DG-0: an evidence change is part of the relationship's
        biography, not silent state.
        """
        rel = self.get_gravity(relationship_id)
        if rel is None:
            raise ValueError(f"unknown relationship: {relationship_id}")
        rel.attach_evidence(evidence)
        self._emit_history(
            "gravity_updated",
            rel.id,
            {
                "gravity_id": rel.id,
                "evidence_source": evidence.source,
                "gravity": rel.gravity(),
            },
            context,
        )
        self.snapshot_at = _now()
        return rel

    def detach_evidence(
        self, relationship_id: str, source: str, *, context: dict | None = None
    ) -> list:
        """Detach all evidence from one source (DG-1 lifecycle).

        Records gravity_updated when anything was actually removed.
        Returns the removed evidence items.
        """
        rel = self.get_gravity(relationship_id)
        if rel is None:
            raise ValueError(f"unknown relationship: {relationship_id}")
        removed = rel.detach_evidence(source)
        if removed:
            self._emit_history(
                "gravity_updated",
                rel.id,
                {
                    "gravity_id": rel.id,
                    "evidence_source": source,
                    "evidence_removed": len(removed),
                    "gravity": rel.gravity(),
                },
                context,
            )
            self.snapshot_at = _now()
        return removed

    def remove_relationship(
        self, relationship_id: str, *, context: dict | None = None
    ) -> Relationship | None:
        """Remove a relationship from the active graph (DG-0).

        "Removed" means no longer present — never erased. The
        gravity_removed event, and the relationship's whole history,
        remain on the record.
        """
        rel = self.get_gravity(relationship_id)
        if rel is None:
            return None
        self.relationships.remove(rel)
        self._emit_history(
            "gravity_removed",
            rel.id,
            {
                "gravity_id": rel.id,
                "source_id": rel.source,
                "target_id": rel.target,
                "relationship_type": rel.relation,
            },
            context,
        )
        self.snapshot_at = _now()
        return rel

    # -- DG-0 query API (Section 11) -------------------------------------

    def departed_star_ids(self) -> set[str]:
        """Stars whose latest presence event is a departure.

        Derived from history (RAC-002: no decision may exist solely
        as component state). Legacy v0.1 'not_observed' events count
        as departures. Used by the scanner (rediscovery) and by DG-1
        generation (departed stars are not part of the observed
        topology, so they generate no new gravity).
        """
        presence = {"star_birth", "star_departure", "star_rediscovery"}
        last: dict[str, str] = {}
        for entry in self.history:
            event_type = entry.get("event_type") or entry.get("event")
            star_id = entry.get("star_id") or entry.get("entity_id")
            if star_id is None:
                continue
            if event_type in presence:
                last[star_id] = event_type
            elif event_type == "not_observed":
                last[star_id] = "star_departure"
        return {sid for sid, ev in last.items() if ev == "star_departure"}

    def get_relationships(self, entity_id: str) -> list[Relationship]:
        """All relationships touching an entity."""
        return self.related_to(entity_id)

    def get_gravity(self, relationship_id: str) -> Relationship | None:
        """The relationship with this independent identity, or None."""
        return next(
            (r for r in self.relationships if r.id == relationship_id), None
        )

    def explain_relationship(self, relationship_id: str):
        """Explanation for a relationship, addressed by its own id."""
        rel = self.get_gravity(relationship_id)
        return rel.explain() if rel is not None else None

    # -- DG-2 queries (Section 11) ----------------------------------------

    def strongest_relationships(self, n: int = 10) -> list[Relationship]:
        """Relationships ranked by derived structural strength, strongest first."""
        return sorted(
            self.relationships, key=lambda r: r.gravity(), reverse=True
        )[:n]

    def weakest_relationships(self, n: int = 10) -> list[Relationship]:
        """Relationships ranked by derived structural strength, weakest first."""
        return sorted(self.relationships, key=lambda r: r.gravity())[:n]

    def related_stars(self, entity_id: str) -> list:
        """Entities on the other side of this entity's relationships."""
        by_id = {node.id: node for node in self.nodes}
        others: list = []
        seen: set[str] = set()
        for rel in self.relationships:
            other = None
            if rel.source == entity_id:
                other = rel.target
            elif rel.target == entity_id:
                other = rel.source
            if other is not None and other not in seen and other in by_id:
                seen.add(other)
                others.append(by_id[other])
        return others

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

    # -- M2: query API (explainability + ranking) ----------------------

    def find_relationship(
        self, source_id: str, target_id: str
    ) -> Relationship | None:
        """Find the relationship between two entities, either direction."""
        for rel in self.relationships:
            if rel.source == source_id and rel.target == target_id:
                return rel
        for rel in self.relationships:
            if rel.source == target_id and rel.target == source_id:
                return rel
        return None

    def explain(
        self, source_id: str, target_id: str
    ) -> Explanation | None:
        """Explain why two entities are connected (M2-C).

        Returns the relationship's verifiable explanation, or None when
        the entities share no relationship.
        """
        rel = self.find_relationship(source_id, target_id)
        return rel.explain() if rel is not None else None

    def related_to(self, entity_id: str) -> list[Relationship]:
        """All relationships touching an entity, either direction."""
        return [
            r
            for r in self.relationships
            if r.source == entity_id or r.target == entity_id
        ]

    def most_connected(self, n: int = 5) -> list[tuple[str, int]]:
        """Entities ranked by relationship count (ties broken by id)."""
        counts: dict[str, int] = {}
        for rel in self.relationships:
            counts[rel.source] = counts.get(rel.source, 0) + 1
            counts[rel.target] = counts.get(rel.target, 0) + 1
        ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        return ranked[: max(0, n)]

    def top_gravity(self, n: int = 5) -> list[tuple[str, float]]:
        """Entities ranked by total gravity across their relationships."""
        totals: dict[str, float] = {}
        for rel in self.relationships:
            gravity = rel.gravity()
            totals[rel.source] = totals.get(rel.source, 0.0) + gravity
            totals[rel.target] = totals.get(rel.target, 0.0) + gravity
        ranked = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))
        return ranked[: max(0, n)]

    def most_gravitational(self, n: int = 5) -> list[tuple[str, float]]:
        """Top entities by gravity (M2-F name for top_gravity)."""
        return self.top_gravity(n)

    # -- M3-A: declared labels ------------------------------------------

    def _find_galaxy(self, galaxy_id: str):
        from .entities import Galaxy

        for node in self.nodes:
            if node.id == galaxy_id and isinstance(node, Galaxy):
                return node
        return None

    def declare_label(self, galaxy_id: str, label: str):
        """Record a user-declared label on a galaxy (M3-A, Amendment A).

        Labels are declarations, not discoveries: this is the ONLY way a
        label enters the universe. The system never infers one.
        Raises ValueError for an unknown galaxy id.
        """
        galaxy = self._find_galaxy(galaxy_id)
        if galaxy is None:
            raise ValueError(f"unknown galaxy: {galaxy_id}")
        galaxy.declare_label(label)
        self.snapshot_at = _now()
        return galaxy

    def labels(self, galaxy_id: str) -> list[str] | None:
        """The galaxy's declared labels, or None for an unknown galaxy."""
        galaxy = self._find_galaxy(galaxy_id)
        if galaxy is None:
            return None
        return list(galaxy.labels)

    def explain_entity(self, entity_id: str) -> str | None:
        """Human-readable summary of an entity's place in the universe.

        Answers "why is this star important?" with measured evidence.
        Returns None for an unknown entity id.
        """
        node = next((x for x in self.nodes if x.id == entity_id), None)
        if node is None:
            return None
        rels = self.related_to(entity_id)
        total = sum(r.gravity() for r in rels)
        lines = [
            f"{node.id} ({node.CLASS_TYPE}) '{node.name}'",
            f"{len(rels)} relationships, total gravity {total:.2f}",
        ]
        for rel in sorted(rels, key=lambda r: -r.gravity())[:5]:
            other = rel.target if rel.source == entity_id else rel.source
            lines.append(
                f"  - {rel.relation} {other}: gravity {rel.gravity():.2f}"
            )
            for evidence in rel.evidence:
                lines.append(f"      * {evidence.describe()}")
        return "\n".join(lines)

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
