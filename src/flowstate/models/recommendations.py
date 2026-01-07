"""Recommendation data models."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .track import Track


class Direction(str, Enum):
    """Energy direction for recommendations."""
    UP = "up"
    HOLD = "hold"
    DOWN = "down"


class FactorScore(BaseModel):
    """Individual scoring factor result."""

    name: str
    score: float = Field(ge=0, le=1)
    weight: float
    weighted_score: float
    reason: Optional[str] = None


class ScoredTrack(BaseModel):
    """Track with recommendation scores."""

    track: Track
    direction: Direction
    total_score: float = Field(ge=0, le=1)
    factor_scores: list[FactorScore] = Field(default_factory=list)

    def explain(self) -> str:
        """Return human-readable explanation of the score."""
        lines = [
            f"{self.track.title} - {self.track.artist}",
            f"Direction: {self.direction.value.upper()} | Score: {self.total_score:.2f}",
            "",
            "Factor Breakdown:",
        ]

        for fs in sorted(self.factor_scores, key=lambda x: -x.weighted_score):
            lines.append(
                f"  {fs.name}: {fs.score:.2f} × {fs.weight:.1f} = {fs.weighted_score:.2f}"
            )
            if fs.reason:
                lines.append(f"    └─ {fs.reason}")

        return "\n".join(lines)


class Recommendations(BaseModel):
    """Complete recommendation set for all directions."""

    current_track: Track
    up: list[ScoredTrack] = Field(default_factory=list)
    hold: list[ScoredTrack] = Field(default_factory=list)
    down: list[ScoredTrack] = Field(default_factory=list)

    # Metadata
    candidates_considered: int = 0
    filtered_count: int = 0
    recently_played: list[str] = Field(default_factory=list)

    def get_direction(self, direction: Direction) -> list[ScoredTrack]:
        """Get recommendations for a specific direction."""
        return {
            Direction.UP: self.up,
            Direction.HOLD: self.hold,
            Direction.DOWN: self.down,
        }[direction]

    def top(self, direction: Direction, n: int = 1) -> list[ScoredTrack]:
        """Get top N recommendations for a direction."""
        return self.get_direction(direction)[:n]

    def all_recommendations(self) -> list[ScoredTrack]:
        """Get all recommendations across all directions."""
        return self.up + self.hold + self.down
