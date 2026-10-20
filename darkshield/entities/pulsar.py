"""Pulsar: a running process (active computation)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from .base import Entity


@dataclass(slots=True)
class Pulsar(Entity):
    CLASS_TYPE: ClassVar[str] = "pulsar"

    pid: int = 0
    cpu_percent: float = 0.0
    memory_mb: float = 0.0

    def __post_init__(self) -> None:
        Entity.__post_init__(self)
        if not self.classification_kind:
            self.classification_kind = "process"

    def properties_dict(self) -> dict:
        return {
            "pid": self.pid,
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
        }
