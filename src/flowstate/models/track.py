"""Track data model with expanded AI-extracted fields."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class Vibe(str, Enum):
    """Track vibe/mood classification."""
    DARK = "dark"
    BRIGHT = "bright"
    HYPNOTIC = "hypnotic"
    EUPHORIC = "euphoric"
    CHILL = "chill"
    AGGRESSIVE = "aggressive"


class Intensity(str, Enum):
    """Track intensity - where it fits in a set."""
    OPENER = "opener"
    JOURNEY = "journey"
    PEAK = "peak"
    CLOSER = "closer"


class GrooveStyle(str, Enum):
    """Rhythmic style classification."""
    FOUR_ON_FLOOR = "four-on-floor"
    BROKEN = "broken"
    SWUNG = "swung"
    SYNCOPATED = "syncopated"
    LINEAR = "linear"


class VocalPresence(str, Enum):
    """Type of vocals in the track."""
    INSTRUMENTAL = "instrumental"
    MALE = "male"
    FEMALE = "female"
    MIXED = "mixed"
    GROUP = "group"


class VocalStyle(str, Enum):
    """Style of vocal delivery."""
    RAP = "rap"
    SINGING = "singing"
    BOTH = "both"
    CHANT = "chant"
    NONE = "none"


class TempoFeel(str, Enum):
    """Perceived tempo relative to BPM."""
    STRAIGHT = "straight"
    DOUBLE_TIME = "double-time"
    HALF_TIME = "half-time"


class Track(BaseModel):
    """Complete track model with AI-extracted metadata."""

    # === Identity ===
    track_id: str = Field(description="Unique identifier (SHA256 hash)")
    title: str
    artist: str
    file_path: Path
    rekordbox_id: Optional[str] = None

    # === Core Audio (from file metadata + AI) ===
    bpm: float = Field(ge=60, le=200)
    key: str = Field(description="Camelot notation (1A-12B)")
    duration_seconds: float

    # === Energy System (AI) ===
    energy: int = Field(ge=1, le=10, description="Overall intensity level")
    danceability: int = Field(ge=1, le=10, description="How much it invites movement")

    # === Vibe & Narrative (AI) ===
    vibe: Vibe
    intensity: Intensity = Field(description="Where it fits in a set")
    mood_tags: list[str] = Field(default_factory=list, description="Free-form mood tags")

    # === Rhythm (AI) ===
    groove_style: GrooveStyle
    tempo_feel: TempoFeel = Field(default=TempoFeel.STRAIGHT)

    # === Mixability (AI) ===
    mix_in_ease: int = Field(ge=1, le=10, description="How easy to mix into")
    mix_out_ease: int = Field(ge=1, le=10, description="How easy to mix out of")
    mixability_notes: Optional[str] = Field(default=None, description="DJ tips for mixing")

    # === Vocals (AI) ===
    vocal_presence: VocalPresence = Field(default=VocalPresence.INSTRUMENTAL)
    vocal_style: VocalStyle = Field(default=VocalStyle.NONE)
    language: Optional[str] = Field(default=None, description="Primary language (korean/english/mixed)")

    # === Structure (AI) ===
    structure: list[str] = Field(
        default_factory=list,
        description="Track sections: intro, verse, chorus, drop, breakdown, outro, etc."
    )
    drop_intensity: Optional[int] = Field(
        default=None, ge=1, le=10,
        description="Intensity of the main drop/chorus"
    )

    # === Production (AI) ===
    instrumentation: list[str] = Field(
        default_factory=list,
        description="Prominent instruments/sounds: synth, brass, strings, etc."
    )
    production_style: Optional[str] = Field(
        default=None,
        description="Production character: clean, distorted, filtered, lo-fi, etc."
    )

    # === Quality Assessment (AI) ===
    production_quality: int = Field(
        ge=1, le=10,
        description="Mix clarity, mastering, professional sound"
    )
    audio_fidelity: int = Field(
        ge=1, le=10,
        description="File quality - artifacts, clipping, encoding issues"
    )

    # === Genre (AI) ===
    genre: str
    subgenre: Optional[str] = None
    similar_artists: list[str] = Field(default_factory=list)

    # === Description (AI) ===
    description: str = Field(description="Concise artistic description (1-2 sentences)")

    # === User Overrides ===
    rating: Optional[int] = Field(
        default=None, ge=1, le=5,
        description="Personal rating (user-set, overrides AI assessment)"
    )
    notes: Optional[str] = Field(default=None, description="Personal notes")

    # === Computed (set after load) ===
    compatible_keys: list[str] = Field(default_factory=list)

    # === Timestamps ===
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


class AudioFile(BaseModel):
    """Scanned audio file before AI analysis."""

    file_path: Path
    file_hash: str = Field(description="SHA256 of first 1MB")

    # From file metadata (Mutagen)
    title: Optional[str] = None
    artist: Optional[str] = None
    bpm: Optional[float] = None
    key: Optional[str] = None
    duration_seconds: float
    format: str = Field(description="File extension: mp3, opus, flac, etc.")
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None

    # From Rekordbox (if matched)
    rekordbox_id: Optional[str] = None
    rekordbox_bpm: Optional[float] = None
    rekordbox_key: Optional[str] = None
