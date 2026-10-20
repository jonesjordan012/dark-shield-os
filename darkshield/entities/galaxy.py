"""Galaxy: a structural container (M1).

M1 kinds: directory, application, workspace — all observed
structurally (classification_source="filesystem").

M3 kinds (NOT M1): development, research, communication,
learning, creativity — these require inference or declaration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from .base import Entity

M1_KINDS = frozenset({"directory", "application", "workspace"})


@dataclass(slots=True)
class Galaxy(Entity):
    CLASS_TYPE: ClassVar[str] = "galaxy"

    kind: str = "directory"
    continuity: float = 1.0

    def __post_init__(self) -> None:
        Entity.__post_init__(self)
        if self.kind not in M1_KINDS:
            raise ValueError(
                f"{self.id}: galaxy kind {self.kind!r} is not an M1 "
                f"structural kind {sorted(M1_KINDS)}; "
                "intent kinds belong to M3"
            )
        if not self.classification_kind:
            self.classification_kind = self.kind

    def properties_dict(self) -> dict:
        return {
            "kind": self.kind,
            "continuity": self.continuity,
        }
