"""Relationship: a first-class connection between two entities.

Data Gravity emerges from relationships, so they are modeled
explicitly — not as attributes of nodes, but as entities of
their own standing.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import ClassVar


def _now() -> datetime:
    return datetime.now(timezone.utc)


# Must match the relation enum in schemas/universe.schema.json.
RELATION_TYPES: frozenset[str] = frozenset({
    "contains",
    "depends_on",
    "uses",
    "runs_on",
    "executes",
    "related_to",
    "belongs_to",
    "inherits_from",
    "split_into",
    "merged_from",
    "generated_echo",
})


@dataclass(slots=True)
class Relationship:
    id: str
    source: str
    target: str
    relation: str
    weight: float = 1.0
    evidence: dict | None = None
    created_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        if self.relation not in RELATION_TYPES:
            raise ValueError(
                f"{self.id}: unknown relation {self.relation!r} "
                f"(known: {sorted(RELATION_TYPES)})"
            )
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(
                f"{self.id}: weight {self.weight} outside [0.0, 1.0]"
            )

    def to_dict(self) -> dict:
        """Plain JSON-safe dict of fields. Round-trips with from_dict()."""
        d = asdict(self)
        value = d.get("created_at")
        if isinstance(value, datetime):
            d["created_at"] = value.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Relationship:
        data = dict(data)
        value = data.get("created_at")
        if isinstance(value, str):
            data["created_at"] = datetime.fromisoformat(value)
        return cls(**data)

    def to_rel_dict(self) -> dict:
        """Serialize to a universe.json schema relationship."""
        d: dict = {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "weight": self.weight,
            "created_at": self.created_at.isoformat(),
        }
        if self.evidence is not None:
            d["evidence"] = self.evidence
        return d

    @classmethod
    def from_rel_dict(cls, data: dict) -> Relationship:
        created = data.get("created_at")
        return cls(
            id=data["id"],
            source=data["source"],
            target=data["target"],
            relation=data["relation"],
            weight=data.get("weight", 1.0),
            evidence=data.get("evidence"),
            created_at=(
                datetime.fromisoformat(created) if created else _now()
            ),
        )
