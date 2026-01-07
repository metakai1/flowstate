"""CLI commands for track analysis."""

from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

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

    # Analyze with Gemini
    console.print(f"\n[bold]Analyzing with Gemini 2.5 Pro...[/bold]")
    console.print(f"[dim]Estimated cost: ~${len(new_files) * 0.05:.2f}[/dim]\n")

    analyzer = GeminiAnalyzer()
    success_count = 0
    fail_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing...", total=len(new_files))

        def on_progress(current: int, total: int, title: str, success: bool):
            nonlocal success_count, fail_count
            if success:
                success_count += 1
                progress.update(task, description=f"[green]✓[/green] {title[:40]}")
            else:
                fail_count += 1
                progress.update(task, description=f"[red]✗[/red] {title[:40]}")
            progress.advance(task)

        tracks = analyzer.analyze_batch_sync(new_files, progress_callback=on_progress)

    # Add to corpus
    for track in tracks:
        corpus.add(track)

    # Save corpus
    corpus.save(output_path)

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
