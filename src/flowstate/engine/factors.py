"""Scoring factors for track recommendations."""

from abc import ABC, abstractmethod
from typing import Optional

from ..models import Direction, FactorScore, Track
from .camelot import key_compatibility_score


class ScoringFactor(ABC):
    """Base class for scoring factors."""

    name: str
    weight: float

    def __init__(self, weight: Optional[float] = None):
        if weight is not None:
            self.weight = weight

    @abstractmethod
    def score(
        self,
        current: Track,
        candidate: Track,
        direction: Direction,
    ) -> FactorScore:
        """
        Score a candidate track.

        Returns:
            FactorScore with score between 0 and 1
        """
        pass


class EnergyTrajectoryFactor(ScoringFactor):
    """Does energy delta match the requested direction?"""

    name = "Energy Trajectory"
    weight = 1.0

    def score(self, current: Track, candidate: Track, direction: Direction) -> FactorScore:
        delta = candidate.energy - current.energy

        if direction == Direction.UP:
            # Want positive delta, ideally +1 to +3
            if delta >= 1:
                raw = min(delta / 3, 1.0)  # +3 or more = 1.0
            else:
                raw = 0.0
            reason = f"Energy {current.energy} → {candidate.energy} ({delta:+d})"

        elif direction == Direction.DOWN:
            # Want negative delta, ideally -1 to -3
            if delta <= -1:
                raw = min(abs(delta) / 3, 1.0)
            else:
                raw = 0.0
            reason = f"Energy {current.energy} → {candidate.energy} ({delta:+d})"

        else:  # HOLD
            # Want minimal change (±1)
            if abs(delta) <= 1:
                raw = 1.0 - (abs(delta) * 0.3)
            else:
                raw = max(0, 1.0 - (abs(delta) * 0.3))
            reason = f"Energy delta: {delta:+d}"

        return FactorScore(
            name=self.name,
            score=raw,
            weight=self.weight,
            weighted_score=raw * self.weight,
            reason=reason,
        )


class DanceabilityFactor(ScoringFactor):
    """Keep the dancefloor moving."""

    name = "Danceability"
    weight = 0.8

    def score(self, current: Track, candidate: Track, direction: Direction) -> FactorScore:
        # High danceability is always good, but big drops are bad
        delta = candidate.danceability - current.danceability

        # Reward high danceability
        base_score = candidate.danceability / 10

        # Penalize big drops in danceability
        if delta < -2:
            penalty = abs(delta + 2) * 0.15
            raw = max(0, base_score - penalty)
            reason = f"Danceability drop: {current.danceability} → {candidate.danceability}"
        else:
            raw = base_score
            reason = f"Danceability: {candidate.danceability}/10"

        return FactorScore(
            name=self.name,
            score=raw,
            weight=self.weight,
            weighted_score=raw * self.weight,
            reason=reason,
        )


class VibeCompatibilityFactor(ScoringFactor):
    """Score vibe/mood transitions."""

    name = "Vibe Compatibility"
    weight = 0.7

    # Vibe compatibility matrix (row = from, col = to)
    # 1.0 = great transition, 0.5 = neutral, 0.0 = jarring
    VIBE_MATRIX = {
        "dark": {"dark": 1.0, "hypnotic": 0.8, "aggressive": 0.7, "chill": 0.3, "bright": 0.2, "euphoric": 0.1},
        "bright": {"bright": 1.0, "euphoric": 0.9, "chill": 0.6, "hypnotic": 0.4, "dark": 0.2, "aggressive": 0.3},
        "hypnotic": {"hypnotic": 1.0, "dark": 0.8, "chill": 0.7, "euphoric": 0.5, "bright": 0.4, "aggressive": 0.4},
        "euphoric": {"euphoric": 1.0, "bright": 0.9, "aggressive": 0.6, "hypnotic": 0.5, "chill": 0.3, "dark": 0.2},
        "chill": {"chill": 1.0, "hypnotic": 0.7, "bright": 0.6, "dark": 0.4, "euphoric": 0.3, "aggressive": 0.1},
        "aggressive": {"aggressive": 1.0, "dark": 0.8, "euphoric": 0.6, "hypnotic": 0.5, "bright": 0.3, "chill": 0.1},
    }

    def score(self, current: Track, candidate: Track, direction: Direction) -> FactorScore:
        from_vibe = current.vibe if isinstance(current.vibe, str) else current.vibe.value
        to_vibe = candidate.vibe if isinstance(candidate.vibe, str) else candidate.vibe.value

        raw = self.VIBE_MATRIX.get(from_vibe, {}).get(to_vibe, 0.5)

        if from_vibe == to_vibe:
            reason = f"Same vibe: {to_vibe}"
        else:
            reason = f"Vibe: {from_vibe} → {to_vibe}"

        return FactorScore(
            name=self.name,
            score=raw,
            weight=self.weight,
            weighted_score=raw * self.weight,
            reason=reason,
        )


