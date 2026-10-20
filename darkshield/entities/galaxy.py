"""Galaxy: a structural container (M1), extended for M3-A.

M1 kinds: directory, application, workspace — all observed
structurally (classification_source="filesystem").

M3 kinds (NOT M1): development, research, communication,
learning, creativity — these require inference or declaration.
They are never kinds; in M3-A they may only ever appear as
user-declared labels.

M3-A extension (Citizen ruling 2026-10-20):
- state: current condition (reversible) — ACTIVE / DORMANT / ARCHIVED.
- fate: historical outcome — UNKNOWN / PERSISTED / TRANSFORMED /
  SPLIT / MERGED / DISSOLVED. (REMOVED is rejected: Retention Doctrine.)
- labels: declared by the user only. Never inferred, never promoted
  from structure (First Constitutional Principle).
- evidence_refs: traceable observational sources.
- parent_id: lineage metadata.
- Membership is DERIVED from the graph, never stored here:
  see members(universe).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from .base import Entity

M1_KINDS = frozenset({"directory", "application", "workspace"})

#: Astronomical State — current condition. Reversible.
GALAXY_STATES = frozenset({"ACTIVE", "DORMANT", "ARCHIVED"})

#: Fate — historical outcome. The 2026-10-19 standardized set.
GALAXY_FATES = frozenset({
    "UNKNOWN",
    "PERSISTED",
    "TRANSFORMED",
    "SPLIT",
    "MERGED",
    "DISSOLVED",
})


@dataclass(slots=True)
class Galaxy(Entity):
    CLASS_TYPE: ClassVar[str] = "galaxy"

    kind: str = "directory"
    continuity: float = 1.0
    state: str = "ACTIVE"
    fate: str = "UNKNOWN"
    labels: list = field(default_factory=list)
    evidence_refs: list = field(default_factory=list)
    parent_id: str | None = None

    def __post_init__(self) -> None:
        Entity.__post_init__(self)
        if self.kind not in M1_KINDS:
            raise ValueError(
                f"{self.id}: galaxy kind {self.kind!r} is not an M1 "
                f"structural kind {sorted(M1_KINDS)}; "
                "intent kinds belong to M3"
            )
        if self.state not in GALAXY_STATES:
            raise ValueError(
                f"{self.id}: unknown state {self.state!r} "
                f"(known: {sorted(GALAXY_STATES)})"
            )
        if self.fate not in GALAXY_FATES:
            raise ValueError(
                f"{self.id}: unknown fate {self.fate!r} "
                f"(known: {sorted(GALAXY_FATES)}); note REMOVED is "
                "rejected under the Retention Doctrine"
            )
        if not self.classification_kind:
            self.classification_kind = self.kind

    # -- M3-A: declared labels ------------------------------------------

    def declare_label(self, label: str) -> Galaxy:
        """Record a user-declared label. A declaration is an act of the
        user, never an inference of the system. Duplicates are ignored."""
        label = label.strip()
        if not label:
            raise ValueError(f"{self.id}: label must not be empty")
        if label not in self.labels:
            self.labels.append(label)
        return self

    # -- M3-A: derived membership ---------------------------------------

    def members(self, universe: object) -> list[str]:
        """Derive member ids from the universe's relationships.

        Membership is computed, never stored: stars the galaxy `contains`,
        plus stars that `belongs_to` it. Sorted for determinism.
        """
        found: set[str] = set()
        for rel in universe.relationships:  # type: ignore[attr-defined]
            if rel.source == self.id and rel.relation == "contains":
                found.add(rel.target)
            elif rel.target == self.id and rel.relation == "belongs_to":
                found.add(rel.source)
        return sorted(found)

    def describe(self, universe: object | None = None) -> str:
        """Observational summary only — structure, never meaning."""
        lines = [
            f"{self.id} (galaxy) '{self.name}'",
            f"kind {self.kind}, state {self.state}, fate {self.fate}, "
            f"continuity {self.continuity:.2f}",
        ]
        if self.labels:
            lines.append(f"declared labels: {', '.join(self.labels)}")
        if universe is not None:
            member_ids = self.members(universe)
            lines.append(f"{len(member_ids)} members (derived)")
            for rel in universe.related_to(self.id):  # type: ignore[attr-defined]
                lines.append(
                    f"  - {rel.relation} "
                    f"{rel.target if rel.source == self.id else rel.source}"
                    f": gravity {rel.gravity():.2f}"
                )
        return "\n".join(lines)

    def properties_dict(self) -> dict:
        return {
            "kind": self.kind,
            "continuity": self.continuity,
            "state": self.state,
            "fate": self.fate,
            "labels": list(self.labels),
            "evidence_refs": list(self.evidence_refs),
            "parent_id": self.parent_id,
        }
