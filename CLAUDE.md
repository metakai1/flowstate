# FLOWSTATE - DJ Decision Support System

## Project Overview

FLOWSTATE is a DJ decision support system that analyzes music libraries using AI and provides real-time track recommendations during live sets based on energy, key compatibility, vibe, and danceability.

## Tech Stack

- **Language:** Python 3.11+
- **AI:** Google Generative AI (Gemini 2.5 Pro)
- **Audio Metadata:** Mutagen 1.47+
- **Data Validation:** Pydantic 2.0+
- **Web UI:** Flask + vanilla JS
- **Database:** SQLite (Rekordbox integration via pyrekordbox)
- **Video Downloads:** yt-dlp

## Project Structure

```
flowstate/
├── src/flowstate/
│   ├── __init__.py
│   ├── models/           # Pydantic data models (Track, Corpus)
│   ├── analysis/         # Gemini audio analysis + scanner
│   ├── engine/           # Recommendation engine with scoring factors
│   ├── integrations/     # Rekordbox DB integration
│   ├── ui/               # Web UI (Flask)
│   └── cli/              # Click CLI entry points
├── data/                 # Corpus JSON files
├── design/               # Design documents
└── pyproject.toml
```

## Running the App

```bash
# Web UI with Rekordbox sync
flowstate run --ui web --rekordbox

# Then open http://localhost:5000
```

## Core Concepts

### Energy Directions
- **UP:** Increase energy (+1 to +3 energy delta)
- **HOLD:** Maintain energy (±1 energy delta)
- **DOWN:** Decrease energy (-1 to -3 energy delta)

### Track Attributes
- **Energy (1-10):** Overall intensity level
- **Danceability (1-10):** How much the track invites movement
- **Vibe:** dark | bright | hypnotic | euphoric | chill | aggressive
- **Intensity:** opener | journey | peak | closer
- **Key:** Camelot notation (1A-12A, 1B-12B)
- **Groove Style:** four-on-floor | broken | swung | syncopated | linear
- **Description:** Concise artistic description of the track (AI-generated)

### Scoring Factors (by weight)
1. Energy Trajectory (1.0) - Primary factor
2. Danceability (0.8)
3. Vibe Compatibility (0.7)
4. Narrative Flow (0.6)
5. Key Quality (0.5) - Harmonic compatibility (Camelot wheel)
6. Groove Compatibility (0.4)
7. Mix Ease (0.4)
8. Genre Affinity (0.3)

## CLI Commands

```bash
# Analyze tracks with Gemini
flowstate analyze ~/Music/DJ/ -o data/corpus.json

# Run web UI
flowstate run --ui web --rekordbox

# Corpus management
flowstate corpus stats data/corpus.json
flowstate corpus export data/corpus.json -o review.csv

# Write metadata to WAV files
flowstate write-metadata /path/to/wav/files

# Download music videos
flowstate download-videos -o /path/to/videos
```

## Web UI Layout

The web interface has a side-by-side layout:
- **Left:** Now Playing (from Rekordbox) with stats and mix-out notes
- **Right:** Track Preview (click any recommendation to compare)
- **Below:** 3-column recommendation grid (UP / HOLD / DOWN)

Press `R` to force-refresh from Rekordbox.

## Rekordbox Integration

- Reads from Rekordbox 6 SQLite database via pyrekordbox
- Database path auto-detected or configurable
- Polls history table for most recently loaded track
- WAL checkpoint performed on each refresh to get latest data
- **Limitation:** Rekordbox batches DB writes, so expect 10-30s delay

## Video Support

```bash
flowstate download-videos -o ~/Music/kpop-videos
```

- Downloads from YouTube using yt-dlp
- Saves as MP4 with artist/title metadata
- Rekordbox-compatible format (H.264, up to 1080p)
- Manual linking required in Rekordbox (LINK button)

## Development Notes

- BPM tolerance: ±6 BPM for recommendations
- Key compatibility uses extended Camelot wheel (2-step compatible)
- Corpus stored as JSON with incremental saves
