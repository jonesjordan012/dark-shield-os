"""Relationship: a first-class connection between two entities.

Data Gravity emerges from relationships, so they are modeled
explicitly — not as attributes of nodes, but as entities of
their own standing.

M2 model: evidence is authoritative (a list), gravity is derived from it.
The stored ``weight`` field is retained for M1 compatibility; M2-D will
synchronize it with the derived gravity.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import ClassVar

from darkshield.gravity.calculator import FORMULA_M2B_V1
from darkshield.gravity.evidence import Evidence
from darkshield.gravity.models import (
    Explanation,
    aggregate_confidence,
    derive_gravity,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


# Must match the relation enum in schemas/universe.schema.json.
# The first eleven are the M1 structural types. The final eight are
# the DG-0/DG-1 gravity registry (ruled 2026-10-20): a single
# vocabulary, no aliases, no alternate spellings.
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
    "same_directory",
    "shared_parent_directory",
    "shared_extension",
    "shared_name_stem",
    "duplicate_candidate",
    "temporal_neighbor",
    "derived_from",
    "unknown",
})

#: The DG-0/DG-1 gravity registry subset of RELATION_TYPES.
GRAVITY_RELATION_TYPES: frozenset[str] = frozenset({
    "same_directory",
    "shared_parent_directory",
    "shared_extension",
    "shared_name_stem",
    "duplicate_candidate",
    "temporal_neighbor",
    "derived_from",
    "unknown",
})


@dataclass(slots=True)
class Relationship:
    id: str
    source: str
    target: str
    relation: str
    weight: float = 1.0
    evidence: list = field(default_factory=list)
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
        # Normalize evidence to a list of Evidence objects. Accepts
        # Evidence instances, plain dicts (kind-dispatched), a single
        # dict, or the legacy M1 evidence object shape.
        raw = self.evidence if isinstance(self.evidence, list) else [self.evidence]
        normalized: list[Evidence] = []
        for item in raw:
            if item is None:
                continue
            if isinstance(item, Evidence):
                normalized.append(item)
            else:
                normalized.append(Evidence.from_dict(dict(item)))
        self.evidence = normalized

    # -- M2: evidence-authoritative model ------------------------------

    def attach_evidence(self, evidence: Evidence) -> Relationship:
        """Append evidence to this relationship. Returns self for chaining."""
        if not isinstance(evidence, Evidence):
            raise TypeError(
                f"attach_evidence expects Evidence, got {type(evidence).__name__}"
            )
        self.evidence.append(evidence)
        return self

    def detach_evidence(self, source: str) -> list:
        """Remove all evidence from one source. Returns what was removed.

        DG-1 lifecycle: when a gravity source stops firing for this
        relationship, its evidence is detached (the Universe records
        the change as gravity_updated; the history is never rewritten).
        """
        removed = [e for e in self.evidence if e.source == source]
        if removed:
            self.evidence = [e for e in self.evidence if e.source != source]
        return removed

    def primary_evidence(self) -> Evidence | None:
        """First attached evidence, if any."""
        return self.evidence[0] if self.evidence else None

    def gravity(self) -> float:
        """Derived gravity in [0.0, 1.0], computed from evidence.

        Evidence is authoritative; this number is derived using the
        current formula (m2b-v1). No evidence means no gravity (DG-6).
        """
        return derive_gravity(
            [e.to_dict() for e in self.evidence], FORMULA_M2B_V1
        )

    @property
    def confidence(self) -> float:
        """Aggregate confidence (noisy-OR over evidence)."""
        return aggregate_confidence([e.to_dict() for e in self.evidence])

    def explain(self) -> Explanation:
        """Build a verifiable explanation of this relationship's gravity."""
        snapshots = [e.to_dict() for e in self.evidence]
        return Explanation(
            relationship_id=self.id,
            source=self.source,
            target=self.target,
            relation=self.relation,
            evidence=snapshots,
            gravity=self.gravity(),
            confidence=self.confidence,
            formula=FORMULA_M2B_V1,
        )

    # -- serialization --------------------------------------------------

    def to_dict(self) -> dict:
        """Plain JSON-safe dict of fields. Round-trips with from_dict()."""
        d = asdict(self)
        value = d.get("created_at")
        if isinstance(value, datetime):
            d["created_at"] = value.isoformat()
        # Serialize evidence explicitly: asdict() would drop the kind
        # marker that from_dict() needs to restore evidence subtypes.
        d["evidence"] = [e.to_dict() for e in self.evidence]
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
        if self.evidence:
            d["evidence"] = [e.to_dict() for e in self.evidence]
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
