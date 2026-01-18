# FLOWSTATE

DJ decision support system - real-time track recommendations based on energy, key, vibe, and danceability.

## Installation

### Prerequisites

- Python 3.11+
- ffmpeg (for video downloads and WAV metadata)
- A Google AI API key for Gemini

### Install from source

```bash
git clone https://github.com/metakai1/flowstate.git
cd flowstate
pip install -e .
```

### System dependencies

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

**Windows (WSL):**
```bash
sudo apt install ffmpeg
```

## Quick Start

```bash
# Set up Gemini API key
export GOOGLE_API_KEY=your_api_key

# Analyze your music library
flowstate analyze ~/Music/DJ/ -o data/corpus.json

# Run the web UI with Rekordbox sync
flowstate run --ui web --rekordbox
```

Then open http://localhost:5000 in your browser.

## Features

- AI-powered track analysis using Gemini 2.5 Pro
- Real-time recommendations in 3 energy directions: UP, HOLD, DOWN
- Harmonic mixing support (Camelot wheel)
- Web UI with live Rekordbox sync
- Side-by-side comparison of Now Playing and candidate tracks
- Music video downloads for Rekordbox video playback

## Web UI

The web interface shows:
- **Now Playing** - Current track from Rekordbox with BPM, key, energy, and mix-out notes
- **Track Preview** - Click any recommendation to see detailed comparison
- **Recommendations** - Top 3 tracks for each energy direction (UP/HOLD/DOWN)

Press `R` or click the refresh button to force-sync from Rekordbox.

## CLI Commands

```bash
# Analyze tracks with Gemini
flowstate analyze ~/Music/DJ/ -o data/corpus.json

# Run web UI
flowstate run --ui web --rekordbox

# Corpus management
flowstate corpus stats data/corpus.json
flowstate corpus export data/corpus.json -o review.csv

# Write metadata to WAV files (for Rekordbox import)
flowstate write-metadata /path/to/wav/files

# Download music videos from YouTube
flowstate download-videos -o /path/to/videos --limit 10
```

## Rekordbox Integration

FLOWSTATE reads from Rekordbox's SQLite database to detect the currently playing track. The database is polled every few seconds.

**Note:** Rekordbox doesn't flush to the database immediately when loading tracks - expect 10-30 second delays.

## Video Support

Download music videos for Rekordbox video playback:

```bash
flowstate download-videos -o ~/Music/kpop-videos
```

Videos are saved as MP4 with artist/title metadata. After downloading, manually link them in Rekordbox using the LINK button.

## Configuration

Set your Gemini API key as an environment variable:

```bash
export GOOGLE_API_KEY=your_api_key
```

Or create a `.env` file in your project directory:

```
GOOGLE_API_KEY=your_api_key
```

## License

MIT
