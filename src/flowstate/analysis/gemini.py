"""Gemini audio analysis for track metadata extraction."""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import google.generativeai as genai
from pydantic import ValidationError

from ..models import AudioFile, Track
from ..engine.camelot import compute_compatible_keys, to_camelot

# Analysis prompt with expanded fields
ANALYSIS_PROMPT = """Analyze this audio track and return a JSON object with the following fields.
Be precise and consistent. Use your musical expertise to assess each attribute.

IMPORTANT: Listen carefully to the ENTIRE track before responding.

Required JSON structure:
{{
    "bpm": <number 60-200, beats per minute - be precise>,
    "key": "<Camelot notation: 1A-12A for minor, 1B-12B for major>",

    "energy": <1-10, overall intensity level>,
    "danceability": <1-10, how much it invites physical movement>,

    "vibe": "<one of: dark | bright | hypnotic | euphoric | chill | aggressive>",
    "intensity": "<one of: opener | journey | peak | closer - where it fits in a DJ set>",
    "mood_tags": ["<3-5 mood descriptors like: uplifting, melancholic, driving, dreamy, etc>"],

    "groove_style": "<one of: four-on-floor | broken | swung | syncopated | linear>",
    "tempo_feel": "<one of: straight | double-time | half-time>",

    "mix_in_ease": <1-10, how easy to mix INTO this track>,
    "mix_out_ease": <1-10, how easy to mix OUT OF this track>,
    "mixability_notes": "<brief DJ tips for mixing this track>",

    "vocal_presence": "<one of: instrumental | male | female | mixed | group>",
    "vocal_style": "<one of: rap | singing | both | chant | none>",
    "language": "<primary language: korean | english | japanese | mixed | other | null if instrumental>",

    "structure": ["<ordered list of sections: intro, verse, prechorus, chorus, drop, breakdown, bridge, outro, etc>"],
    "drop_intensity": <1-10 or null if no clear drop, intensity of the main drop/chorus>,

    "instrumentation": ["<3-6 prominent sounds: synth, bass, drums, brass, strings, vocal chops, etc>"],
    "production_style": "<production character: clean | distorted | filtered | lo-fi | polished | raw | layered>",

    "production_quality": <1-10, mix clarity, mastering quality, professional sound>,
    "audio_fidelity": <1-10, file quality - check for compression artifacts, clipping, encoding issues>,

    "genre": "<primary genre>",
    "subgenre": "<specific subgenre or null>",
    "similar_artists": ["<2-3 artists with similar sound>"],

    "description": "<1-2 sentence artistic description capturing the track's essence and emotional character>"
}}

IMPORTANT GUIDELINES:
- BPM: Count carefully, K-pop is often 100-130 BPM
- Key: Use Camelot notation (e.g., "8A" for A minor, "8B" for C major)
- Energy vs Danceability: A chill track can have high danceability if it grooves
- Vibe: Choose the DOMINANT mood, not a blend
- Mix ease: 10 = clean intro/outro, easy to beatmatch; 1 = complex, hard to blend
- Production quality: Rate the craftsmanship, not your personal taste
- Audio fidelity: Flag bad rips, transcodes, or mastering issues
- Description: Be evocative and specific, not generic

Metadata hints from file:
- Title: {title}
- Artist: {artist}
- File BPM (if available): {bpm}
- Duration: {duration}s

Return ONLY the JSON object, no markdown formatting or explanation."""


