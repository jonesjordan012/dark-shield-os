"""Star: an information object (file, document, code)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from .base import Entity


@dataclass(slots=True)
class Star(Entity):
    CLASS_TYPE: ClassVar[str] = "star"

    path: str = ""
    size_bytes: int = 0
    sha256: str | None = None

    def __post_init__(self) -> None:
        Entity.__post_init__(self)
        if not self.classification_kind:
            self.classification_kind = "file"

    def properties_dict(self) -> dict:
        return {
            "path": self.path,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }
