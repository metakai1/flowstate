# FLOWSTATE - DJ Decision Support System

## Project Overview

FLOWSTATE is a DJ decision support system that analyzes music libraries using AI and provides real-time track recommendations during live sets based on energy, key compatibility, vibe, and danceability.

**Target:** Gig-ready in 20 days
**Author:** Kai

## Tech Stack

- **Language:** Python 3.11+
- **AI:** Google Generative AI (Gemini 3)
- **Audio Metadata:** Mutagen 1.47+
- **Data Validation:** Pydantic 2.0+
- **Terminal UI:** Rich 13.0+
- **Web UI (optional):** Flask + HTMX 3.0+
- **Database:** SQLite (Rekordbox integration)
- **Config:** YAML + Pydantic Settings

## Project Structure

```
flowstate/
├── src/flowstate/
│   ├── __init__.py
│   ├── models/           # Pydantic data models (Track, Corpus, Recommendations)
│   ├── analyzer/         # Gemini audio analysis pipeline
│   ├── scanner/          # Audio file scanner with Mutagen
│   ├── engine/           # Recommendation engine with scoring factors
│   ├── rekordbox/        # Rekordbox DB integration
│   ├── ui/               # Terminal (Rich) and Web (Flask) UIs
│   └── cli.py            # Click CLI entry points
├── config/               # YAML configuration files
├── data/                 # Corpus JSON files
├── design/               # Design documents
├── tests/                # Pytest tests
└── pyproject.toml
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
- **Description:** Concise artistic description of the track (AI-generated) - stored in corpus

### Gemini Analysis Output
The Gemini 3 analysis prompt must return:
- All standard track metadata (BPM, key, energy, etc.)
- A **concise artistic track description** (1-2 sentences capturing the essence/mood)

### Scoring Factors (by weight)
1. Energy Trajectory (1.0) - Primary factor
2. Danceability (0.8) - Keep the floor moving
3. Vibe Compatibility (0.7) - Mood transitions
4. Narrative Flow (0.6) - Set position progression
5. Key Quality (0.5) - Harmonic compatibility (Camelot wheel)
6. Groove Compatibility (0.4) - Rhythm style transitions
7. Mix Ease (0.4) - Technical mixability
8. Genre Affinity (0.3) - Genre match bonus

## Key Commands

```bash
# Analyze tracks
python -m flowstate.analyze ~/Music/DJ/kpop/ -o data/corpus.json

# Run live recommendations
python -m flowstate.live

# Export corpus for review
python -m flowstate.corpus export data/corpus.json -o data/review.csv

# Show corpus stats
python -m flowstate.corpus stats data/corpus.json
```

## Development Guidelines

1. **Keep it simple** - MVP focused, gig-ready in 20 days
2. **Use Pydantic** for all data models with validation
3. **Gemini 3** for audio analysis (not 2.5)
4. **Rekordbox DB polling** instead of Pro DJ Link (simpler)
5. **Terminal UI first** (Rich), web UI optional
6. **JSON corpus** - no complex database needed
7. **Configurable weights** via YAML for scoring tuning

## Important Notes

- The Gemini analysis prompt must include generating a **concise artistic track description** to be stored with each track
- BPM tolerance: ±6 BPM for recommendations
- Key compatibility uses extended Camelot wheel (2-step compatible)
- Poll Rekordbox DB every 5 seconds for track changes
- Cost estimate: ~$0.05/track for Gemini analysis

## Design Document

Full specification available at: `design/flowstate-mvp-design-doc.md`
