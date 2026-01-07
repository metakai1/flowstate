"""CLI commands for corpus management."""

import csv
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ..models import Corpus

console = Console()


@click.group()
def corpus():
    """Manage the track corpus."""
    pass


@corpus.command()
@click.argument("corpus_path", type=click.Path(exists=True))
def stats(corpus_path: str):
    """Show corpus statistics.

    Example:
        flowstate corpus stats data/corpus.json
    """
    corpus_obj = Corpus.load(corpus_path)
    s = corpus_obj.stats()

    console.print(f"\n[bold]Corpus Statistics[/bold]")
    console.print(f"  Total tracks: [cyan]{s.total_tracks}[/cyan]")
    console.print(f"  BPM range: {s.bpm_min:.0f} - {s.bpm_max:.0f} (avg: {s.bpm_avg:.1f})")

    # Energy distribution
    console.print(f"\n[bold]Energy Distribution[/bold]")
    for energy in sorted(s.energy_distribution.keys()):
        count = s.energy_distribution[energy]
        bar = "█" * count
        console.print(f"  {energy:2d}: {bar} ({count})")

    # Vibe distribution
    console.print(f"\n[bold]Vibe Distribution[/bold]")
    table = Table(show_header=False, box=None)
    for vibe, count in sorted(s.vibe_distribution.items(), key=lambda x: -x[1]):
        pct = count / s.total_tracks * 100
        table.add_row(vibe, f"{count}", f"({pct:.0f}%)")
    console.print(table)

    # Intensity distribution
    console.print(f"\n[bold]Intensity Distribution[/bold]")
    for intensity, count in sorted(s.intensity_distribution.items()):
        console.print(f"  {intensity}: {count}")

    # Quality stats
    console.print(f"\n[bold]Quality[/bold]")
    console.print(f"  Avg production quality: {s.avg_production_quality:.1f}/10")
    console.print(f"  Avg audio fidelity: {s.avg_audio_fidelity:.1f}/10")
    if s.low_fidelity_count > 0:
        console.print(f"  [yellow]Low fidelity tracks: {s.low_fidelity_count}[/yellow]")

    # Vocal distribution
    console.print(f"\n[bold]Vocals[/bold]")
    for vocal, count in sorted(s.vocal_distribution.items(), key=lambda x: -x[1]):
        console.print(f"  {vocal}: {count}")


@corpus.command()
@click.argument("corpus_path", type=click.Path(exists=True))
@click.option("-o", "--output", default="data/corpus_review.csv", help="Output CSV file")
def export(corpus_path: str, output: str):
    """Export corpus to CSV for review.

    Example:
        flowstate corpus export data/corpus.json -o data/review.csv
    """
    corpus_obj = Corpus.load(corpus_path)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "title", "artist", "bpm", "key", "energy", "danceability",
        "vibe", "intensity", "groove_style", "vocal_presence",
        "production_quality", "audio_fidelity", "genre", "description",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for track in corpus_obj.tracks:
            row = {field: getattr(track, field, "") for field in fields}
            writer.writerow(row)

    console.print(f"Exported {len(corpus_obj.tracks)} tracks to [cyan]{output_path}[/cyan]")


