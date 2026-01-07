# FLOWSTATE

DJ decision support system - real-time track recommendations based on energy, key, vibe, and danceability.

## Quick Start

```bash
# Install
pip install -e .

# Analyze tracks
flowstate analyze ~/Music/DJ/ -o data/corpus.json

# Run recommendations
flowstate run -c data/corpus.json
```

## Features

- AI-powered track analysis using Gemini 2.5 Pro
- Real-time recommendations in 3 directions: UP, HOLD, DOWN
- Harmonic mixing support (Camelot wheel)
- Rich terminal UI
- Configurable scoring weights
