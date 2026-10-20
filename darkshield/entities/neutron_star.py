"""NeutronStar: a CPU core (compute resource)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from .base import Entity


@dataclass(slots=True)
class NeutronStar(Entity):
    CLASS_TYPE: ClassVar[str] = "neutron_star"

    core_index: int = 0
    utilization: float = 0.0

    def __post_init__(self) -> None:
        Entity.__post_init__(self)
        if not self.classification_kind:
            self.classification_kind = "cpu_core"

    def properties_dict(self) -> dict:
        return {
            "core_index": self.core_index,
            "utilization": self.utilization,
        }
