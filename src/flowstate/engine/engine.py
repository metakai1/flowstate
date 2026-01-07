"""Recommendation engine - 4-stage scoring pipeline."""

from dataclasses import dataclass, field
from typing import Optional

from ..models import Corpus, Direction, Recommendations, ScoredTrack, Track
from .camelot import get_compatible_keys
from .factors import DEFAULT_FACTORS, ScoringFactor


@dataclass
class ScoringConfig:
    """Configuration for the recommendation engine."""

    # Hard filter settings
    bpm_range: float = 6.0
    allow_key_clash: bool = False

    # Direction settings
    up_min_delta: int = 1
    up_max_delta: int = 3
    hold_max_delta: int = 1
    down_min_delta: int = 1
    down_max_delta: int = 3

    # Output settings
    top_n: int = 5

    # Scoring factors (can be customized)
    factors: list[ScoringFactor] = field(default_factory=lambda: DEFAULT_FACTORS.copy())

    # Quality filters
    min_audio_fidelity: int = 0  # Set to 6 to filter out bad rips


class RecommendationEngine:
    """
    4-stage recommendation pipeline:
    1. Hard filters (BPM, key, not recently played)
    2. Direction split (UP/HOLD/DOWN based on energy)
    3. Soft scoring (weighted factors)
    4. Rank and return top N
    """

    def __init__(self, corpus: Corpus, config: Optional[ScoringConfig] = None):
        self.corpus = corpus
        self.config = config or ScoringConfig()
        self.recently_played: list[str] = []
        self.max_history = 20

    def add_to_history(self, track_id: str) -> None:
        """Add track to recently played history."""
        if track_id in self.recently_played:
            self.recently_played.remove(track_id)
        self.recently_played.insert(0, track_id)
        self.recently_played = self.recently_played[:self.max_history]

    def recommend(self, current: Track) -> Recommendations:
        """Generate recommendations for all directions."""

        # Add current to history
        self.add_to_history(current.track_id)

        # Stage 1: Hard filters
        candidates = self._hard_filter(current)

        # Stage 2: Split by direction
        up_candidates = []
        hold_candidates = []
        down_candidates = []

        for candidate in candidates:
            delta = candidate.energy - current.energy

            if delta >= self.config.up_min_delta:
                up_candidates.append(candidate)
            if abs(delta) <= self.config.hold_max_delta:
                hold_candidates.append(candidate)
            if delta <= -self.config.down_min_delta:
                down_candidates.append(candidate)

        # Stage 3 & 4: Score and rank each direction
        up_scored = self._score_and_rank(current, up_candidates, Direction.UP)
        hold_scored = self._score_and_rank(current, hold_candidates, Direction.HOLD)
        down_scored = self._score_and_rank(current, down_candidates, Direction.DOWN)

        return Recommendations(
            current_track=current,
            up=up_scored[:self.config.top_n],
            hold=hold_scored[:self.config.top_n],
            down=down_scored[:self.config.top_n],
            candidates_considered=len(self.corpus.tracks),
            filtered_count=len(candidates),
            recently_played=self.recently_played.copy(),
        )

    def _hard_filter(self, current: Track) -> list[Track]:
        """Stage 1: Apply hard filters."""
        candidates = []

        # Get compatible keys
        compatible_keys = get_compatible_keys(current.key, extended=True)
        if self.config.allow_key_clash:
            compatible_keys = None  # Allow all keys

        for track in self.corpus.tracks:
            # Skip same track
            if track.track_id == current.track_id:
                continue

            # Skip recently played
            if track.track_id in self.recently_played:
                continue

            # BPM filter (within range)
            bpm_diff = abs(track.bpm - current.bpm)
            if bpm_diff > self.config.bpm_range:
                continue

            # Key filter (must be compatible)
            if compatible_keys and track.key not in compatible_keys:
                continue

            # Quality filter
            if track.audio_fidelity < self.config.min_audio_fidelity:
                continue

            candidates.append(track)

        return candidates

    def _score_and_rank(
        self,
        current: Track,
        candidates: list[Track],
        direction: Direction,
    ) -> list[ScoredTrack]:
        """Stage 3 & 4: Score candidates and rank by total score."""
        scored = []

        for candidate in candidates:
            factor_scores = []
            total_weighted = 0.0
            total_weight = 0.0

            for factor in self.config.factors:
                fs = factor.score(current, candidate, direction)
                factor_scores.append(fs)
                total_weighted += fs.weighted_score
                total_weight += fs.weight

            # Normalize to 0-1
            total_score = total_weighted / total_weight if total_weight > 0 else 0

            scored.append(ScoredTrack(
                track=candidate,
                direction=direction,
                total_score=total_score,
                factor_scores=factor_scores,
            ))

        # Sort by score descending
        scored.sort(key=lambda x: x.total_score, reverse=True)

        return scored

    def set_factor_weight(self, factor_name: str, weight: float) -> None:
        """Adjust a factor's weight at runtime."""
        for factor in self.config.factors:
            if factor.name == factor_name:
                factor.weight = weight
                return
        raise ValueError(f"Unknown factor: {factor_name}")

    def get_factor_weights(self) -> dict[str, float]:
        """Get current factor weights."""
        return {f.name: f.weight for f in self.config.factors}
