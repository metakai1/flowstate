"""CLI commands for track analysis."""

import sys
from pathlib import Path

import click
from rich.console import Console

from ..analysis import AudioScanner, GeminiAnalyzer
from ..models import Corpus

console = Console()


@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("-o", "--output", default="data/corpus.json", help="Output corpus file")
@click.option("--append/--no-append", default=True, help="Append to existing corpus")
@click.option("--recursive/--no-recursive", default=True, help="Scan subdirectories")
@click.option("--dry-run", is_flag=True, help="Scan only, don't analyze")
@click.option("--max-tracks", type=int, default=None, help="Limit number of tracks to analyze")
def analyze(
    paths: tuple[str, ...],
    output: str,
    append: bool,
    recursive: bool,
    dry_run: bool,
    max_tracks: int | None,
):
    """Analyze audio tracks and build corpus.

    PATHS: One or more directories or files to scan.

    Example:
        flowstate analyze ~/Music/DJ/kpop/ -o data/corpus.json
    """
    if not paths:
        console.print("[red]Error: No paths provided[/red]")
        raise SystemExit(1)

    # Load existing corpus if appending
    output_path = Path(output)
    if append and output_path.exists():
        corpus = Corpus.load(output_path)
        console.print(f"[dim]Loaded existing corpus with {len(corpus.tracks)} tracks[/dim]")
    else:
        corpus = Corpus()

    # Scan for audio files
    scanner = AudioScanner()
    console.print(f"\n[bold]Scanning for audio files...[/bold]")

    audio_files = scanner.scan_multiple([Path(p) for p in paths], recursive=recursive)

    # Filter out already analyzed files
    existing_hashes = {t.track_id for t in corpus.tracks}
    new_files = [f for f in audio_files if f.file_hash not in existing_hashes]

    console.print(f"Found [cyan]{len(audio_files)}[/cyan] audio files")
    console.print(f"Already analyzed: [dim]{len(audio_files) - len(new_files)}[/dim]")
    console.print(f"New files to analyze: [cyan]{len(new_files)}[/cyan]")

    if max_tracks:
        new_files = new_files[:max_tracks]
        console.print(f"Limited to: [cyan]{len(new_files)}[/cyan] tracks")

    if not new_files:
        console.print("[yellow]No new files to analyze[/yellow]")
        return

    if dry_run:
        console.print("\n[bold]Files to analyze:[/bold]")
        for f in new_files:
            console.print(f"  • {f.artist} - {f.title}")
        console.print(f"\n[dim]Dry run - no analysis performed[/dim]")
        return

    # Analyze with Gemini - ONE AT A TIME with incremental saves
    console.print(f"\n[bold]Analyzing with Gemini 2.5 Pro...[/bold]")
    console.print(f"[dim]Estimated cost: ~${len(new_files) * 0.05:.2f}[/dim]")
    console.print(f"[dim]Saving after each track for robustness[/dim]\n")

    analyzer = GeminiAnalyzer()
    success_count = 0
    fail_count = 0
    total = len(new_files)

    for i, audio_file in enumerate(new_files, 1):
        # Progress indicator (works in background/non-TTY mode)
        pct = (i / total) * 100
        status_prefix = f"[{i:3d}/{total}] ({pct:5.1f}%)"

        # Flush output for real-time progress
        print(f"{status_prefix} Analyzing: {audio_file.artist} - {audio_file.title}...", end="", flush=True)

        try:
            track = analyzer.analyze_sync(audio_file)

            if track:
                corpus.add(track)
                corpus.save(output_path)  # Save after EACH successful track
                success_count += 1
                print(f" ✓", flush=True)
            else:
                fail_count += 1
                print(f" ✗ (parse error)", flush=True)

        except KeyboardInterrupt:
            print(f"\n\n[yellow]Interrupted! Saving progress...[/yellow]")
            corpus.save(output_path)
            console.print(f"Saved {len(corpus.tracks)} tracks to {output_path}")
            raise SystemExit(0)

        except Exception as e:
            fail_count += 1
            print(f" ✗ ({e})", flush=True)

    # Summary
    console.print(f"\n[bold]Analysis complete![/bold]")
    console.print(f"  Analyzed: [green]{success_count}[/green] tracks")
    if fail_count:
        console.print(f"  Failed: [red]{fail_count}[/red] tracks")
    console.print(f"  Total corpus: [cyan]{len(corpus.tracks)}[/cyan] tracks")
    console.print(f"  Saved to: [dim]{output_path}[/dim]")

    # Show stats
    stats = corpus.stats()
    if stats.low_fidelity_count > 0:
        console.print(f"\n[yellow]Warning: {stats.low_fidelity_count} tracks with low audio fidelity[/yellow]")