@corpus.command()
@click.argument("corpus_path", type=click.Path(exists=True))
@click.option("-q", "--query", default="", help="Search query")
@click.option("--min-energy", type=int, help="Minimum energy")
@click.option("--max-energy", type=int, help="Maximum energy")
@click.option("--vibe", help="Filter by vibe")
@click.option("--limit", type=int, default=20, help="Max results")
def search(
    corpus_path: str,
    query: str,
    min_energy: int | None,
    max_energy: int | None,
    vibe: str | None,
    limit: int,
):
    """Search tracks in corpus.

    Example:
        flowstate corpus search data/corpus.json -q "BTS" --min-energy 7
    """
    corpus_obj = Corpus.load(corpus_path)

    results = corpus_obj.search(
        query=query,
        min_energy=min_energy,
        max_energy=max_energy,
        vibes=[vibe] if vibe else None,
    )[:limit]

    if not results:
        console.print("[yellow]No tracks found[/yellow]")
        return

    table = Table(title=f"Search Results ({len(results)} tracks)")
    table.add_column("Title", style="cyan")
    table.add_column("Artist")
    table.add_column("BPM")
    table.add_column("Key")
    table.add_column("E", justify="center")
    table.add_column("D", justify="center")
    table.add_column("Vibe")
    table.add_column("Intensity")

    for track in results:
        table.add_row(
            track.title[:30],
            track.artist[:20],
            f"{track.bpm:.0f}",
            track.key,
            str(track.energy),
            str(track.danceability),
            track.vibe if isinstance(track.vibe, str) else track.vibe.value,
            track.intensity if isinstance(track.intensity, str) else track.intensity.value,
        )

    console.print(table)


@corpus.command()
@click.argument("corpus_path", type=click.Path(exists=True))
@click.argument("track_id")
def show(corpus_path: str, track_id: str):
    """Show detailed track info.

    Example:
        flowstate corpus show data/corpus.json abc123
    """
    corpus_obj = Corpus.load(corpus_path)
    track = corpus_obj.get_by_id(track_id)

    if not track:
        # Try partial match
        for t in corpus_obj.tracks:
            if track_id.lower() in t.track_id.lower() or track_id.lower() in t.title.lower():
                track = t
                break

    if not track:
        console.print(f"[red]Track not found: {track_id}[/red]")
        return

    console.print(f"\n[bold cyan]{track.title}[/bold cyan]")
    console.print(f"[dim]{track.artist}[/dim]\n")

    console.print(f"[bold]Audio[/bold]")
    console.print(f"  BPM: {track.bpm:.1f} | Key: {track.key} | Duration: {track.duration_seconds:.0f}s")

    console.print(f"\n[bold]Energy[/bold]")
    console.print(f"  Energy: {track.energy}/10 | Danceability: {track.danceability}/10")

    console.print(f"\n[bold]Character[/bold]")
    console.print(f"  Vibe: {track.vibe} | Intensity: {track.intensity}")
    console.print(f"  Groove: {track.groove_style} | Tempo feel: {track.tempo_feel}")
    if track.mood_tags:
        console.print(f"  Mood: {', '.join(track.mood_tags)}")

    console.print(f"\n[bold]Vocals[/bold]")
    console.print(f"  Presence: {track.vocal_presence} | Style: {track.vocal_style}")
    if track.language:
        console.print(f"  Language: {track.language}")

    console.print(f"\n[bold]Mixability[/bold]")
    console.print(f"  Mix in: {track.mix_in_ease}/10 | Mix out: {track.mix_out_ease}/10")
    if track.mixability_notes:
        console.print(f"  Notes: {track.mixability_notes}")

    console.print(f"\n[bold]Production[/bold]")
    console.print(f"  Quality: {track.production_quality}/10 | Fidelity: {track.audio_fidelity}/10")
    if track.instrumentation:
        console.print(f"  Sounds: {', '.join(track.instrumentation)}")
    if track.production_style:
        console.print(f"  Style: {track.production_style}")

    console.print(f"\n[bold]Structure[/bold]")
    if track.structure:
        console.print(f"  {' → '.join(track.structure)}")
    if track.drop_intensity:
        console.print(f"  Drop intensity: {track.drop_intensity}/10")

    console.print(f"\n[bold]Genre[/bold]")
    console.print(f"  {track.genre}" + (f" / {track.subgenre}" if track.subgenre else ""))
    if track.similar_artists:
        console.print(f"  Similar to: {', '.join(track.similar_artists)}")

    console.print(f"\n[bold]Description[/bold]")
    console.print(f"  [italic]{track.description}[/italic]")

    console.print(f"\n[dim]ID: {track.track_id}[/dim]")
    console.print(f"[dim]Path: {track.file_path}[/dim]")
