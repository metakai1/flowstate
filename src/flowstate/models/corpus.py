"""Corpus storage and management."""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from .track import Track


class CorpusStats(BaseModel):
    """Statistics about the corpus."""

    total_tracks: int = 0

    # BPM distribution
    bpm_min: Optional[float] = None
    bpm_max: Optional[float] = None
    bpm_avg: Optional[float] = None

    # Energy distribution
    energy_distribution: dict[int, int] = Field(default_factory=dict)

    # Vibe distribution
    vibe_distribution: dict[str, int] = Field(default_factory=dict)

    # Intensity distribution
    intensity_distribution: dict[str, int] = Field(default_factory=dict)

    # Key distribution
    key_distribution: dict[str, int] = Field(default_factory=dict)

    # Genre distribution
    genre_distribution: dict[str, int] = Field(default_factory=dict)

    # Quality stats
    avg_production_quality: Optional[float] = None
    avg_audio_fidelity: Optional[float] = None
    low_fidelity_count: int = 0  # Tracks with fidelity < 6

    # Vocal stats
    vocal_distribution: dict[str, int] = Field(default_factory=dict)


class Corpus(BaseModel):
    """Track corpus with indexing and search."""

    tracks: list[Track] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Indexes (built on load) - private attributes
    _by_id: dict[str, Track] = PrivateAttr(default_factory=dict)
    _by_path: dict[str, Track] = PrivateAttr(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def model_post_init(self, __context) -> None:
        """Build indexes after loading."""
        self._rebuild_indexes()

    def _rebuild_indexes(self) -> None:
        """Rebuild lookup indexes."""
        self._by_id = {t.track_id: t for t in self.tracks}
        self._by_path = {str(t.file_path): t for t in self.tracks}

    def add(self, track: Track) -> None:
        """Add a track to the corpus."""
        # Update if exists, otherwise add
        if track.track_id in self._by_id:
            self.tracks = [t if t.track_id != track.track_id else track for t in self.tracks]
        else:
            self.tracks.append(track)
        self._rebuild_indexes()
        self.updated_at = datetime.now()

    def get_by_id(self, track_id: str) -> Optional[Track]:
        """Get track by ID."""
        return self._by_id.get(track_id)

    def get_by_path(self, file_path: str | Path) -> Optional[Track]:
        """Get track by file path."""
        return self._by_path.get(str(file_path))

    def search(
        self,
        query: str,
        bpm_range: Optional[tuple[float, float]] = None,
        keys: Optional[list[str]] = None,
        vibes: Optional[list[str]] = None,
        min_energy: Optional[int] = None,
        max_energy: Optional[int] = None,
        min_rating: Optional[int] = None,
        min_fidelity: Optional[int] = None,
    ) -> list[Track]:
        """Search tracks with filters."""
        query_lower = query.lower()
        results = []

        for track in self.tracks:
            # Text search
            if query:
                if not (
                    query_lower in track.title.lower() or
                    query_lower in track.artist.lower() or
                    query_lower in track.genre.lower() or
                    query_lower in track.description.lower()
                ):
                    continue

            # BPM filter
            if bpm_range and not (bpm_range[0] <= track.bpm <= bpm_range[1]):
                continue

            # Key filter
            if keys and track.key not in keys:
                continue

            # Vibe filter
            if vibes and track.vibe not in vibes:
                continue

            # Energy filter
            if min_energy and track.energy < min_energy:
                continue
            if max_energy and track.energy > max_energy:
                continue

            # Rating filter
            if min_rating and (track.rating is None or track.rating < min_rating):
                continue

            # Fidelity filter
            if min_fidelity and track.audio_fidelity < min_fidelity:
                continue

            results.append(track)

        return results

    def stats(self) -> CorpusStats:
        """Compute corpus statistics."""
        if not self.tracks:
            return CorpusStats()

        bpms = [t.bpm for t in self.tracks]
        energies = [t.energy for t in self.tracks]
        prod_qualities = [t.production_quality for t in self.tracks]
        fidelities = [t.audio_fidelity for t in self.tracks]

        return CorpusStats(
            total_tracks=len(self.tracks),
            bpm_min=min(bpms),
            bpm_max=max(bpms),
            bpm_avg=sum(bpms) / len(bpms),
            energy_distribution=dict(Counter(energies)),
            vibe_distribution=dict(Counter(t.vibe for t in self.tracks)),
            intensity_distribution=dict(Counter(t.intensity for t in self.tracks)),
            key_distribution=dict(Counter(t.key for t in self.tracks)),
            genre_distribution=dict(Counter(t.genre for t in self.tracks)),
            avg_production_quality=sum(prod_qualities) / len(prod_qualities),
            avg_audio_fidelity=sum(fidelities) / len(fidelities),
            low_fidelity_count=sum(1 for f in fidelities if f < 6),
            vocal_distribution=dict(Counter(t.vocal_presence for t in self.tracks)),
        )

    def save(self, path: str | Path) -> None:
        """Save corpus to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = self.model_dump(mode="json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    @classmethod
    def load(cls, path: str | Path) -> "Corpus":
        """Load corpus from JSON file."""
        path = Path(path)
        if not path.exists():
            return cls()

        with open(path) as f:
            data = json.load(f)

        return cls(**data)
