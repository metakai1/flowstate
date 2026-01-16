"""Rekordbox integration for detecting currently playing tracks."""

import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional

from ..models import Corpus, Track


def _find_rekordbox_db() -> Optional[Path]:
    """Find Rekordbox database, including WSL access to Windows."""
    # Standard locations
    locations = []

    # Check if running in WSL
    is_wsl = os.path.exists("/proc/version") and "microsoft" in open("/proc/version").read().lower()

    if is_wsl:
        # Try to find Windows username
        # Common location: /mnt/c/Users/<username>/AppData/Roaming/Pioneer/rekordbox
        mnt_users = Path("/mnt/c/Users")
        if mnt_users.exists():
            for user_dir in mnt_users.iterdir():
                try:
                    if user_dir.is_dir() and user_dir.name not in ("Public", "Default", "Default User", "All Users"):
                        rb_path = user_dir / "AppData" / "Roaming" / "Pioneer" / "rekordbox"
                        try:
                            if rb_path.exists():
                                locations.append(rb_path)
                        except PermissionError:
                            pass
                except PermissionError:
                    pass

    # Native paths
    home = Path.home()
    if os.name == "nt":  # Windows
        locations.append(home / "AppData" / "Roaming" / "Pioneer" / "rekordbox")
    else:  # macOS/Linux
        locations.append(home / "Library" / "Pioneer" / "rekordbox")

    # Find master.db in any location
    for loc in locations:
        db_path = loc / "master.db"
        if db_path.exists():
            return db_path

    return None


