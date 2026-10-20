"""Dark Shield canonical entities (M1) + M3-A galaxy extension."""

from .base import Entity
from .galaxy import GALAXY_FATES, GALAXY_STATES, Galaxy
from .neutron_star import NeutronStar
from .pulsar import Pulsar
from .star import Star

__all__ = [
    "Entity",
    "Star",
    "Pulsar",
    "NeutronStar",
    "Galaxy",
    "GALAXY_STATES",
    "GALAXY_FATES",
]
