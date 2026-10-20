"""Dark Shield canonical universe (M1)."""

from .entities import Entity, Galaxy, NeutronStar, Pulsar, Star
from .relations import RELATION_TYPES, Relationship
from .universe import Universe

__all__ = [
    "Entity",
    "Star",
    "Pulsar",
    "NeutronStar",
    "Galaxy",
    "Relationship",
    "RELATION_TYPES",
    "Universe",
]
