"""CLI command for downloading music videos from YouTube."""

from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..models import Corpus

console = Console()


def search_and_download(artist: str, title: str, output_dir: Path, quality: str, dry_run: bool) -> bool:
    """Search YouTube and download video for a track."""
    import yt_dlp

    # Build search query - prefer official MVs
    query = f"ytsearch1:{artist} {title} official mv"

    # Quality format strings
    quality_formats = {
        "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
        "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best",
        "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best",
    }

    output_path = output_dir / f"{artist} - {title}.mp4"

    if dry_run:
        console.print(f"  [dim]Would search:[/dim] {query}")
        console.print(f"  [dim]Would save to:[/dim] {output_path}")
        return True

    ydl_opts = {
        "format": quality_formats.get(quality, quality_formats["1080p"]),
        "outtmpl": str(output_dir / f"{artist} - {title}.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "postprocessors": [{
            "key": "FFmpegMetadata",
            "add_metadata": True,
        }],
        "postprocessor_args": {
            "ffmpeg": ["-metadata", f"title={title}", "-metadata", f"artist={artist}"],
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([query])
        return True
    except Exception as e:
        console.print(f"  [red]Error:[/red] {e}")
        return False


@click.command()
@click.option("-c", "--corpus", "corpus_path", default="data/corpus.json", help="Corpus file")
@click.option("-o", "--output", "output_dir", required=True, type=click.Path(), help="Output directory for videos")
@click.option("--quality", type=click.Choice(["1080p", "720p", "480p"]), default="1080p", help="Video quality")
@click.option("--skip-existing", is_flag=True, help="Skip if video already exists")
@click.option("--dry-run", is_flag=True, help="Show what would be downloaded")
@click.option("--limit", type=int, default=0, help="Limit number of downloads (0=all)")
@click.option("--artist", "artist_filter", default="", help="Filter by artist name (contains)")
def download_videos(corpus_path: str, output_dir: str, quality: str, skip_existing: bool, dry_run: bool, limit: int, artist_filter: str):
    """Download music videos from YouTube for corpus tracks.

    Downloads videos in Rekordbox-compatible MP4 format.
    After downloading, manually link videos in Rekordbox using the LINK button.

    Example:
        flowstate download-videos -o /mnt/c/Users/ssuta/Music/kpop-videos
        flowstate download-videos -o ./videos --limit 5 --dry-run
    """
    corpus_file = Path(corpus_path)
    if not corpus_file.exists():
        console.print(f"[red]Corpus not found: {corpus_path}[/red]")
        raise SystemExit(1)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    corpus = Corpus.load(corpus_file)
    tracks = corpus.tracks

    # Filter by artist if specified
    if artist_filter:
        tracks = [t for t in tracks if artist_filter.lower() in t.artist.lower()]
        console.print(f"Filtered to [cyan]{len(tracks)}[/cyan] tracks matching '{artist_filter}'")

    # Apply limit
    if limit > 0:
        tracks = tracks[:limit]

    console.print(f"Processing [cyan]{len(tracks)}[/cyan] tracks")
    console.print(f"Output: [cyan]{output_path}[/cyan]")
    console.print(f"Quality: [cyan]{quality}[/cyan]")
    if dry_run:
        console.print("[yellow]DRY RUN - no downloads will occur[/yellow]")
    console.print()

    success = 0
    skipped = 0
    failed = 0

    for i, track in enumerate(tracks, 1):
        video_file = output_path / f"{track.artist} - {track.title}.mp4"

        console.print(f"[{i}/{len(tracks)}] {track.artist} - {track.title}")

        if skip_existing and video_file.exists():
            console.print("  [yellow]Skipped (exists)[/yellow]")
            skipped += 1
            continue

        if search_and_download(track.artist, track.title, output_path, quality, dry_run):
            if not dry_run:
                console.print("  [green]Downloaded[/green]")
            success += 1
        else:
            failed += 1

    console.print()
    console.print(f"[green]Success:[/green] {success}  [yellow]Skipped:[/yellow] {skipped}  [red]Failed:[/red] {failed}")

    if not dry_run and success > 0:
        console.print()
        console.print("[dim]Next steps:[/dim]")
        console.print("  1. Import videos into Rekordbox")
        console.print("  2. Load audio track to deck")
        console.print("  3. Drag video to same deck")
        console.print("  4. Click LINK button to associate")
