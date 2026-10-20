"""Moonlight (ML-001 / ML-P1): the reflection engine.

Phase 1 implements the minimum viable Moonlight system capable of
proving constitutional containment:

    reflection, identity preservation, isolation, archival.

It does NOT implement experimentation, Hallucinate AI, promotion,
or cross-Moon interaction (ML-P1 Section 2).

Constitutional summary (ML-P1, Citizen ruling 2026-10-20):

    "A certified Phase 1 does not prove that Dark Shield can
    experiment. A certified Phase 1 proves that Dark Shield can
    contain experimentation."
"""

from .reflector import (
    MOON_TYPES,
    REFLECTOR_VERSION,
    MoonlightError,
    Reflector,
)

__all__ = [
    "MOON_TYPES",
    "REFLECTOR_VERSION",
    "MoonlightError",
    "Reflector",
]
