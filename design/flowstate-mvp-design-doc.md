# FLOWSTATE MVP
## Design Document

**Version:** 1.0  
**Author:** Kai  
**Target:** Gig-ready in 20 days  
**Codename:** FLOWSTATE

---

## Table of Contents

1. [Overview](#1-overview)
2. [Goals & Non-Goals](#2-goals--non-goals)
3. [System Architecture](#3-system-architecture)
4. [Data Models](#4-data-models)
5. [Component Design](#5-component-design)
6. [Gemini Analysis Pipeline](#6-gemini-analysis-pipeline)
7. [Recommendation Engine](#7-recommendation-engine)
8. [Rekordbox Integration](#8-rekordbox-integration)
9. [User Interface](#9-user-interface)
10. [Configuration](#10-configuration)
11. [File Structure](#11-file-structure)
12. [Implementation Plan](#12-implementation-plan)
13. [Risk Mitigation](#13-risk-mitigation)
14. [Future Enhancements](#14-future-enhancements)

---

## 1. Overview

### 1.1 Problem Statement

DJs face decision fatigue during live sets. With hundreds of tracks available, choosing the next track that maintains energy flow, harmonic compatibility, and narrative coherence is cognitively demanding—especially while managing the current mix, reading the crowd, and handling equipment.

### 1.2 Solution

FLOWSTATE is a DJ decision support system that:

1. **Analyzes** your music library using AI to extract musical and narrative metadata
2. **Monitors** what's currently playing via Rekordbox
3. **Recommends** the next track based on three directions: UP (increase energy), HOLD (maintain), DOWN (decrease energy)
4. **Scores** recommendations using tunable, weighted factors

### 1.3 Core Philosophy

```
The DJ is the artist. The system illuminates options.
```

- Show paths, not picks
- Energy + Key + Vibe = 80% of the value
- Simple enough to trust at 1am
- Tunable enough to match your style

### 1.4 Success Criteria

| Metric | Target |
|--------|--------|
| Corpus size at gig | 100+ analyzed tracks |
| Recommendation latency | < 2 seconds |
| False positive rate | < 20% (bad recommendations) |
| Gig readiness | Day 18 (2-day buffer) |

---

## 2. Goals & Non-Goals

### 2.1 Goals (Must Have)

| Goal | Description |
|------|-------------|
| **G1: Corpus Builder** | Analyze 100+ tracks with Gemini, store as JSON |
| **G2: Track Matching** | Match playing track to corpus via Rekordbox DB |
| **G3: Recommendations** | Show UP/HOLD/DOWN directions with 5 tracks each |
| **G4: Scoring Engine** | Weighted scoring with energy, key, vibe factors |
| **G5: Basic UI** | Terminal or web interface showing recommendations |
| **G6: Gig Ready** | Tested with 2+ practice sets before gig |

### 2.2 Non-Goals (Explicitly Out of Scope)

| Non-Goal | Rationale |
|----------|-----------|
| Pro DJ Link integration | Complex, Rekordbox DB polling is sufficient |
| Fine-tuning local model | ROI not there for 100 tracks |
| Gemini deep analysis | Nice to have, not need to have |
| Full review TUI | Spreadsheet validation is sufficient |
| 6 narrative directions | 3 directions (UP/HOLD/DOWN) is enough |
| Mobile app | Desktop/tablet web is sufficient |
| Multi-user support | Single DJ system |
| Cloud deployment | Local only |

### 2.3 Stretch Goals (If Time Permits)

| Stretch | Days Required |
|---------|---------------|
| Set history tracking | 0.5 |
| Search/filter corpus | 0.5 |
| Export set to playlist | 1 |
| Real-time Rekordbox (Pro DJ Link) | 2+ |

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FLOWSTATE MVP                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                         ┌─────────────────────┐                             │
│                         │     USER INTERFACE  │                             │
│                         │  (Terminal or Web)  │                             │
│                         └──────────┬──────────┘                             │
│                                    │                                         │
│                                    ▼                                         │
│                         ┌─────────────────────┐                             │
│                         │   SESSION MANAGER   │                             │
│                         │                     │                             │
│                         │ • Coordinates flow  │                             │
│                         │ • Tracks set history│                             │
│                         │ • Manages state     │                             │
│                         └──────────┬──────────┘                             │
│                                    │                                         │
│              ┌─────────────────────┼─────────────────────┐                  │
│              │                     │                     │                  │
│              ▼                     ▼                     ▼                  │
│   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐          │
│   │    REKORDBOX    │   │  RECOMMENDATION │   │     CORPUS      │          │
│   │    MONITOR      │   │     ENGINE      │   │     STORE       │          │
│   │                 │   │                 │   │                 │          │
│   │ • Poll history  │   │ • Hard filters  │   │ • Load/save     │          │
│   │ • Match corpus  │   │ • Soft scoring  │   │ • Search        │          │
│   │ • Track changes │   │ • Direction map │   │ • Statistics    │          │
│   └────────┬────────┘   └────────┬────────┘   └────────┬────────┘          │
│            │                     │                     │                    │
│            └─────────────────────┴─────────────────────┘                    │
│                                  │                                          │
│                                  ▼                                          │
│                         ┌─────────────────────┐                             │
│                         │   CORPUS (JSON)     │                             │
│                         │                     │                             │
│                         │ • 100+ tracks       │                             │
│                         │ • Full metadata     │                             │
│                         └─────────────────────┘                             │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                          OFFLINE PIPELINE                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                   │
│   │   AUDIO     │     │   GEMINI    │     │    RAW      │                   │
│   │   SCANNER   │────▶│   ANALYZER  │────▶│  ANALYSES   │                   │
│   │             │     │             │     │             │                   │
│   │ • Find MP3s │     │ • Send API  │     │ • JSON file │                   │
│   │ • Read tags │     │ • Parse     │     │ • Validate  │                   │
│   │ • Match RB  │     │ • Retry     │     │ • Merge     │                   │
│   └─────────────┘     └─────────────┘     └─────────────┘                   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow

```
OFFLINE (Corpus Building):
Audio Files → Scanner → Gemini API → Raw JSON → Validation → Corpus

ONLINE (Live Performance):
Rekordbox DB → Monitor → Match to Corpus → Engine → Recommendations → UI
     ↑                                                      │
     └──────────────── DJ loads track ◄─────────────────────┘
```

### 3.3 Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.11+ |
| AI | Google Generative AI (Gemini 2.5 Pro) | Latest |
| Audio Metadata | Mutagen | 1.47+ |
| Data Validation | Pydantic | 2.0+ |
| Terminal UI | Rich | 13.0+ |
| Web UI (optional) | Flask + HTMX | 3.0+ |
| Database | SQLite (Rekordbox) | Built-in |
| Config | YAML + Pydantic Settings | - |

### 3.4 Dependencies

```toml
[project]
name = "flowstate"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "google-generativeai>=0.3",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "mutagen>=1.47",
    "rich>=13.0",
    "pyyaml>=6.0",
    "click>=8.0",
]

[project.optional-dependencies]
web = [
    "flask>=3.0",
]
dev = [
    "pytest>=7.0",
    "ruff>=0.1",
]
```

---

## 4. Data Models

### 4.1 Core Track Model

```python
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class EnergyDirection(str, Enum):
    """How the track's energy evolves over time"""
    BUILDING = "building"      # Ramps up
    PEAK = "peak"              # Stays at max
    SUSTAINING = "sustaining"  # Maintains level
    RELEASING = "releasing"    # Winds down


class Vibe(str, Enum):
    """The emotional/sonic character of the track"""
    DARK = "dark"              # Minor, tense, underground
    BRIGHT = "bright"          # Major, uplifting, poppy
    HYPNOTIC = "hypnotic"      # Repetitive, trancey, locked-in
    EUPHORIC = "euphoric"      # Big, emotional, hands-up
    CHILL = "chill"            # Relaxed, groovy, laid-back
    AGGRESSIVE = "aggressive"  # Hard, intense, confrontational


class Intensity(str, Enum):
    """Where the track fits in a set's narrative arc"""
    OPENER = "opener"          # Low commitment, warming up
    JOURNEY = "journey"        # Building, exploring
    PEAK = "peak"              # Maximum impact moment
    CLOSER = "closer"          # Winding down, memorable exit


class Track(BaseModel):
    """
    Core track model with all fields needed for recommendations.
    
    This is intentionally minimal compared to the full spec—
    we only extract what the scoring engine actually uses.
    """
    
    # ══════════════════════════════════════════════════════════
    # IDENTITY
    # ══════════════════════════════════════════════════════════
    
    track_id: str = Field(
        description="Unique identifier (artist-title-hash)"
    )
    title: str
    artist: str
    file_path: Optional[str] = Field(
        default=None,
        description="Absolute path to audio file"
    )
    
    # ══════════════════════════════════════════════════════════
    # HARD FILTER FIELDS
    # These are used for binary pass/fail filtering
    # ══════════════════════════════════════════════════════════
    
    bpm: float = Field(
        description="Beats per minute"
    )
    key: str = Field(
        description="Camelot notation (e.g., 8A, 11B)"
    )
    compatible_keys: list[str] = Field(
        default_factory=list,
        description="Pre-computed compatible keys from Camelot wheel"
    )
    
    # ══════════════════════════════════════════════════════════
    # ENERGY SYSTEM
    # Primary scoring factor
    # ══════════════════════════════════════════════════════════
    
    energy: int = Field(
        ge=1, le=10,
        description="Overall energy level 1-10"
    )
    energy_direction: EnergyDirection = Field(
        description="How energy evolves during the track"
    )
    
    # ══════════════════════════════════════════════════════════
    # DANCEABILITY SYSTEM
    # How much the track invites body movement
    # Distinct from energy: a track can be high energy but
    # awkward to dance to, or low energy but incredibly groovy
    # ══════════════════════════════════════════════════════════
    
    danceability: int = Field(
        ge=1, le=10,
        description="""
        How much the track invites body movement:
        1-3 = Difficult (complex, arrhythmic, cerebral)
        4-5 = Requires effort (broken beats, odd patterns)
        6-7 = Solid groove (most club tracks)
        8-9 = Infectious (head-nodding inevitable)
        10 = Undeniable (impossible not to move)
        """
    )
    groove_style: Optional[str] = Field(
        default=None,
        description="Rhythmic character: 'four-on-floor', 'broken', 'swung', 'syncopated', 'linear'"
    )
    
    # ══════════════════════════════════════════════════════════
    # NARRATIVE SYSTEM
    # Secondary scoring factors
    # ══════════════════════════════════════════════════════════
    
    vibe: Vibe = Field(
        description="Emotional/sonic character"
    )
    intensity: Intensity = Field(
        description="Set position fit"
    )
    mood_tags: list[str] = Field(
        default_factory=list,
        description="Descriptive tags like 'dreamy', 'driving', 'vocal'"
    )
    
    # ══════════════════════════════════════════════════════════
    # MIXABILITY
    # Tertiary scoring factors
    # ══════════════════════════════════════════════════════════
    
    mix_in_ease: int = Field(
        default=5, ge=1, le=10,
        description="How easy to mix into this track"
    )
    mix_out_ease: int = Field(
        default=5, ge=1, le=10,
        description="How easy to mix out of this track"
    )
    
    # ══════════════════════════════════════════════════════════
    # METADATA
    # For display and filtering
    # ══════════════════════════════════════════════════════════
    
    genre: str = Field(
        default="",
        description="Primary genre"
    )
    subgenre: Optional[str] = Field(
        default=None,
        description="Subgenre if applicable"
    )
    duration_seconds: Optional[float] = Field(
        default=None,
        description="Track duration"
    )
    
    # ══════════════════════════════════════════════════════════
    # REKORDBOX INTEGRATION
    # For matching to currently playing track
    # ══════════════════════════════════════════════════════════
    
    rekordbox_id: Optional[int] = Field(
        default=None,
        description="ID from Rekordbox database"
    )
    
    # ══════════════════════════════════════════════════════════
    # INTERNAL
    # ══════════════════════════════════════════════════════════
    
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __hash__(self):
        return hash(self.track_id)
    
    def __eq__(self, other):
        if isinstance(other, Track):
            return self.track_id == other.track_id
        return False
```

### 4.2 Recommendation Models

```python
from dataclasses import dataclass, field
from enum import Enum


class Direction(str, Enum):
    """The three recommendation directions"""
    UP = "up"       # Increase energy
    HOLD = "hold"   # Maintain energy
    DOWN = "down"   # Decrease energy


@dataclass
class ScoredTrack:
    """A track with its recommendation score"""
    
    track: Track
    direction: Direction
    total_score: float
    factor_scores: dict[str, float] = field(default_factory=dict)
    
    def __repr__(self):
        return f"{self.track.title} ({self.direction.value}: {self.total_score:.2f})"


@dataclass
class Recommendations:
    """Complete recommendation set from current track"""
    
    current_track: Track
    up: list[ScoredTrack]
    hold: list[ScoredTrack]
    down: list[ScoredTrack]
    
    def get(self, direction: Direction) -> list[ScoredTrack]:
        return {
            Direction.UP: self.up,
            Direction.HOLD: self.hold,
            Direction.DOWN: self.down,
        }[direction]
```

### 4.3 Corpus Model

```python
@dataclass
class CorpusStats:
    """Statistics about the corpus"""
    
    total_tracks: int
    genre_distribution: dict[str, int]
    energy_distribution: dict[int, int]
    bpm_range: tuple[float, float]
    key_distribution: dict[str, int]
    vibe_distribution: dict[str, int]
    
    def summary(self) -> str:
        return f"""
Corpus: {self.total_tracks} tracks
BPM: {self.bpm_range[0]:.0f} - {self.bpm_range[1]:.0f}
Top genres: {', '.join(list(self.genre_distribution.keys())[:3])}
Energy spread: {min(self.energy_distribution.keys())}-{max(self.energy_distribution.keys())}
"""


class Corpus:
    """The analyzed track library"""
    
    def __init__(self, tracks: list[Track] = None):
        self.tracks = tracks or []
        self._by_id: dict[str, Track] = {}
        self._by_path: dict[str, Track] = {}
        self._rebuild_indexes()
    
    def _rebuild_indexes(self):
        self._by_id = {t.track_id: t for t in self.tracks}
        self._by_path = {t.file_path: t for t in self.tracks if t.file_path}
    
    def add(self, track: Track):
        if track.track_id in self._by_id:
            self.tracks.remove(self._by_id[track.track_id])
        self.tracks.append(track)
        self._rebuild_indexes()
    
    def get_by_id(self, track_id: str) -> Optional[Track]:
        return self._by_id.get(track_id)
    
    def get_by_path(self, path: str) -> Optional[Track]:
        return self._by_path.get(path)
    
    def search(self, query: str) -> list[Track]:
        query = query.lower()
        return [
            t for t in self.tracks
            if query in t.title.lower() or query in t.artist.lower()
        ]
    
    def stats(self) -> CorpusStats:
        from collections import Counter
        
        genres = Counter(t.genre for t in self.tracks)
        energies = Counter(t.energy for t in self.tracks)
        keys = Counter(t.key for t in self.tracks)
        vibes = Counter(t.vibe.value for t in self.tracks)
        bpms = [t.bpm for t in self.tracks]
        
        return CorpusStats(
            total_tracks=len(self.tracks),
            genre_distribution=dict(genres.most_common()),
            energy_distribution=dict(sorted(energies.items())),
            bpm_range=(min(bpms), max(bpms)) if bpms else (0, 0),
            key_distribution=dict(keys.most_common()),
            vibe_distribution=dict(vibes.most_common()),
        )
    
    def save(self, path: str):
        import json
        data = {
            "version": "1.0",
            "tracks": [t.model_dump() for t in self.tracks],
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    @classmethod
    def load(cls, path: str) -> 'Corpus':
        import json
        with open(path) as f:
            data = json.load(f)
        tracks = [Track(**t) for t in data['tracks']]
        return cls(tracks)
```

### 4.4 Camelot Wheel Reference

```python
# Camelot wheel for harmonic mixing
# Each key maps to: [same key, energy boost/drop, -1 on wheel, +1 on wheel]

CAMELOT_WHEEL: dict[str, list[str]] = {
    "1A":  ["1A",  "1B",  "12A", "2A"],
    "1B":  ["1B",  "1A",  "12B", "2B"],
    "2A":  ["2A",  "2B",  "1A",  "3A"],
    "2B":  ["2B",  "2A",  "1B",  "3B"],
    "3A":  ["3A",  "3B",  "2A",  "4A"],
    "3B":  ["3B",  "3A",  "2B",  "4B"],
    "4A":  ["4A",  "4B",  "3A",  "5A"],
    "4B":  ["4B",  "4A",  "3B",  "5B"],
    "5A":  ["5A",  "5B",  "4A",  "6A"],
    "5B":  ["5B",  "5A",  "4B",  "6B"],
    "6A":  ["6A",  "6B",  "5A",  "7A"],
    "6B":  ["6B",  "6A",  "5B",  "7B"],
    "7A":  ["7A",  "7B",  "6A",  "8A"],
    "7B":  ["7B",  "7A",  "6B",  "8B"],
    "8A":  ["8A",  "8B",  "7A",  "9A"],
    "8B":  ["8B",  "8A",  "7B",  "9B"],
    "9A":  ["9A",  "9B",  "8A",  "10A"],
    "9B":  ["9B",  "9A",  "8B",  "10B"],
    "10A": ["10A", "10B", "9A",  "11A"],
    "10B": ["10B", "10A", "9B",  "11B"],
    "11A": ["11A", "11B", "10A", "12A"],
    "11B": ["11B", "11A", "10B", "12B"],
    "12A": ["12A", "12B", "11A", "1A"],
    "12B": ["12B", "12A", "11B", "1B"],
}


def get_compatible_keys(key: str, extended: bool = True) -> set[str]:
    """
    Get keys compatible for harmonic mixing.
    
    Args:
        key: Camelot key code (e.g., "8A")
        extended: If True, include 2-step compatible keys
    
    Returns:
        Set of compatible key codes
    """
    if key not in CAMELOT_WHEEL:
        return {key}
    
    compatible = set(CAMELOT_WHEEL[key])
    
    if extended:
        # Add 2-step compatibility (still mixable, just trickier)
        for adj_key in CAMELOT_WHEEL[key]:
            if adj_key in CAMELOT_WHEEL:
                compatible.update(CAMELOT_WHEEL[adj_key])
    
    return compatible
```

---

## 5. Component Design

### 5.1 Audio Scanner

Scans directories for audio files and extracts basic metadata.

```python
from pathlib import Path
from dataclasses import dataclass
from mutagen import File as MutagenFile
import hashlib


@dataclass
class AudioFile:
    """Discovered audio file with basic metadata"""
    path: Path
    filename: str
    file_hash: str
    format: str
    duration_seconds: float
    
    # Embedded metadata (if present)
    title: Optional[str]
    artist: Optional[str]
    album: Optional[str]
    genre: Optional[str]
    bpm: Optional[float]
    key: Optional[str]
    
    # Rekordbox metadata (if matched)
    rekordbox_id: Optional[int]


class AudioScanner:
    """Scan directories for audio files"""
    
    SUPPORTED_FORMATS = {'.mp3', '.wav', '.flac', '.m4a', '.aiff'}
    
    def __init__(self, rekordbox_db_path: Optional[Path] = None):
        self.rekordbox = RekordboxDB(rekordbox_db_path) if rekordbox_db_path else None
    
    def scan(self, directory: Path, recursive: bool = True) -> list[AudioFile]:
        """Scan directory for audio files"""
        
        pattern = '**/*' if recursive else '*'
        files = []
        
        for path in directory.glob(pattern):
            if path.suffix.lower() in self.SUPPORTED_FORMATS:
                try:
                    audio_file = self._process_file(path)
                    files.append(audio_file)
                except Exception as e:
                    print(f"Warning: Failed to process {path}: {e}")
        
        return files
    
    def _process_file(self, path: Path) -> AudioFile:
        """Extract metadata from audio file"""
        
        audio = MutagenFile(path)
        
        # Try to match to Rekordbox
        rb_data = None
        if self.rekordbox:
            rb_data = self.rekordbox.find_by_path(str(path))
        
        return AudioFile(
            path=path,
            filename=path.name,
            file_hash=self._compute_hash(path),
            format=path.suffix.lower()[1:],
            duration_seconds=audio.info.length if audio and audio.info else 0,
            title=self._get_tag(audio, 'title') or path.stem,
            artist=self._get_tag(audio, 'artist') or 'Unknown',
            album=self._get_tag(audio, 'album'),
            genre=self._get_tag(audio, 'genre'),
            bpm=rb_data['bpm'] if rb_data else self._parse_bpm(self._get_tag(audio, 'bpm')),
            key=rb_data['key'] if rb_data else self._get_tag(audio, 'key'),
            rekordbox_id=rb_data['id'] if rb_data else None,
        )
    
    def _compute_hash(self, path: Path) -> str:
        """Compute short hash for deduplication"""
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            # Only hash first 1MB for speed
            sha256.update(f.read(1024 * 1024))
        return sha256.hexdigest()[:12]
    
    def _get_tag(self, audio, tag_name: str) -> Optional[str]:
        """Extract tag from mutagen audio object"""
        if not audio or not audio.tags:
            return None
        
        # Handle different tag formats
        for key in [tag_name, tag_name.upper(), tag_name.title(), f'©{tag_name}']:
            if key in audio.tags:
                val = audio.tags[key]
                return str(val[0]) if isinstance(val, list) else str(val)
        return None
    
    def _parse_bpm(self, bpm_str: Optional[str]) -> Optional[float]:
        """Parse BPM from string"""
        if not bpm_str:
            return None
        try:
            return float(bpm_str.split()[0])
        except (ValueError, IndexError):
            return None
```

### 5.2 Gemini Analyzer

Analyzes audio files using Gemini 2.5 Pro.

```python
import google.generativeai as genai
import asyncio
import json
from datetime import datetime
import re


class GeminiAnalyzer:
    """Analyze tracks using Gemini 2.5 Pro"""
    
    def __init__(
        self,
        api_key: str,
        max_concurrent: int = 3,
        requests_per_minute: int = 50,
    ):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.rpm_limit = requests_per_minute
        self.last_request_time = 0
    
    async def analyze_batch(
        self,
        audio_files: list[AudioFile],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> list[Track]:
        """Analyze a batch of audio files"""
        
        results = []
        
        for i, audio_file in enumerate(audio_files):
            async with self.semaphore:
                # Rate limiting
                await self._rate_limit()
                
                try:
                    track = await self._analyze_single(audio_file)
                    results.append(track)
                except Exception as e:
                    print(f"Failed to analyze {audio_file.filename}: {e}")
                
                if progress_callback:
                    progress_callback(i + 1, len(audio_files))
        
        return results
    
    async def _analyze_single(self, audio_file: AudioFile) -> Track:
        """Analyze a single audio file"""
        
        # Upload audio
        uploaded = genai.upload_file(str(audio_file.path))
        
        # Build prompt with hints
        prompt = self._build_prompt(audio_file)
        
        # Generate analysis
        response = await self.model.generate_content_async([prompt, uploaded])
        
        # Parse response
        track = self._parse_response(response.text, audio_file)
        
        return track
    
    def _build_prompt(self, audio_file: AudioFile) -> str:
        """Build the analysis prompt"""
        
        hints = []
        if audio_file.title:
            hints.append(f"Title (from tags): {audio_file.title}")
        if audio_file.artist:
            hints.append(f"Artist (from tags): {audio_file.artist}")
        if audio_file.bpm:
            hints.append(f"BPM (from Rekordbox/tags): {audio_file.bpm}")
        if audio_file.key:
            hints.append(f"Key (from Rekordbox/tags): {audio_file.key}")
        
        hint_section = ""
        if hints:
            hint_section = f"""
## HINTS (verify against audio)
{chr(10).join('- ' + h for h in hints)}
"""
        
        return f"""{ANALYSIS_PROMPT}

{hint_section}

Analyze the audio and return ONLY valid JSON matching the schema.
No markdown, no explanation, just the JSON object.
"""
    
    def _parse_response(self, response: str, audio_file: AudioFile) -> Track:
        """Parse Gemini response into Track"""
        
        # Extract JSON
        response = response.strip()
        if response.startswith('```'):
            response = re.sub(r'^```json?\n?', '', response)
            response = re.sub(r'\n?```$', '', response)
        
        data = json.loads(response)
        
        # Generate track ID
        artist_slug = re.sub(r'[^a-z0-9]', '-', data['artist'].lower())[:20]
        title_slug = re.sub(r'[^a-z0-9]', '-', data['title'].lower())[:30]
        track_id = f"{artist_slug}-{title_slug}-{audio_file.file_hash[:6]}"
        
        # Compute compatible keys
        compatible = list(get_compatible_keys(data['key']))
        
        return Track(
            track_id=track_id,
            title=data['title'],
            artist=data['artist'],
            file_path=str(audio_file.path),
            bpm=data['bpm'],
            key=data['key'],
            compatible_keys=compatible,
            energy=data['energy'],
            energy_direction=EnergyDirection(data['energy_direction']),
            danceability=data['danceability'],
            groove_style=data.get('groove_style'),
            vibe=Vibe(data['vibe']),
            intensity=Intensity(data['intensity']),
            mood_tags=data.get('mood_tags', []),
            mix_in_ease=data.get('mix_in_ease', 5),
            mix_out_ease=data.get('mix_out_ease', 5),
            genre=data.get('genre', ''),
            subgenre=data.get('subgenre'),
            duration_seconds=audio_file.duration_seconds,
            rekordbox_id=audio_file.rekordbox_id,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
    
    async def _rate_limit(self):
        """Simple rate limiting"""
        import time
        
        min_interval = 60.0 / self.rpm_limit
        elapsed = time.time() - self.last_request_time
        
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)
        
        self.last_request_time = time.time()


# The analysis prompt
ANALYSIS_PROMPT = """You are a professional DJ and music analyst. Analyze this audio track and extract structured metadata for a DJ recommendation system.

Return a JSON object with these exact fields:

{
  "title": "string - track title",
  "artist": "string - artist name",
  "bpm": number - beats per minute (be precise),
  "key": "string - Camelot notation (e.g., 8A, 11B, 2A)",
  "energy": integer 1-10 - overall energy level where:
    1-2 = ambient/downtempo
    3-4 = chill/warm-up
    5-6 = steady groove
    7-8 = driving/building
    9-10 = peak/intense,
  "energy_direction": "building" | "peak" | "sustaining" | "releasing" - how energy evolves,
  "danceability": integer 1-10 - how much the track invites body movement where:
    1-3 = difficult to dance to (complex, arrhythmic, cerebral)
    4-5 = danceable but requires effort (broken beats, odd patterns)
    6-7 = solid groove (most club tracks)
    8-9 = infectious groove (head-nodding inevitable)
    10 = undeniable (impossible not to move),
  "groove_style": "four-on-floor" | "broken" | "swung" | "syncopated" | "linear" - rhythmic character,
  "vibe": "dark" | "bright" | "hypnotic" | "euphoric" | "chill" | "aggressive" - emotional character,
  "intensity": "opener" | "journey" | "peak" | "closer" - where it fits in a set,
  "mix_in_ease": integer 1-10 - how easy to mix into (clean intro = high),
  "mix_out_ease": integer 1-10 - how easy to mix out of (clean outro = high),
  "genre": "string - primary genre",
  "subgenre": "string or null - subgenre if applicable",
  "mood_tags": ["array", "of", "3-5", "descriptive", "tags"]
}

Key analysis guidelines:
- BPM: Count beats precisely. Common ranges: House 120-130, Techno 125-140, D&B 170-180
- Key: Use Camelot wheel notation (1A-12A for minor, 1B-12B for major)
- Energy: Consider bass weight, percussion intensity, synth layers, vocal energy
- Danceability: Consider groove strength, beat clarity, rhythm consistency, body-movement invitation
- Groove style: four-on-floor (house/techno), broken (breakbeat/DnB), swung (UK garage/shuffle), syncopated (funk/disco), linear (minimal/industrial)
- Vibe: Dark = minor/tense, Bright = major/uplifting, Hypnotic = repetitive/trancey
- Mix ease: Clean intros/outros with just beats = high, complex arrangements = lower

Return ONLY the JSON object, no other text."""
```

### 5.3 Recommendation Engine

The core recommendation logic with pluggable scoring factors.

```python
from typing import Protocol
from dataclasses import dataclass


@dataclass
class ScoringConfig:
    """Tunable configuration for scoring"""
    
    # Hard filters
    bpm_range: float = 6.0
    allow_key_clash: bool = False
    
    # Scoring weights (0.0 = disabled, 1.0 = full weight)
    weight_energy_trajectory: float = 1.0
    weight_danceability: float = 0.8
    weight_vibe_compatibility: float = 0.7
    weight_narrative_flow: float = 0.6
    weight_key_quality: float = 0.5
    weight_groove_compatibility: float = 0.4
    weight_mix_ease: float = 0.4
    weight_genre_affinity: float = 0.3
    
    # Direction tuning
    up_min_energy_delta: int = 1
    up_max_energy_delta: int = 3
    hold_max_energy_delta: int = 1
    down_min_energy_delta: int = 1
    down_max_energy_delta: int = 3


class ScoringFactor(Protocol):
    """Interface for pluggable scoring factors"""
    name: str
    
    def score(
        self,
        current: Track,
        candidate: Track,
        direction: Direction,
        config: ScoringConfig,
    ) -> float:
        """Return score from 0.0 to 1.0"""
        ...


class EnergyTrajectoryFactor:
    """Score based on energy delta matching direction"""
    name = "energy_trajectory"
    
    def score(self, current: Track, candidate: Track, direction: Direction, config: ScoringConfig) -> float:
        delta = candidate.energy - current.energy
        
        if direction == Direction.UP:
            if config.up_min_energy_delta <= delta <= config.up_max_energy_delta:
                return 1.0
            elif delta > config.up_max_energy_delta:
                return 0.5
            elif delta > 0:
                return 0.7
            return 0.0
            
        elif direction == Direction.HOLD:
            if abs(delta) <= config.hold_max_energy_delta:
                return 1.0 - (abs(delta) * 0.3)
            return 0.0
            
        elif direction == Direction.DOWN:
            delta = -delta
            if config.down_min_energy_delta <= delta <= config.down_max_energy_delta:
                return 1.0
            elif delta > config.down_max_energy_delta:
                return 0.5
            elif delta > 0:
                return 0.7
            return 0.0
        
        return 0.0


class KeyQualityFactor:
    """Score based on harmonic compatibility"""
    name = "key_quality"
    
    def score(self, current: Track, candidate: Track, direction: Direction, config: ScoringConfig) -> float:
        if candidate.key == current.key:
            return 1.0
        
        compatible = CAMELOT_WHEEL.get(current.key, [])
        
        if candidate.key in compatible:
            # Energy key bonus (same number, different letter)
            if candidate.key[:-1] == current.key[:-1]:
                return 0.95
            return 0.8
        
        # Check 2-step compatibility
        for adj_key in compatible:
            if candidate.key in CAMELOT_WHEEL.get(adj_key, []):
                return 0.5
        
        return 0.0


class VibeCompatibilityFactor:
    """Score based on vibe transitions"""
    name = "vibe_compatibility"
    
    FLOWS = {
        Vibe.DARK: {Vibe.DARK: 1.0, Vibe.HYPNOTIC: 0.9, Vibe.AGGRESSIVE: 0.7, Vibe.CHILL: 0.4, Vibe.BRIGHT: 0.2, Vibe.EUPHORIC: 0.3},
        Vibe.BRIGHT: {Vibe.BRIGHT: 1.0, Vibe.EUPHORIC: 0.9, Vibe.CHILL: 0.7, Vibe.HYPNOTIC: 0.5, Vibe.DARK: 0.2, Vibe.AGGRESSIVE: 0.3},
        Vibe.HYPNOTIC: {Vibe.HYPNOTIC: 1.0, Vibe.DARK: 0.8, Vibe.CHILL: 0.7, Vibe.EUPHORIC: 0.5, Vibe.BRIGHT: 0.4, Vibe.AGGRESSIVE: 0.6},
        Vibe.EUPHORIC: {Vibe.EUPHORIC: 1.0, Vibe.BRIGHT: 0.9, Vibe.HYPNOTIC: 0.6, Vibe.CHILL: 0.5, Vibe.DARK: 0.3, Vibe.AGGRESSIVE: 0.7},
        Vibe.CHILL: {Vibe.CHILL: 1.0, Vibe.HYPNOTIC: 0.8, Vibe.BRIGHT: 0.7, Vibe.DARK: 0.5, Vibe.EUPHORIC: 0.4, Vibe.AGGRESSIVE: 0.2},
        Vibe.AGGRESSIVE: {Vibe.AGGRESSIVE: 1.0, Vibe.DARK: 0.8, Vibe.HYPNOTIC: 0.7, Vibe.EUPHORIC: 0.6, Vibe.BRIGHT: 0.3, Vibe.CHILL: 0.2},
    }
    
    def score(self, current: Track, candidate: Track, direction: Direction, config: ScoringConfig) -> float:
        return self.FLOWS.get(current.vibe, {}).get(candidate.vibe, 0.5)


class NarrativeFlowFactor:
    """Score based on set position progression"""
    name = "narrative_flow"
    
    FLOWS = {
        Intensity.OPENER: {Intensity.OPENER: 0.8, Intensity.JOURNEY: 1.0, Intensity.PEAK: 0.3, Intensity.CLOSER: 0.2},
        Intensity.JOURNEY: {Intensity.OPENER: 0.4, Intensity.JOURNEY: 1.0, Intensity.PEAK: 0.9, Intensity.CLOSER: 0.5},
        Intensity.PEAK: {Intensity.OPENER: 0.1, Intensity.JOURNEY: 0.6, Intensity.PEAK: 0.9, Intensity.CLOSER: 0.7},
        Intensity.CLOSER: {Intensity.OPENER: 0.3, Intensity.JOURNEY: 0.4, Intensity.PEAK: 0.2, Intensity.CLOSER: 1.0},
    }
    
    def score(self, current: Track, candidate: Track, direction: Direction, config: ScoringConfig) -> float:
        base = self.FLOWS.get(current.intensity, {}).get(candidate.intensity, 0.5)
        
        # Direction modifiers
        if direction == Direction.UP:
            if candidate.intensity in [Intensity.JOURNEY, Intensity.PEAK]:
                base *= 1.1
            if candidate.energy_direction == EnergyDirection.BUILDING:
                base *= 1.1
        elif direction == Direction.DOWN:
            if candidate.energy_direction == EnergyDirection.RELEASING:
                base *= 1.2
            if candidate.intensity == Intensity.CLOSER:
                base *= 1.1
        
        return min(1.0, base)


class MixEaseFactor:
    """Score based on transition ease"""
    name = "mix_ease"
    
    def score(self, current: Track, candidate: Track, direction: Direction, config: ScoringConfig) -> float:
        return (current.mix_out_ease + candidate.mix_in_ease) / 20.0


class GenreAffinityFactor:
    """Score based on genre match"""
    name = "genre_affinity"
    
    def score(self, current: Track, candidate: Track, direction: Direction, config: ScoringConfig) -> float:
        if current.genre == candidate.genre:
            return 1.0
        if current.subgenre and candidate.subgenre and current.subgenre == candidate.subgenre:
            return 0.9
        return 0.5


class DanceabilityFactor:
    """Score based on danceability maintenance - keep the floor moving"""
    name = "danceability"
    
    def score(self, current: Track, candidate: Track, direction: Direction, config: ScoringConfig) -> float:
        current_d = current.danceability
        candidate_d = candidate.danceability
        delta = candidate_d - current_d
        
        # Generally want to maintain or increase danceability
        # Dropping danceability risks losing the floor
        
        if direction == Direction.UP:
            # Going UP energy - danceability should stay high or increase
            if candidate_d >= current_d:
                return 1.0
            elif candidate_d >= current_d - 1:
                return 0.7  # Slight drop acceptable
            else:
                return 0.3  # Big drop risky when pushing energy
                
        elif direction == Direction.HOLD:
            # Maintaining - keep danceability stable
            if abs(delta) <= 1:
                return 1.0
            elif candidate_d >= 6:  # Still danceable
                return 0.7
            else:
                return 0.4
                
        elif direction == Direction.DOWN:
            # Going DOWN energy - some danceability drop is natural
            if delta >= -2:
                return 1.0
            elif candidate_d >= 5:  # Still groovy enough
                return 0.7
            else:
                return 0.5  # Getting into chill/ambient territory
        
        return 0.5


class GrooveCompatibilityFactor:
    """Score based on groove style transitions"""
    name = "groove_compatibility"
    
    FLOWS = {
        'four-on-floor': {'four-on-floor': 1.0, 'swung': 0.7, 'syncopated': 0.6, 'broken': 0.4, 'linear': 0.5},
        'broken': {'broken': 1.0, 'syncopated': 0.8, 'swung': 0.6, 'four-on-floor': 0.5, 'linear': 0.6},
        'swung': {'swung': 1.0, 'four-on-floor': 0.7, 'syncopated': 0.7, 'broken': 0.5, 'linear': 0.4},
        'syncopated': {'syncopated': 1.0, 'broken': 0.8, 'swung': 0.7, 'four-on-floor': 0.6, 'linear': 0.5},
        'linear': {'linear': 1.0, 'four-on-floor': 0.6, 'broken': 0.6, 'syncopated': 0.5, 'swung': 0.4},
    }
    
    def score(self, current: Track, candidate: Track, direction: Direction, config: ScoringConfig) -> float:
        if not current.groove_style or not candidate.groove_style:
            return 0.7  # Neutral if unknown
        return self.FLOWS.get(current.groove_style, {}).get(candidate.groove_style, 0.5)


class RecommendationEngine:
    """Main recommendation engine"""
    
    def __init__(self, config: Optional[ScoringConfig] = None):
        self.config = config or ScoringConfig()
        self.factors: list[tuple[ScoringFactor, float]] = []
        self._init_factors()
    
    def _init_factors(self):
        """Initialize scoring factors with weights"""
        self.factors = [
            (EnergyTrajectoryFactor(), self.config.weight_energy_trajectory),
            (DanceabilityFactor(), self.config.weight_danceability),
            (VibeCompatibilityFactor(), self.config.weight_vibe_compatibility),
            (NarrativeFlowFactor(), self.config.weight_narrative_flow),
            (KeyQualityFactor(), self.config.weight_key_quality),
            (GrooveCompatibilityFactor(), self.config.weight_groove_compatibility),
            (MixEaseFactor(), self.config.weight_mix_ease),
            (GenreAffinityFactor(), self.config.weight_genre_affinity),
        ]
    
    def recommend(
        self,
        current: Track,
        corpus: Corpus,
        played: list[str] = None,
        top_n: int = 5,
    ) -> Recommendations:
        """Get recommendations from current track"""
        
        played = played or []
        
        # Hard filters
        candidates = self._filter(current, corpus.tracks, played)
        
        # Score per direction
        up = self._score_direction(current, candidates, Direction.UP)[:top_n]
        hold = self._score_direction(current, candidates, Direction.HOLD)[:top_n]
        down = self._score_direction(current, candidates, Direction.DOWN)[:top_n]
        
        return Recommendations(
            current_track=current,
            up=up,
            hold=hold,
            down=down,
        )
    
    def _filter(self, current: Track, tracks: list[Track], played: list[str]) -> list[Track]:
        """Apply hard filters"""
        
        candidates = []
        
        for track in tracks:
            if track.track_id == current.track_id:
                continue
            if track.track_id in played:
                continue
            if abs(track.bpm - current.bpm) > self.config.bpm_range:
                continue
            
            if not self.config.allow_key_clash:
                compatible = get_compatible_keys(current.key, extended=True)
                if track.key not in compatible:
                    continue
            
            candidates.append(track)
        
        return candidates
    
    def _score_direction(
        self,
        current: Track,
        candidates: list[Track],
        direction: Direction,
    ) -> list[ScoredTrack]:
        """Score candidates for a direction"""
        
        scored = []
        
        for candidate in candidates:
            # Direction compatibility check
            delta = candidate.energy - current.energy
            if direction == Direction.UP and delta < 0:
                continue
            if direction == Direction.DOWN and delta > 0:
                continue
            
            # Calculate weighted score
            factor_scores = {}
            total_weight = 0
            weighted_sum = 0
            
            for factor, weight in self.factors:
                if weight <= 0:
                    continue
                score = factor.score(current, candidate, direction, self.config)
                factor_scores[factor.name] = score
                weighted_sum += score * weight
                total_weight += weight
            
            total = weighted_sum / total_weight if total_weight > 0 else 0
            
            scored.append(ScoredTrack(
                track=candidate,
                direction=direction,
                total_score=total,
                factor_scores=factor_scores,
            ))
        
        scored.sort(key=lambda x: x.total_score, reverse=True)
        return scored
    
    def update_config(self, **kwargs):
        """Update config and rebuild factors"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self._init_factors()
```

---

## 6. Gemini Analysis Pipeline

### 6.1 Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ANALYSIS PIPELINE                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  INPUT                                                              │
│  ─────                                                              │
│  ~/Music/DJ/kpop/                                                   │
│  ├── NewJeans - Super Shy.mp3                                       │
│  ├── NewJeans - OMG.mp3                                             │
│  └── ... (100+ tracks)                                              │
│                                                                      │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  STEP 1: SCAN                                                │    │
│  │                                                              │    │
│  │  • Find all audio files                                      │    │
│  │  • Extract embedded tags (title, artist, BPM)               │    │
│  │  • Match to Rekordbox DB for accurate BPM/key               │    │
│  │  • Compute file hashes for deduplication                    │    │
│  │                                                              │    │
│  │  Output: list[AudioFile]                                    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  STEP 2: ANALYZE (Gemini)                                   │    │
│  │                                                              │    │
│  │  For each AudioFile:                                        │    │
│  │    • Upload audio to Gemini                                 │    │
│  │    • Send analysis prompt with metadata hints               │    │
│  │    • Parse JSON response                                    │    │
│  │    • Compute compatible keys                                │    │
│  │                                                              │    │
│  │  Rate limit: 50 RPM                                         │    │
│  │  Concurrent: 3 parallel                                     │    │
│  │  Cost: ~$0.05/track                                         │    │
│  │                                                              │    │
│  │  Output: list[Track]                                        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  STEP 3: VALIDATE (Quick Check)                             │    │
│  │                                                              │    │
│  │  • Export to CSV for review                                 │    │
│  │  • Spot check 20% of tracks                                 │    │
│  │  • Fix obvious errors                                       │    │
│  │  • Mark validated                                           │    │
│  │                                                              │    │
│  │  Output: validated list[Track]                              │    │
│  └─────────────────────────────────────────────────────────────┘    │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  STEP 4: SAVE                                               │    │
│  │                                                              │    │
│  │  • Save to corpus.json                                      │    │
│  │  • Compute statistics                                       │    │
│  │                                                              │    │
│  │  Output: corpus.json                                        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  OUTPUT                                                             │
│  ──────                                                             │
│  data/corpus.json (100+ analyzed tracks)                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Cost Estimation

| Tracks | API Cost | Time (3 concurrent) | Total |
|--------|----------|---------------------|-------|
| 50 | ~$2.50 | ~35 min | ~40 min |
| 100 | ~$5.00 | ~70 min | ~1.5 hr |
| 150 | ~$7.50 | ~105 min | ~2 hr |

### 6.3 CLI Commands

```bash
# Scan and analyze
python -m flowstate.analyze ~/Music/DJ/kpop/ -o data/corpus.json

# Resume interrupted analysis
python -m flowstate.analyze ~/Music/DJ/kpop/ -o data/corpus.json --resume

# Export for validation
python -m flowstate.corpus export data/corpus.json -o data/review.csv

# Import validated CSV
python -m flowstate.corpus import data/review.csv -o data/corpus.json

# Show stats
python -m flowstate.corpus stats data/corpus.json
```

---

## 7. Recommendation Engine

### 7.1 Scoring Pipeline

```
CURRENT TRACK
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 1: HARD FILTERS                                              │
│  Binary pass/fail - no scoring                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ✓ BPM within ±6 of current                                        │
│  ✓ Key compatible (Camelot wheel, 2-step)                          │
│  ✓ Not the same track                                              │
│  ✓ Not in recently played list                                     │
│                                                                      │
│  100 tracks → ~30 candidates pass                                   │
└─────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 2: DIRECTION SPLIT                                           │
│  Separate candidates by energy direction                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  UP:   candidate.energy > current.energy                           │
│  HOLD: |candidate.energy - current.energy| <= 1                    │
│  DOWN: candidate.energy < current.energy                           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 3: SOFT SCORING                                              │
│  Weighted factors for each candidate in each direction             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  For each (candidate, direction):                                   │
│                                                                      │
│    score = Σ (factor_i.score() × weight_i) / Σ weight_i            │
│                                                                      │
│  Factors:                                                           │
│  ┌──────────────────────┬────────┬─────────────────────────────┐   │
│  │ Factor               │ Weight │ What it measures            │   │
│  ├──────────────────────┼────────┼─────────────────────────────┤   │
│  │ energy_trajectory    │ 1.0    │ Energy delta fits direction │   │
│  │ danceability         │ 0.8    │ Groove maintenance          │   │
│  │ vibe_compatibility   │ 0.7    │ Mood transition quality     │   │
│  │ narrative_flow       │ 0.6    │ Set position progression    │   │
│  │ key_quality          │ 0.5    │ Harmonic compatibility      │   │
│  │ groove_compatibility │ 0.4    │ Rhythm style transitions    │   │
│  │ mix_ease             │ 0.4    │ Technical mixability        │   │
│  │ genre_affinity       │ 0.3    │ Genre match bonus           │   │
│  └──────────────────────┴────────┴─────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 4: RANK & RETURN                                             │
│  Sort by score, return top N per direction                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  UP:   [OMG (0.87), Attention (0.82), GODS (0.79), ...]            │
│  HOLD: [Ditto (0.91), Hype Boy (0.85), ...]                        │
│  DOWN: [Hurt (0.78), ...]                                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Scoring Factor Details

#### Energy Trajectory (Weight: 1.0)

The most important factor. Ensures energy delta matches direction intent.

| Direction | Ideal Delta | Score |
|-----------|-------------|-------|
| UP | +1 to +3 | 1.0 |
| UP | > +3 | 0.5 (too big a jump) |
| UP | 0 | 0.7 (small increase) |
| UP | negative | 0.0 (wrong direction) |
| HOLD | 0 | 1.0 |
| HOLD | ±1 | 0.7 |
| HOLD | > ±1 | 0.0 |
| DOWN | -1 to -3 | 1.0 |
| DOWN | < -3 | 0.5 (too big a drop) |

#### Key Quality (Weight: 0.5)

Harmonic compatibility using Camelot wheel.

| Relationship | Score | Example |
|--------------|-------|---------|
| Same key | 1.0 | 8A → 8A |
| Energy key | 0.95 | 8A → 8B |
| Adjacent | 0.8 | 8A → 7A or 9A |
| 2-step | 0.5 | 8A → 6A |
| Incompatible | 0.0 | 8A → 3B |

#### Vibe Compatibility (Weight: 0.7)

How well emotional characters transition.

```
           TO:
           DARK  BRIGHT  HYPNOTIC  EUPHORIC  CHILL  AGGRESSIVE
FROM:
DARK       1.0   0.2     0.9       0.3       0.4    0.7
BRIGHT     0.2   1.0     0.5       0.9       0.7    0.3
HYPNOTIC   0.8   0.4     1.0       0.5       0.7    0.6
EUPHORIC   0.3   0.9     0.6       1.0       0.5    0.7
CHILL      0.5   0.7     0.8       0.4       1.0    0.2
AGGRESSIVE 0.8   0.3     0.7       0.6       0.2    1.0
```

#### Narrative Flow (Weight: 0.6)

Set position progression logic.

| From | Best To | Score |
|------|---------|-------|
| OPENER | JOURNEY | 1.0 |
| OPENER | PEAK | 0.3 (too fast) |
| JOURNEY | PEAK | 0.9 |
| JOURNEY | JOURNEY | 1.0 |
| PEAK | PEAK | 0.9 |
| PEAK | CLOSER | 0.7 |
| CLOSER | CLOSER | 1.0 |
| CLOSER | PEAK | 0.2 (re-peaking is awkward) |

#### Mix Ease (Weight: 0.4)

Technical transition quality.

```
score = (current.mix_out_ease + candidate.mix_in_ease) / 20
```

#### Genre Affinity (Weight: 0.3)

Genre matching bonus.

| Match | Score |
|-------|-------|
| Same genre | 1.0 |
| Same subgenre | 0.9 |
| Different | 0.5 |

#### Danceability (Weight: 0.8)

Maintains groove and keeps people moving. Second most important factor.

**Danceability Level Scoring:**

| Direction | Danceability Delta | Score |
|-----------|-------------------|-------|
| UP | ≥ 0 (same or higher) | 1.0 |
| UP | -1 | 0.7 |
| UP | < -1 | 0.4 (risky) |
| HOLD | ±1 | 1.0 |
| HOLD | > ±1 | 0.6 |
| DOWN | ≥ -2 | 1.0 |
| DOWN | < -2 | 0.7 |

**Groove Style Compatibility:**

```
             TO:
             4-floor  broken  sync  swung  linear
FROM:
four-on-floor  1.0    0.4    0.6    0.8    0.5
broken         0.4    1.0    0.7    0.5    0.6
syncopated     0.6    0.7    1.0    0.8    0.5
swung          0.8    0.5    0.8    1.0    0.4
linear         0.5    0.6    0.5    0.4    1.0
```

**Groove Styles Explained:**

| Style | Description | Example Genres |
|-------|-------------|----------------|
| four-on-floor | Steady kick on every beat | House, Techno, Trance |
| broken | Syncopated drum patterns, breakbeats | Breaks, DnB, UKG |
| syncopated | Off-beat emphasis, funky | Funk, Disco, R&B |
| swung | Shuffle feel, bounce | UK Garage, Jackin House |
| linear | Minimal, industrial patterns | Minimal, Industrial |

### 7.3 Tuning the Engine

Weights are configurable via YAML:

```yaml
# config/scoring.yaml
weights:
  energy_trajectory: 1.0    # Primary factor
  danceability: 0.8         # Keep them moving!
  vibe_compatibility: 0.7
  narrative_flow: 0.6
  key_quality: 0.5
  groove_compatibility: 0.4 # Rhythm style transitions
  mix_ease: 0.4
  genre_affinity: 0.3
```

Or at runtime:

```python
engine.update_config(weight_vibe_compatibility=0.9)
```

---

## 8. Rekordbox Integration

### 8.1 Approach: Database Polling

Instead of Pro DJ Link (complex, requires network setup), we poll the Rekordbox SQLite database directly.

**Trade-offs:**

| Pro DJ Link | DB Polling |
|-------------|------------|
| Real-time (instant) | Near real-time (5s delay) |
| Complex setup | Simple |
| Network required | Local file |
| May need virtual CDJ | Just file access |
| 2+ days to implement | 2 hours |

For MVP, DB polling is sufficient.

### 8.2 Database Location

```python
from pathlib import Path
import platform

def get_rekordbox_db_path() -> Path:
    if platform.system() == 'Darwin':  # macOS
        return Path.home() / "Library/Pioneer/rekordbox/master.db"
    elif platform.system() == 'Windows':
        return Path.home() / "AppData/Roaming/Pioneer/rekordbox/master.db"
    else:
        raise RuntimeError("Unsupported platform")
```

### 8.3 Database Schema (Relevant Tables)

```sql
-- djmdContent: Track library
CREATE TABLE djmdContent (
    ID INTEGER PRIMARY KEY,
    Title TEXT,
    Artist TEXT,
    Album TEXT,
    Genre TEXT,
    BPM INTEGER,  -- Stored as BPM * 100 (e.g., 12500 = 125.00)
    Tonality TEXT,  -- Key in standard notation (e.g., "Am", "C")
    FolderPath TEXT,
    FileNameL TEXT,
    ...
);

-- djmdHistory: Play history
CREATE TABLE djmdHistory (
    ID INTEGER PRIMARY KEY,
    ContentID INTEGER,  -- FK to djmdContent.ID
    created_at TEXT,  -- ISO timestamp
    ...
);
```

### 8.4 Implementation

```python
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import time


class RekordboxDB:
    """Read-only access to Rekordbox database"""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_rekordbox_db_path()
        self._verify_access()
    
    def _verify_access(self):
        if not self.db_path.exists():
            raise FileNotFoundError(f"Rekordbox DB not found: {self.db_path}")
    
    def _connect(self):
        # Read-only connection (works while Rekordbox is open)
        return sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
    
    def get_last_played(self) -> Optional[dict]:
        """Get the most recently played track"""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                c.ID,
                c.Title,
                c.Artist,
                c.BPM / 100.0 as BPM,
                c.Tonality,
                c.FolderPath || c.FileNameL as FilePath,
                h.created_at
            FROM djmdHistory h
            JOIN djmdContent c ON h.ContentID = c.ID
            ORDER BY h.created_at DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'rekordbox_id': row[0],
                'title': row[1],
                'artist': row[2],
                'bpm': row[3],
                'key': self._convert_key(row[4]),
                'file_path': row[5],
                'played_at': row[6],
            }
        return None
    
    def find_by_path(self, path: str) -> Optional[dict]:
        """Find track by file path"""
        conn = self._connect()
        cursor = conn.cursor()
        
        # Rekordbox stores path in two parts
        cursor.execute("""
            SELECT 
                ID,
                Title,
                Artist,
                BPM / 100.0,
                Tonality
            FROM djmdContent
            WHERE FolderPath || FileNameL = ?
        """, (path,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'title': row[1],
                'artist': row[2],
                'bpm': row[3],
                'key': self._convert_key(row[4]),
            }
        return None
    
    def _convert_key(self, tonality: str) -> str:
        """Convert Rekordbox key notation to Camelot"""
        # Rekordbox uses standard notation (Am, C, F#m, etc.)
        # Convert to Camelot
        KEY_MAP = {
            'C': '8B', 'Am': '8A',
            'G': '9B', 'Em': '9A',
            'D': '10B', 'Bm': '10A',
            'A': '11B', 'F#m': '11A',
            'E': '12B', 'C#m': '12A',
            'B': '1B', 'G#m': '1A',
            'F#': '2B', 'D#m': '2A',
            'Db': '3B', 'Bbm': '3A',
            'Ab': '4B', 'Fm': '4A',
            'Eb': '5B', 'Cm': '5A',
            'Bb': '6B', 'Gm': '6A',
            'F': '7B', 'Dm': '7A',
        }
        return KEY_MAP.get(tonality, tonality)


class RekordboxMonitor:
    """Monitor Rekordbox for track changes"""
    
    def __init__(self, corpus: Corpus, poll_interval: float = 5.0):
        self.db = RekordboxDB()
        self.corpus = corpus
        self.poll_interval = poll_interval
        self.last_track_id: Optional[str] = None
        self.callbacks: list[Callable[[Track], None]] = []
    
    def on_track_change(self, callback: Callable[[Track], None]):
        """Register callback for track changes"""
        self.callbacks.append(callback)
    
    def get_current_track(self) -> Optional[Track]:
        """Get currently playing track matched to corpus"""
        last_played = self.db.get_last_played()
        if not last_played:
            return None
        
        # Try to match to corpus
        # Priority 1: File path
        track = self.corpus.get_by_path(last_played['file_path'])
        if track:
            return track
        
        # Priority 2: Title + Artist fuzzy match
        track = self._fuzzy_match(last_played['title'], last_played['artist'])
        if track:
            return track
        
        return None
    
    def _fuzzy_match(self, title: str, artist: str) -> Optional[Track]:
        """Fuzzy match by title and artist"""
        from difflib import SequenceMatcher
        
        target = f"{title}|{artist}".lower()
        best_match = None
        best_score = 0.0
        
        for track in self.corpus.tracks:
            candidate = f"{track.title}|{track.artist}".lower()
            score = SequenceMatcher(None, target, candidate).ratio()
            
            if score > best_score and score > 0.8:
                best_score = score
                best_match = track
        
        return best_match
    
    def poll_loop(self):
        """Main polling loop - run in thread"""
        while True:
            try:
                track = self.get_current_track()
                
                if track and track.track_id != self.last_track_id:
                    self.last_track_id = track.track_id
                    for callback in self.callbacks:
                        callback(track)
            
            except Exception as e:
                print(f"Polling error: {e}")
            
            time.sleep(self.poll_interval)
```

---

## 9. User Interface

### 9.1 Terminal UI (Primary)

Built with Rich for styled terminal output.

```
┌─────────────────────────────────────────────────────────────────────┐
│  FLOWSTATE                                          Set: 47 min    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  NOW PLAYING                                                       │
│  ───────────────────────────────────────────────────────────────── │
│  Super Shy - NewJeans                                              │
│  125 BPM │ 8A │ E:7 │ D:8 │ bright │ journey                       │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ▲ UP - Increase Energy                                            │
│  ───────────────────────────────────────────────────────────────── │
│  1. OMG - NewJeans                                                 │
│     8A │ E:8 D:9 │ 0.87 │ euphoric                                 │
│  2. Attention - NewJeans                                           │
│     8B │ E:8 D:8 │ 0.82 │ bright                                   │
│  3. GODS - NewJeans                                                │
│     7A │ E:9 D:9 │ 0.79 │ euphoric                                 │
│                                                                     │
│  ━ HOLD - Maintain Energy                                          │
│  ───────────────────────────────────────────────────────────────── │
│  1. Ditto - NewJeans                                               │
│     8A │ E:7 D:8 │ 0.91 │ hypnotic                                 │
│  2. Hype Boy - NewJeans                                            │
│     9A │ E:7 D:9 │ 0.85 │ bright                                   │
│                                                                     │
│  ▼ DOWN - Decrease Energy                                          │
│  ───────────────────────────────────────────────────────────────── │
│  1. Hurt - NewJeans                                                │
│     8A │ E:5 D:6 │ 0.78 │ chill                                    │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  [R] Refresh  [S] Search  [D] Debug  [Q] Quit                      │
└─────────────────────────────────────────────────────────────────────┘
```

E = Energy, D = Danceability

### 9.2 Web UI (Alternative)

Simple Flask + HTMX for tablet viewing at the booth.

```
┌────────────────────────────────────────┐
│  FLOWSTATE            47 min          │
├────────────────────────────────────────┤
│                                        │
│  NOW: Super Shy                        │
│  NewJeans │ 8A │ 125 │ E:7            │
│                                        │
├────────────────────────────────────────┤
│ ┌────────────────────────────────────┐ │
│ │ ▲ UP                               │ │
│ │                                    │ │
│ │   OMG (0.87)                      │ │
│ │   Attention (0.82)                │ │
│ │   GODS (0.79)                     │ │
│ └────────────────────────────────────┘ │
│                                        │
│ ┌────────────────────────────────────┐ │
│ │ ━ HOLD                             │ │
│ │                                    │ │
│ │   Ditto (0.91)                    │ │
│ │   Hype Boy (0.85)                 │ │
│ └────────────────────────────────────┘ │
│                                        │
│ ┌────────────────────────────────────┐ │
│ │ ▼ DOWN                             │ │
│ │                                    │ │
│ │   Hurt (0.78)                     │ │
│ └────────────────────────────────────┘ │
│                                        │
│  Auto-refresh: 5s                      │
└────────────────────────────────────────┘
```

### 9.3 Implementation

```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
import time


class TerminalUI:
    """Rich terminal UI for recommendations"""
    
    def __init__(self, engine: RecommendationEngine, corpus: Corpus):
        self.engine = engine
        self.corpus = corpus
        self.monitor = RekordboxMonitor(corpus)
        self.console = Console()
        self.current_track: Optional[Track] = None
        self.recommendations: Optional[Recommendations] = None
    
    def run(self):
        """Main UI loop"""
        
        self.monitor.on_track_change(self._on_track_change)
        
        # Start polling in background
        import threading
        poll_thread = threading.Thread(target=self.monitor.poll_loop, daemon=True)
        poll_thread.start()
        
        # UI loop
        with Live(self._render(), refresh_per_second=1, console=self.console) as live:
            while True:
                live.update(self._render())
                time.sleep(1)
    
    def _on_track_change(self, track: Track):
        """Handle track change"""
        self.current_track = track
        self.recommendations = self.engine.recommend(track, self.corpus)
    
    def _render(self) -> Panel:
        """Render the UI"""
        
        layout = Layout()
        
        # Now playing section
        if self.current_track:
            now_playing = self._render_now_playing()
        else:
            now_playing = "[dim]Waiting for track...[/dim]"
        
        # Recommendations
        if self.recommendations:
            recs = self._render_recommendations()
        else:
            recs = "[dim]No recommendations yet[/dim]"
        
        content = f"""
{now_playing}

{recs}

[dim][R] Refresh  [S] Search  [D] Debug scores  [Q] Quit[/dim]
"""
        
        return Panel(content, title="FLOWSTATE", border_style="blue")
    
    def _render_now_playing(self) -> str:
        t = self.current_track
        return f"""[bold]NOW PLAYING[/bold]
[bold cyan]{t.title}[/bold cyan] - {t.artist}
{t.bpm:.0f} BPM │ {t.key} │ E:{t.energy} D:{t.danceability} │ {t.vibe.value} │ {t.intensity.value}
"""
    
    def _render_recommendations(self) -> str:
        sections = []
        
        for direction, label, icon in [
            (Direction.UP, "UP - Increase Energy", "▲"),
            (Direction.HOLD, "HOLD - Maintain Energy", "━"),
            (Direction.DOWN, "DOWN - Decrease Energy", "▼"),
        ]:
            tracks = self.recommendations.get(direction)
            
            lines = [f"[bold]{icon} {label}[/bold]"]
            
            if tracks:
                for i, scored in enumerate(tracks[:5], 1):
                    t = scored.track
                    lines.append(
                        f"  {i}. [cyan]{t.title}[/cyan] - {t.artist}\n"
                        f"     {t.key} │ E:{t.energy} D:{t.danceability} │ {scored.total_score:.2f} │ {t.vibe.value}"
                    )
            else:
                lines.append("  [dim]No tracks available[/dim]")
            
            sections.append("\n".join(lines))
        
        return "\n\n".join(sections)
```

---

## 10. Configuration

### 10.1 Config File Structure

```yaml
# config/flowstate.yaml

# Corpus settings
corpus:
  path: "data/corpus.json"

# Rekordbox integration  
rekordbox:
  db_path: null  # Auto-detect if null
  poll_interval: 5.0  # seconds

# Gemini API (for analysis)
gemini:
  model: "gemini-2.5-pro"
  max_concurrent: 3
  requests_per_minute: 50

# Recommendation engine
scoring:
  bpm_range: 6.0
  allow_key_clash: false
  
  weights:
    energy_trajectory: 1.0
    danceability: 0.8         # Keep people moving
    vibe_compatibility: 0.7
    narrative_flow: 0.6
    key_quality: 0.5
    groove_compatibility: 0.4 # Rhythm style transitions
    mix_ease: 0.4
    genre_affinity: 0.3
  
  directions:
    up:
      min_energy_delta: 1
      max_energy_delta: 3
    hold:
      max_energy_delta: 1
    down:
      min_energy_delta: 1
      max_energy_delta: 3

# UI settings
ui:
  mode: "terminal"  # terminal or web
  top_n: 5  # tracks per direction
  
  web:
    host: "0.0.0.0"
    port: 5000
```

### 10.2 Environment Variables

```bash
# .env
GEMINI_API_KEY=your_api_key_here
FLOWSTATE_CONFIG=config/flowstate.yaml
```

### 10.3 Config Loading

```python
from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
import yaml


class ScoringWeights(BaseSettings):
    energy_trajectory: float = 1.0
    danceability: float = 0.8
    vibe_compatibility: float = 0.7
    narrative_flow: float = 0.6
    key_quality: float = 0.5
    groove_compatibility: float = 0.4
    mix_ease: float = 0.4
    genre_affinity: float = 0.3


class Config(BaseSettings):
    corpus_path: Path = Path("data/corpus.json")
    gemini_api_key: str = Field(alias="GEMINI_API_KEY")
    rekordbox_poll_interval: float = 5.0
    scoring_weights: ScoringWeights = ScoringWeights()
    ui_mode: str = "terminal"
    top_n: int = 5
    
    @classmethod
    def load(cls, path: str = None) -> 'Config':
        if path and Path(path).exists():
            with open(path) as f:
                data = yaml.safe_load(f)
            return cls(**data)
        return cls()
```

---

## 11. File Structure

```
flowstate/
├── README.md
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
│
├── config/
│   └── flowstate.yaml
│
├── data/
│   ├── corpus.json          # Analyzed tracks
│   └── review.csv           # For validation
│
├── src/
│   └── flowstate/
│       ├── __init__.py
│       ├── __main__.py       # Entry point
│       ├── config.py         # Configuration
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── track.py      # Track, Vibe, Intensity, etc.
│       │   ├── corpus.py     # Corpus, CorpusStats
│       │   └── recommendations.py  # Direction, ScoredTrack
│       │
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── scanner.py    # AudioScanner
│       │   └── gemini.py     # GeminiAnalyzer
│       │
│       ├── engine/
│       │   ├── __init__.py
│       │   ├── factors.py    # Scoring factors
│       │   ├── engine.py     # RecommendationEngine
│       │   └── camelot.py    # Key compatibility
│       │
│       ├── rekordbox/
│       │   ├── __init__.py
│       │   ├── db.py         # RekordboxDB
│       │   └── monitor.py    # RekordboxMonitor
│       │
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── terminal.py   # Rich terminal UI
│       │   └── web.py        # Flask web UI (optional)
│       │
│       └── cli/
│           ├── __init__.py
│           ├── analyze.py    # Analysis commands
│           ├── corpus.py     # Corpus management
│           └── run.py        # Main app
│
└── tests/
    ├── __init__.py
    ├── test_engine.py
    ├── test_models.py
    └── fixtures/
        └── sample_corpus.json
```

---

## 12. Implementation Plan

### 12.1 Timeline Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        20-DAY TIMELINE                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  PHASE 1: CORPUS BUILDING                        Days 1-7           │
│  ═══════════════════════════════════════════════════════════════    │
│  │                                                                  │
│  ├── Day 1-2: Scanner + Gemini pipeline                            │
│  │   • Project scaffolding                                         │
│  │   • AudioScanner implementation                                 │
│  │   • GeminiAnalyzer implementation                               │
│  │   • CLI for batch analysis                                      │
│  │                                                                  │
│  ├── Day 3-5: Run analysis                                         │
│  │   • Analyze 100-150 tracks overnight                            │
│  │   • Monitor for errors                                          │
│  │   • Cost: ~$5-8                                                 │
│  │                                                                  │
│  └── Day 6-7: Validation                                           │
│      • Export to CSV                                               │
│      • Spot-check 20 tracks                                        │
│      • Fix obvious errors                                          │
│      • Save final corpus                                           │
│                                                                      │
│  PHASE 2: ENGINE + INTEGRATION                   Days 8-12          │
│  ═══════════════════════════════════════════════════════════════    │
│  │                                                                  │
│  ├── Day 8-9: Recommendation engine                                │
│  │   • Data models (Track, Direction, etc.)                        │
│  │   • Scoring factors                                             │
│  │   • RecommendationEngine                                        │
│  │   • Unit tests                                                  │
│  │                                                                  │
│  └── Day 10-12: Rekordbox integration                              │
│      • RekordboxDB reader                                          │
│      • RekordboxMonitor (polling)                                  │
│      • Track matching logic                                        │
│      • Integration test                                            │
│                                                                      │
│  PHASE 3: USER INTERFACE                         Days 13-16         │
│  ═══════════════════════════════════════════════════════════════    │
│  │                                                                  │
│  ├── Day 13-14: Terminal UI                                        │
│  │   • Rich-based display                                          │
│  │   • Live updates                                                │
│  │   • Keyboard controls                                           │
│  │                                                                  │
│  └── Day 15-16: Polish                                             │
│      • Search/filter                                               │
│      • Manual track selection                                      │
│      • Error handling                                              │
│      • (Optional) Web UI                                           │
│                                                                      │
│  PHASE 4: BATTLE TEST                            Days 17-20         │
│  ═══════════════════════════════════════════════════════════════    │
│  │                                                                  │
│  ├── Day 17-18: Practice sets                                      │
│  │   • Run 2-3 practice sessions                                   │
│  │   • Note issues                                                 │
│  │   • Tune scoring weights                                        │
│  │                                                                  │
│  └── Day 19-20: Buffer                                             │
│      • Fix critical bugs                                           │
│      • Final tuning                                                │
│      • Backup plan ready                                           │
│                                                                      │
│  ════════════════════════════════════════════════════════════════   │
│                                                                      │
│  DAY 21: GIG                                                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 12.2 Daily Deliverables

| Day | Deliverable | Hours | Risk |
|-----|-------------|-------|------|
| 1 | Project setup, AudioScanner | 3 | Low |
| 2 | GeminiAnalyzer, CLI | 4 | Low |
| 3 | Start batch analysis | 2 | Low |
| 4 | Monitor analysis, fix issues | 2 | Medium |
| 5 | Complete analysis | 1 | Low |
| 6 | Export, start validation | 2 | Low |
| 7 | Complete validation, save corpus | 2 | Low |
| 8 | Track models, scoring factors | 4 | Low |
| 9 | RecommendationEngine, tests | 4 | Low |
| 10 | RekordboxDB reader | 3 | Medium |
| 11 | RekordboxMonitor | 3 | Medium |
| 12 | Integration testing | 3 | Medium |
| 13 | Terminal UI layout | 4 | Low |
| 14 | Live updates, keyboard | 3 | Low |
| 15 | Search, manual selection | 3 | Low |
| 16 | Polish, error handling | 3 | Low |
| 17 | Practice set #1 | 2 | Low |
| 18 | Practice set #2, fixes | 3 | Medium |
| 19 | Critical fixes | 2 | Medium |
| 20 | Final check, backup plan | 1 | Low |

**Total: ~54 hours** (~2.7 hrs/day average)

### 12.3 Milestones

| Milestone | Day | Validation |
|-----------|-----|------------|
| **M1: Corpus Ready** | 7 | 100+ tracks in corpus.json |
| **M2: Engine Working** | 12 | Recommendations from REPL |
| **M3: UI Complete** | 16 | Full terminal UI running |
| **M4: Gig Ready** | 18 | 2 practice sets completed |

---

## 13. Risk Mitigation

### 13.1 Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Gemini API errors/rate limits | Medium | High | Retry logic, batch overnight |
| Rekordbox DB locked | Low | Medium | Read-only mode, try again |
| Bad track analysis | Medium | Medium | Spot-check validation |
| Pro DJ Link needed | Low | High | Fallback to manual selection |
| Not enough time | Medium | High | Cut features, not quality |
| Weight tuning wrong | Medium | Low | Defaults are reasonable |

### 13.2 Fallback Plans

**If Rekordbox integration fails:**
- Manual track selection in UI
- Type track name to search corpus

**If recommendations are bad:**
- Tune weights in config
- Fall back to just BPM + key filtering

**If UI isn't ready:**
- Python REPL is usable
- Print recommendations to console

**If tool fails at gig:**
- DJ without it (you've done it before)
- Use Rekordbox's built-in related tracks

---

## 14. Future Enhancements

### 14.1 Post-Gig (Month 2)

| Feature | Effort | Value |
|---------|--------|-------|
| Set history tracking | 2 hrs | Medium |
| Export set to playlist | 3 hrs | Medium |
| More scoring factors | 4 hrs | High |
| Web UI for mobile | 8 hrs | Medium |

### 14.2 Long-Term

| Feature | Effort | Value |
|---------|--------|-------|
| Pro DJ Link (real-time) | 2 days | High |
| Fine-tune local model | 1 week | Medium |
| Gemini deep analysis | 1 day | Medium |
| 6 narrative directions | 2 days | Medium |
| Crowd feedback loop | 1 week | High |

---

## Appendix A: Quick Start

```bash
# 1. Clone and setup
git clone <repo>
cd flowstate
python -m venv .venv
source .venv/bin/activate
pip install -e .

# 2. Configure
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# 3. Analyze your tracks
python -m flowstate.analyze ~/Music/DJ/kpop/ -o data/corpus.json

# 4. Run the app
python -m flowstate
```

---

## Appendix B: Scoring Weight Recommendations

### Conservative (Safe for First Gig)

```yaml
weights:
  energy_trajectory: 1.0
  danceability: 0.9         # Keep them moving!
  key_quality: 0.7          # Prioritize harmonic mixing
  vibe_compatibility: 0.5
  narrative_flow: 0.4
  groove_compatibility: 0.5 # Stick to familiar rhythms
  mix_ease: 0.5             # Prioritize easy transitions
  genre_affinity: 0.3
```

### Adventurous (After Practice)

```yaml
weights:
  energy_trajectory: 1.0
  danceability: 0.7         # Allow groove experiments
  key_quality: 0.4          # Allow more key experiments
  vibe_compatibility: 0.8   # Trust vibe transitions
  narrative_flow: 0.7
  groove_compatibility: 0.3 # Allow rhythm shifts
  mix_ease: 0.3
  genre_affinity: 0.2       # Allow genre blending
```

### Peak Hour (Maximum Dancefloor)

```yaml
weights:
  energy_trajectory: 1.0
  danceability: 1.0         # Nothing else matters
  key_quality: 0.5
  vibe_compatibility: 0.6
  narrative_flow: 0.3       # Less about journey, more about NOW
  groove_compatibility: 0.6 # Keep the groove locked
  mix_ease: 0.4
  genre_affinity: 0.2
```

---

*End of Design Document*