class GeminiAnalyzer:
    """Analyze audio tracks using Gemini 2.5 Pro."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-pro",
        max_concurrent: int = 3,
        requests_per_minute: int = 50,
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model)
        self.max_concurrent = max_concurrent
        self.requests_per_minute = requests_per_minute
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._request_times: list[float] = []

    async def _rate_limit(self) -> None:
        """Enforce rate limiting."""
        now = asyncio.get_event_loop().time()

        # Remove old timestamps
        self._request_times = [
            t for t in self._request_times
            if now - t < 60
        ]

        # Wait if at limit
        if len(self._request_times) >= self.requests_per_minute:
            wait_time = 60 - (now - self._request_times[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        self._request_times.append(now)

    def _build_prompt(self, audio_file: AudioFile) -> str:
        """Build the analysis prompt with file metadata hints."""
        return ANALYSIS_PROMPT.format(
            title=audio_file.title or "Unknown",
            artist=audio_file.artist or "Unknown",
            bpm=audio_file.bpm or "Unknown",
            duration=int(audio_file.duration_seconds),
        )

    def _parse_response(self, response_text: str, audio_file: AudioFile) -> Optional[Track]:
        """Parse Gemini response into a Track object."""
        try:
            # Clean up response (remove markdown if present)
            text = response_text.strip()
            if text.startswith("```"):
                # Remove markdown code blocks (```json ... ```)
                # Find the first newline after ``` and the last ```
                start = text.find("\n") + 1
                end = text.rfind("```")
                if end > start:
                    text = text[start:end].strip()

            data = json.loads(text)

            # Convert key to Camelot if not already
            key = data.get("key", "8A")
            if not (len(key) >= 2 and key[-1] in "AB"):
                camelot = to_camelot(key)
                if camelot:
                    key = camelot
                else:
                    key = "8A"  # Default fallback

            # Build Track object
            track = Track(
                track_id=audio_file.file_hash,
                title=audio_file.title or "Unknown",
                artist=audio_file.artist or "Unknown",
                file_path=audio_file.file_path,
                rekordbox_id=audio_file.rekordbox_id,

                # Core audio
                bpm=data.get("bpm", audio_file.bpm or 120),
                key=key,
                duration_seconds=audio_file.duration_seconds,

                # Energy
                energy=data.get("energy", 5),
                danceability=data.get("danceability", 5),

                # Vibe
                vibe=data.get("vibe", "bright"),
                intensity=data.get("intensity", "journey"),
                mood_tags=data.get("mood_tags", []),

                # Rhythm
                groove_style=data.get("groove_style", "four-on-floor"),
                tempo_feel=data.get("tempo_feel", "straight"),

                # Mixability
                mix_in_ease=data.get("mix_in_ease", 5),
                mix_out_ease=data.get("mix_out_ease", 5),
                mixability_notes=data.get("mixability_notes"),

                # Vocals
                vocal_presence=data.get("vocal_presence", "group"),
                vocal_style=data.get("vocal_style", "singing"),
                language=data.get("language"),

                # Structure
                structure=data.get("structure", []),
                drop_intensity=data.get("drop_intensity"),

                # Production
                instrumentation=data.get("instrumentation", []),
                production_style=data.get("production_style"),

                # Quality
                production_quality=data.get("production_quality", 7),
                audio_fidelity=data.get("audio_fidelity", 7),

                # Genre
                genre=data.get("genre", "K-pop"),
                subgenre=data.get("subgenre"),
                similar_artists=data.get("similar_artists", []),

                # Description
                description=data.get("description", "No description available."),

                # Computed
                compatible_keys=compute_compatible_keys(key),

                # Timestamps
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            return track

        except json.JSONDecodeError as e:
            print(f"JSON Error for {audio_file.title}: {e}")
            print(f"Raw response:\n{response_text[:1000]}")
            return None
        except ValidationError as e:
            print(f"Validation Error for {audio_file.title}: {e}")
            return None

    async def analyze(self, audio_file: AudioFile) -> Optional[Track]:
        """Analyze a single audio file."""
        async with self._semaphore:
            await self._rate_limit()

            try:
                # Upload the audio file
                uploaded_file = genai.upload_file(
                    path=str(audio_file.file_path),
                    mime_type=f"audio/{audio_file.format}",
                )

                # Wait for processing
                while uploaded_file.state.name == "PROCESSING":
                    await asyncio.sleep(2)
                    uploaded_file = genai.get_file(uploaded_file.name)

                if uploaded_file.state.name == "FAILED":
                    print(f"Upload failed for {audio_file.title}")
                    return None

                # Generate analysis
                prompt = self._build_prompt(audio_file)
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    [uploaded_file, prompt],
                )

                # Clean up uploaded file
                try:
                    genai.delete_file(uploaded_file.name)
                except Exception:
                    pass

                return self._parse_response(response.text, audio_file)

            except Exception as e:
                import traceback
                print(f"Error analyzing {audio_file.title}: {e}")
                traceback.print_exc()
                return None

    async def analyze_batch(
        self,
        audio_files: list[AudioFile],
        progress_callback: Optional[callable] = None,
    ) -> list[Track]:
        """Analyze multiple audio files concurrently."""
        tracks: list[Track] = []
        total = len(audio_files)

        for i, audio_file in enumerate(audio_files):
            track = await self.analyze(audio_file)
            if track:
                tracks.append(track)

            if progress_callback:
                progress_callback(i + 1, total, audio_file.title, track is not None)

        return tracks

    def analyze_sync(self, audio_file: AudioFile) -> Optional[Track]:
        """Synchronous wrapper for analyze."""
        return asyncio.run(self.analyze(audio_file))

    def analyze_batch_sync(
        self,
        audio_files: list[AudioFile],
        progress_callback: Optional[callable] = None,
    ) -> list[Track]:
        """Synchronous wrapper for analyze_batch."""
        return asyncio.run(self.analyze_batch(audio_files, progress_callback))
