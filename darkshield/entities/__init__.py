"""Dark Shield canonical entities (M1)."""

from .base import Entity
from .galaxy import Galaxy
from .neutron_star import NeutronStar
from .pulsar import Pulsar
from .star import Star

__all__ = ["Entity", "Star", "Pulsar", "NeutronStar", "Galaxy"]