class RekordboxMonitor:
    """Monitor Rekordbox for currently playing track changes."""

    def __init__(
        self,
        corpus: Corpus,
        on_track_change: Optional[Callable[[Track], None]] = None,
        poll_interval: float = 2.0,
    ):
        self.corpus = corpus
        self.on_track_change = on_track_change
        self.poll_interval = poll_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_track_id: Optional[str] = None
        self._rb = None
        self._db_available = False

    def _init_rekordbox(self) -> bool:
        """Initialize pyrekordbox connection."""
        try:
            from pyrekordbox import Rekordbox6Database
            import shutil
            import tempfile

            # First try our custom finder (handles WSL)
            db_path = _find_rekordbox_db()

            # Fall back to pyrekordbox's config
            if not db_path:
                from pyrekordbox.config import get_config
                config = get_config()
                db_path = Path(config.db_path) if config.db_path else None

            if not db_path or not db_path.exists():
                print(f"[Rekordbox] Database not found")
                return False

            print(f"[Rekordbox] Found database at {db_path}")

            # Copy database to temp location to avoid locking issues
            # (Rekordbox keeps the DB locked while running)
            self._temp_dir = tempfile.mkdtemp(prefix="flowstate_rb_")
            self._db_copy_path = Path(self._temp_dir) / "master.db"
            self._original_db_path = db_path

            try:
                shutil.copy2(db_path, self._db_copy_path)
                # Also copy WAL files if they exist for consistency
                wal_file = db_path.parent / "master.db-wal"
                shm_file = db_path.parent / "master.db-shm"
                if wal_file.exists():
                    shutil.copy2(wal_file, Path(self._temp_dir) / "master.db-wal")
                if shm_file.exists():
                    shutil.copy2(shm_file, Path(self._temp_dir) / "master.db-shm")
            except Exception as e:
                print(f"[Rekordbox] Error copying database: {e}")
                return False

            self._rb = Rekordbox6Database(self._db_copy_path)
            self._db_available = True
            return True

        except ImportError:
            print("[Rekordbox] pyrekordbox not installed")
            return False
        except Exception as e:
            print(f"[Rekordbox] Error initializing: {e}")
            return False

    def _get_recent_track(self) -> Optional[dict]:
        """Get the most recently played track from Rekordbox history."""
        if not self._rb:
            return None

        try:
            # Get recent history entries
            history = list(self._rb.get_history())
            if not history:
                return None

            # Get the most recent history playlist
            latest_history = history[-1]

            # Get songs from that history (note: capitalized attribute names in pyrekordbox)
            songs = list(latest_history.Songs)
            if not songs:
                return None

            # Get the most recent song
            latest_song = songs[-1]
            content = latest_song.Content

            if content:
                # Get key if available
                key_name = None
                if hasattr(content, 'Key') and content.Key:
                    key_name = content.Key.ScaleName

                return {
                    "title": content.Title or "Unknown",
                    "artist": content.ArtistName or "Unknown",
                    "file_path": getattr(content, 'FolderPath', None),
                    "bpm": getattr(content, 'BPM', None),
                    "key": key_name,
                    "rekordbox_id": str(content.ID),
                }

        except Exception as e:
            print(f"[Rekordbox] Error getting recent track: {e}")

        return None

    def _match_to_corpus(self, rb_track: dict) -> Optional[Track]:
        """Match a Rekordbox track to our corpus."""
        # Try matching by rekordbox_id first
        if rb_track.get("rekordbox_id"):
            for track in self.corpus.tracks:
                if track.rekordbox_id == rb_track["rekordbox_id"]:
                    return track

        # Try matching by file path (compare just the filename)
        if rb_track.get("file_path"):
            rb_path = Path(rb_track["file_path"])
            rb_filename = rb_path.stem.lower()  # Without extension
            for track in self.corpus.tracks:
                if track.file_path:
                    corpus_filename = Path(track.file_path).stem.lower()
                    if rb_filename == corpus_filename:
                        return track

        # Parse title - Rekordbox sometimes stores as "Artist - Title"
        rb_title = rb_track.get("title", "")
        rb_artist = rb_track.get("artist", "") or ""

        # Try to extract artist from title if it contains " - "
        if " - " in rb_title and (not rb_artist or rb_artist == "Unknown"):
            parts = rb_title.split(" - ", 1)
            rb_artist = parts[0]
            rb_title = parts[1] if len(parts) > 1 else rb_title

        title = rb_title.lower().strip()
        artist = rb_artist.lower().strip()

        for track in self.corpus.tracks:
            track_title = track.title.lower()
            track_artist = track.artist.lower()

            # Exact match
            if track_title == title and track_artist == artist:
                return track

            # Title exact match with artist contains
            if track_title == title:
                if artist in track_artist or track_artist in artist:
                    return track

            # Fuzzy match - title contains
            if title and (title in track_title or track_title in title):
                if artist and (artist in track_artist or track_artist in artist):
                    return track

        return None

    def _refresh_db_copy(self):
        """Refresh the database copy from the original."""
        if not hasattr(self, '_original_db_path') or not self._original_db_path:
            return False

        import shutil
        import sqlite3

        try:
            # Close current connection
            if self._rb:
                self._rb = None

            # Re-copy the database and WAL files
            shutil.copy2(self._original_db_path, self._db_copy_path)
            wal_file = self._original_db_path.parent / "master.db-wal"
            shm_file = self._original_db_path.parent / "master.db-shm"
            if wal_file.exists():
                shutil.copy2(wal_file, Path(self._temp_dir) / "master.db-wal")
            if shm_file.exists():
                shutil.copy2(shm_file, Path(self._temp_dir) / "master.db-shm")

            # Force WAL checkpoint to merge pending changes into main DB
            try:
                conn = sqlite3.connect(str(self._db_copy_path))
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.close()
            except Exception:
                pass  # If checkpoint fails, continue anyway

            # Reopen
            from pyrekordbox import Rekordbox6Database
            self._rb = Rekordbox6Database(self._db_copy_path)
            return True

        except Exception as e:
            print(f"[Rekordbox] Error refreshing database: {e}")
            return False

    def _poll_loop(self):
        """Background polling loop."""
        refresh_counter = 0
        while self._running:
            try:
                # Refresh database copy every 5 polls to catch new history
                refresh_counter += 1
                if refresh_counter >= 5:
                    self._refresh_db_copy()
                    refresh_counter = 0

                rb_track = self._get_recent_track()

                if rb_track:
                    # Create a simple ID from title+artist
                    track_id = f"{rb_track.get('artist', '')}:{rb_track.get('title', '')}"

                    if track_id != self._last_track_id:
                        self._last_track_id = track_id

                        # Match to corpus
                        matched = self._match_to_corpus(rb_track)

                        if matched and self.on_track_change:
                            self.on_track_change(matched)

            except Exception as e:
                print(f"[Rekordbox] Poll error: {e}")

            time.sleep(self.poll_interval)

    def start(self) -> bool:
        """Start monitoring Rekordbox."""
        if not self._init_rekordbox():
            return False

        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        """Stop monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None

        # Cleanup temp files
        self._cleanup()

    def _cleanup(self):
        """Clean up temporary files."""
        import shutil
        if hasattr(self, '_temp_dir') and self._temp_dir:
            try:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            except Exception:
                pass
            self._temp_dir = None

    def __del__(self):
        """Destructor to ensure cleanup."""
        self._cleanup()

    @property
    def is_available(self) -> bool:
        """Check if Rekordbox database is available."""
        return self._db_available


def get_now_playing(corpus: Corpus) -> Optional[Track]:
    """Get the currently playing track from Rekordbox (one-shot)."""
    monitor = RekordboxMonitor(corpus)
    if not monitor._init_rekordbox():
        return None

    try:
        rb_track = monitor._get_recent_track()
        if rb_track:
            return monitor._match_to_corpus(rb_track)
    finally:
        monitor._cleanup()

    return None