class NarrativeFlowFactor(ScoringFactor):
    """Score set position progression (opener → journey → peak → closer)."""

    name = "Narrative Flow"
    weight = 0.6

    # Natural progression order
    INTENSITY_ORDER = {"opener": 0, "journey": 1, "peak": 2, "closer": 3}

    # Transition scores: (from_intensity, to_intensity) -> score
    FLOW_MATRIX = {
        "opener": {"opener": 0.7, "journey": 1.0, "peak": 0.4, "closer": 0.2},
        "journey": {"opener": 0.3, "journey": 0.9, "peak": 1.0, "closer": 0.5},
        "peak": {"opener": 0.1, "journey": 0.6, "peak": 0.8, "closer": 1.0},
        "closer": {"opener": 0.5, "journey": 0.4, "peak": 0.3, "closer": 0.8},
    }

    def score(self, current: Track, candidate: Track, direction: Direction) -> FactorScore:
        from_int = current.intensity if isinstance(current.intensity, str) else current.intensity.value
        to_int = candidate.intensity if isinstance(candidate.intensity, str) else candidate.intensity.value

        raw = self.FLOW_MATRIX.get(from_int, {}).get(to_int, 0.5)

        # Adjust based on direction
        from_order = self.INTENSITY_ORDER.get(from_int, 1)
        to_order = self.INTENSITY_ORDER.get(to_int, 1)

        if direction == Direction.UP and to_order > from_order:
            raw = min(1.0, raw + 0.2)
        elif direction == Direction.DOWN and to_order < from_order:
            raw = min(1.0, raw + 0.2)

        reason = f"Flow: {from_int} → {to_int}"

        return FactorScore(
            name=self.name,
            score=raw,
            weight=self.weight,
            weighted_score=raw * self.weight,
            reason=reason,
        )


class KeyQualityFactor(ScoringFactor):
    """Score harmonic compatibility using Camelot wheel."""

    name = "Key Quality"
    weight = 0.5

    def score(self, current: Track, candidate: Track, direction: Direction) -> FactorScore:
        raw = key_compatibility_score(current.key, candidate.key)

        if raw >= 0.9:
            reason = f"Key: {current.key} → {candidate.key} (harmonic)"
        elif raw >= 0.7:
            reason = f"Key: {current.key} → {candidate.key} (compatible)"
        elif raw > 0:
            reason = f"Key: {current.key} → {candidate.key} (tension)"
        else:
            reason = f"Key: {current.key} → {candidate.key} (clash)"

        return FactorScore(
            name=self.name,
            score=raw,
            weight=self.weight,
            weighted_score=raw * self.weight,
            reason=reason,
        )


class GrooveCompatibilityFactor(ScoringFactor):
    """Score rhythm style transitions."""

    name = "Groove Compatibility"
    weight = 0.4

    # Groove transition scores
    GROOVE_MATRIX = {
        "four-on-floor": {"four-on-floor": 1.0, "linear": 0.7, "syncopated": 0.5, "swung": 0.4, "broken": 0.3},
        "broken": {"broken": 1.0, "syncopated": 0.8, "swung": 0.6, "linear": 0.4, "four-on-floor": 0.3},
        "swung": {"swung": 1.0, "broken": 0.7, "syncopated": 0.6, "four-on-floor": 0.4, "linear": 0.5},
        "syncopated": {"syncopated": 1.0, "broken": 0.8, "swung": 0.7, "linear": 0.5, "four-on-floor": 0.5},
        "linear": {"linear": 1.0, "four-on-floor": 0.8, "syncopated": 0.5, "swung": 0.4, "broken": 0.4},
    }

    def score(self, current: Track, candidate: Track, direction: Direction) -> FactorScore:
        from_groove = current.groove_style if isinstance(current.groove_style, str) else current.groove_style.value
        to_groove = candidate.groove_style if isinstance(candidate.groove_style, str) else candidate.groove_style.value

        raw = self.GROOVE_MATRIX.get(from_groove, {}).get(to_groove, 0.5)

        if from_groove == to_groove:
            reason = f"Same groove: {to_groove}"
        else:
            reason = f"Groove: {from_groove} → {to_groove}"

        return FactorScore(
            name=self.name,
            score=raw,
            weight=self.weight,
            weighted_score=raw * self.weight,
            reason=reason,
        )


class MixEaseFactor(ScoringFactor):
    """Score technical mixability."""

    name = "Mix Ease"
    weight = 0.4

    def score(self, current: Track, candidate: Track, direction: Direction) -> FactorScore:
        # Combine mix_out of current with mix_in of candidate
        mix_out = current.mix_out_ease
        mix_in = candidate.mix_in_ease

        # Average, weighted slightly toward mix_in (what you're going to)
        raw = (mix_out * 0.4 + mix_in * 0.6) / 10

        reason = f"Mix out: {mix_out}/10, Mix in: {mix_in}/10"

        return FactorScore(
            name=self.name,
            score=raw,
            weight=self.weight,
            weighted_score=raw * self.weight,
            reason=reason,
        )


class GenreAffinityFactor(ScoringFactor):
    """Score genre match."""

    name = "Genre Affinity"
    weight = 0.3

    def score(self, current: Track, candidate: Track, direction: Direction) -> FactorScore:
        # Same genre = high score
        # Same subgenre = bonus
        if current.genre.lower() == candidate.genre.lower():
            raw = 0.8
            if current.subgenre and candidate.subgenre:
                if current.subgenre.lower() == candidate.subgenre.lower():
                    raw = 1.0
                    reason = f"Same subgenre: {candidate.subgenre}"
                else:
                    reason = f"Same genre, different subgenre"
            else:
                reason = f"Same genre: {candidate.genre}"
        else:
            raw = 0.3
            reason = f"Genre: {current.genre} → {candidate.genre}"

        return FactorScore(
            name=self.name,
            score=raw,
            weight=self.weight,
            weighted_score=raw * self.weight,
            reason=reason,
        )


# Default factor set
DEFAULT_FACTORS = [
    EnergyTrajectoryFactor(),
    DanceabilityFactor(),
    VibeCompatibilityFactor(),
    NarrativeFlowFactor(),
    KeyQualityFactor(),
    GrooveCompatibilityFactor(),
    MixEaseFactor(),
    GenreAffinityFactor(),
]
