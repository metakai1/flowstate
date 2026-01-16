"""CLI command for writing metadata to WAV files."""

import subprocess
import shutil
from pathlib import Path

import click
from rich.console import Console

console = Console()


def write_riff_metadata(wav_path: Path, artist: str, title: str) -> bool:
    """Write RIFF INFO metadata using ffmpeg (Rekordbox-compatible)."""
    temp_path = wav_path.with_suffix(".tmp.wav")

    try:
        result = subprocess.run([
            "ffmpeg", "-y", "-i", str(wav_path),
            "-metadata", f"artist={artist}",
            "-metadata", f"title={title}",
            "-c", "copy",
            str(temp_path)
        ], capture_output=True, text=True)

        if result.returncode == 0 and temp_path.exists():
            shutil.move(str(temp_path), str(wav_path))
            return True
        else:
            if temp_path.exists():
                temp_path.unlink()
            return False
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        return False


@click.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option("--dry-run", is_flag=True, help="Show what would be done without writing")
def write_metadata(directory: str, dry_run: bool):
    """Write artist and title metadata to WAV files.

    Expects files named "Artist - Title.wav" format.
    Uses ffmpeg to write RIFF INFO chunks (Rekordbox-compatible).

    Example:
        flowstate write-metadata /mnt/c/Users/ssuta/Music/kpop
    """
    root = Path(directory)
    wav_files = list(root.rglob("*.wav"))

    if not wav_files:
        console.print(f"[yellow]No WAV files found in {directory}[/yellow]")
        return

    console.print(f"Found [cyan]{len(wav_files)}[/cyan] WAV files")

    success = 0
    failed = 0

    for wav_path in wav_files:
        filename = wav_path.stem  # Without extension

        # Parse "Artist - Title" format
        if " - " not in filename:
            console.print(f"[yellow]Skipping (no ' - ' separator):[/yellow] {wav_path.name}")
            failed += 1
            continue

        parts = filename.split(" - ", 1)
        artist = parts[0].strip()
        title = parts[1].strip() if len(parts) > 1 else filename

        if dry_run:
            console.print(f"[dim]Would write:[/dim] {artist} - {title}")
            success += 1
            continue

        if write_riff_metadata(wav_path, artist, title):
            console.print(f"[green]✓[/green] {artist} - {title}")
            success += 1
        else:
            console.print(f"[red]✗[/red] {wav_path.name}")
            failed += 1

    console.print()
    console.print(f"[green]Success:[/green] {success}  [red]Failed:[/red] {failed}")
