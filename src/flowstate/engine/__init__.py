"""Recommendation engine."""

from .camelot import (
    CAMELOT_WHEEL,
    compute_compatible_keys,
    get_compatible_keys,
    key_compatibility_score,
    to_camelot,
)
from .engine import RecommendationEngine, ScoringConfig
from .factors import (
    DEFAULT_FACTORS,
    DanceabilityFactor,
    EnergyTrajectoryFactor,
    GenreAffinityFactor,
    GrooveCompatibilityFactor,
    KeyQualityFactor,
    MixEaseFactor,
    NarrativeFlowFactor,
    ScoringFactor,
    VibeCompatibilityFactor,
)

__all__ = [
    # Camelot
    "CAMELOT_WHEEL",
    "compute_compatible_keys",
    "get_compatible_keys",
    "key_compatibility_score",
    "to_camelot",
    # Engine
    "RecommendationEngine",
    "ScoringConfig",
    # Factors
    "DEFAULT_FACTORS",
    "DanceabilityFactor",
    "EnergyTrajectoryFactor",
    "GenreAffinityFactor",
    "GrooveCompatibilityFactor",
    "KeyQualityFactor",
    "MixEaseFactor",
    "NarrativeFlowFactor",
    "ScoringFactor",
    "VibeCompatibilityFactor",
]
