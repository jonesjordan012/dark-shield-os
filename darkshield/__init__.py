"""Dark Shield canonical universe (M1) + data gravity engine (M2)."""

from .entities import (
    GALAXY_FATES,
    GALAXY_STATES,
    Entity,
    Galaxy,
    NeutronStar,
    Pulsar,
    Star,
)
from .gravity import (
    EVIDENCE_TYPES,
    FORMULA_M2A_V1,
    FORMULA_M2B_V1,
    SOURCE_BASE_WEIGHTS,
    Evidence,
    ExecutionEvidence,
    Explanation,
    GravityCalculator,
    ImportEvidence,
    aggregate_confidence,
    calculate_gravity,
    derive_gravity,
)
from .relations import RELATION_TYPES, Relationship
from .universe import Universe

__all__ = [
    "Entity",
    "Star",
    "Pulsar",
    "NeutronStar",
    "Galaxy",
    "GALAXY_STATES",
    "GALAXY_FATES",
    "Relationship",
    "RELATION_TYPES",
    "Universe",
    "Evidence",
    "ImportEvidence",
    "ExecutionEvidence",
    "EVIDENCE_TYPES",
    "Explanation",
    "derive_gravity",
    "aggregate_confidence",
    "GravityCalculator",
    "calculate_gravity",
    "SOURCE_BASE_WEIGHTS",
    "FORMULA_M2A_V1",
    "FORMULA_M2B_V1",
]
