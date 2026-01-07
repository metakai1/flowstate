"""Audio file scanner using Mutagen."""

import hashlib
from pathlib import Path
from typing import Optional

from mutagen import File as MutagenFile
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis

from ..models import AudioFile

# Supported audio formats
SUPPORTED_FORMATS = {
    ".mp3", ".flac", ".m4a", ".aiff", ".aif",
    ".ogg", ".opus", ".wav",
}


def compute_file_hash(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Compute SHA256 hash of first 1MB of file."""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        data = f.read(chunk_size)
        sha256.update(data)
    return sha256.hexdigest()[:16]  # First 16 chars is enough


def extract_metadata(path: Path) -> Optional[AudioFile]:
    """Extract metadata from an audio file using Mutagen."""
    if not path.exists():
        return None

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        return None

    try:
        audio = MutagenFile(path)
        if audio is None:
            return None

        # Get duration
        duration = audio.info.length if audio.info else 0

        # Get sample rate and bitrate
        sample_rate = getattr(audio.info, "sample_rate", None)
        bitrate = getattr(audio.info, "bitrate", None)

        # Extract tags based on format
        title = None
        artist = None
        bpm = None
        key = None

        if isinstance(audio, MP3):
            try:
                tags = EasyID3(path)
                title = tags.get("title", [None])[0]
                artist = tags.get("artist", [None])[0]
                bpm_str = tags.get("bpm", [None])[0]
                if bpm_str:
                    try:
                        bpm = float(bpm_str)
                    except ValueError:
                        pass
            except Exception:
                pass

        elif isinstance(audio, FLAC):
            title = audio.get("title", [None])[0]
            artist = audio.get("artist", [None])[0]
            bpm_str = audio.get("bpm", [None])[0]
            if bpm_str:
                try:
                    bpm = float(bpm_str)
                except ValueError:
                    pass

        elif isinstance(audio, MP4):
            title = audio.tags.get("\xa9nam", [None])[0] if audio.tags else None
            artist = audio.tags.get("\xa9ART", [None])[0] if audio.tags else None
            # BPM in MP4 is stored differently
            tmpo = audio.tags.get("tmpo", [None])[0] if audio.tags else None
            if tmpo:
                try:
                    bpm = float(tmpo)
                except (ValueError, TypeError):
                    pass

        elif isinstance(audio, (OggOpus, OggVorbis)):
            title = audio.get("title", [None])[0]
            artist = audio.get("artist", [None])[0]
            bpm_str = audio.get("bpm", [None])[0]
            if bpm_str:
                try:
                    bpm = float(bpm_str)
                except ValueError:
                    pass

        # Fallback: try to extract from filename
        if not title or not artist:
            # Format: "Artist - Title.ext"
            stem = path.stem
            if " - " in stem:
                parts = stem.split(" - ", 1)
                if not artist:
                    artist = parts[0].strip()
                if not title:
                    title = parts[1].strip()
            else:
                if not title:
                    title = stem
                if not artist:
                    artist = "Unknown Artist"

        return AudioFile(
            file_path=path,
            file_hash=compute_file_hash(path),
            title=title,
            artist=artist,
            bpm=bpm,
            key=key,
            duration_seconds=duration,
            format=suffix[1:],  # Remove the dot
            bitrate=bitrate,
            sample_rate=sample_rate,
        )

    except Exception as e:
        print(f"Error reading {path}: {e}")
        return None


class AudioScanner:
    """Scan directories for audio files."""

    def __init__(self, supported_formats: set[str] | None = None):
        self.supported_formats = supported_formats or SUPPORTED_FORMATS

    def scan(self, path: Path | str, recursive: bool = True) -> list[AudioFile]:
        """
        Scan a directory for audio files.

        Args:
            path: Directory or file path
            recursive: If True, scan subdirectories

        Returns:
            List of AudioFile objects
        """
        path = Path(path)
        files: list[AudioFile] = []

        if path.is_file():
            audio_file = extract_metadata(path)
            if audio_file:
                files.append(audio_file)
            return files

        if not path.is_dir():
            return files

        # Scan directory
        pattern = "**/*" if recursive else "*"
        for file_path in path.glob(pattern):
            if not file_path.is_file():
                continue

            if file_path.suffix.lower() not in self.supported_formats:
                continue

            audio_file = extract_metadata(file_path)
            if audio_file:
                files.append(audio_file)

        # Sort by path for consistent ordering
        files.sort(key=lambda x: str(x.file_path))

        return files

    def scan_multiple(self, paths: list[Path | str], recursive: bool = True) -> list[AudioFile]:
        """Scan multiple directories/files."""
        all_files: list[AudioFile] = []
        seen_hashes: set[str] = set()

        for path in paths:
            for audio_file in self.scan(path, recursive):
                # Deduplicate by hash
                if audio_file.file_hash not in seen_hashes:
                    all_files.append(audio_file)
                    seen_hashes.add(audio_file.file_hash)

        return all_files
