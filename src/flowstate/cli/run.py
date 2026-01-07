"""CLI command for running the live recommendation UI."""

from pathlib import Path

import click
from rich.console import Console

from ..models import Corpus
from ..engine import RecommendationEngine, ScoringConfig

console = Console()


@click.command()
@click.option("-c", "--corpus", "corpus_path", default="data/corpus.json", help="Corpus file")
@click.option("--ui", type=click.Choice(["terminal", "web"]), default="terminal", help="UI mode")
@click.option("--port", type=int, default=5000, help="Web UI port")
def run(corpus_path: str, ui: str, port: int):
    """Run the live recommendation UI.

    Example:
        flowstate run -c data/corpus.json
    """
    corpus_file = Path(corpus_path)
    if not corpus_file.exists():
        console.print(f"[red]Corpus not found: {corpus_path}[/red]")
        console.print("[dim]Run 'flowstate analyze' first to build a corpus[/dim]")
        raise SystemExit(1)

    corpus = Corpus.load(corpus_file)
    console.print(f"Loaded corpus with [cyan]{len(corpus.tracks)}[/cyan] tracks")

    if len(corpus.tracks) < 2:
        console.print("[red]Need at least 2 tracks in corpus[/red]")
        raise SystemExit(1)

    engine = RecommendationEngine(corpus, ScoringConfig())

    if ui == "terminal":
        from ..ui.terminal import TerminalUI
        terminal_ui = TerminalUI(corpus, engine)
        terminal_ui.run()
    else:
        console.print("[yellow]Web UI not yet implemented[/yellow]")
        raise SystemExit(1)
