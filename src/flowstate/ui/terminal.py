"""Rich terminal UI for live recommendations."""

from typing import Optional

from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..models import Corpus, Direction, Recommendations, ScoredTrack, Track
from ..engine import RecommendationEngine


class TerminalUI:
    """Interactive terminal UI for DJ recommendations."""

    def __init__(self, corpus: Corpus, engine: RecommendationEngine):
        self.corpus = corpus
        self.engine = engine
        self.console = Console()
        self.current_track: Optional[Track] = None
        self.recommendations: Optional[Recommendations] = None
        self.search_results: list[Track] = []
        self.search_mode = False
        self.search_query = ""

    def run(self):
        """Run the interactive UI."""
        self.console.clear()
        self.console.print("[bold cyan]FLOWSTATE[/bold cyan] - DJ Decision Support")
        self.console.print("[dim]Press 's' to search, 'q' to quit[/dim]\n")

        # Start with track selection
        self._search_mode()

    def _search_mode(self):
        """Interactive search mode."""
        while True:
            self.console.print("\n[bold]Search for a track:[/bold]")
            query = self.console.input("[cyan]> [/cyan]").strip()

            if query.lower() == "q":
                return

            if not query:
                # Show random tracks
                import random
                results = random.sample(self.corpus.tracks, min(10, len(self.corpus.tracks)))
            else:
                results = self.corpus.search(query)[:10]

            if not results:
                self.console.print("[yellow]No tracks found[/yellow]")
                continue

            # Display results
            self.console.print()
            for i, track in enumerate(results, 1):
                self.console.print(
                    f"  [cyan]{i:2d}[/cyan]. {track.title[:40]} - {track.artist[:20]} "
                    f"[dim]({track.bpm:.0f} BPM, {track.key}, E:{track.energy})[/dim]"
                )

            # Select track
            self.console.print("\n[dim]Enter number to select, or search again[/dim]")
            choice = self.console.input("[cyan]> [/cyan]").strip()

            if choice.lower() == "q":
                return

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(results):
                    self._select_track(results[idx])
            except ValueError:
                # Treat as new search
                if choice:
                    results = self.corpus.search(choice)[:10]
                    continue

    def _select_track(self, track: Track):
        """Select a track and show recommendations."""
        self.current_track = track
        self.recommendations = self.engine.recommend(track)

        self._show_recommendations()

    def _show_recommendations(self):
        """Display current track and recommendations."""
        if not self.current_track or not self.recommendations:
            return

        self.console.clear()

        # Current track header
        track = self.current_track
        self.console.print(Panel(
            f"[bold cyan]{track.title}[/bold cyan]\n"
            f"{track.artist}\n\n"
            f"[dim]{track.bpm:.0f} BPM[/dim] │ [dim]{track.key}[/dim] │ "
            f"Energy: [bold]{track.energy}[/bold] │ "
            f"Danceability: [bold]{track.danceability}[/bold] │ "
            f"{track.vibe}\n\n"
            f"[italic dim]{track.description}[/italic dim]",
            title="NOW PLAYING",
            border_style="cyan",
        ))

        # Recommendations
        self.console.print()
        self._show_direction("UP", self.recommendations.up, "green", "↑")
        self.console.print()
        self._show_direction("HOLD", self.recommendations.hold, "yellow", "→")
        self.console.print()
        self._show_direction("DOWN", self.recommendations.down, "red", "↓")

        # Controls
        self.console.print(f"\n[dim]Filtered {self.recommendations.filtered_count} candidates from {self.recommendations.candidates_considered} tracks[/dim]")
        self.console.print("\n[dim]Commands: [1-5] select track, [s]earch, [d]etails, [q]uit[/dim]")

        # Wait for input
        self._handle_input()

    def _show_direction(self, name: str, tracks: list[ScoredTrack], color: str, arrow: str):
        """Display recommendations for one direction."""
        header = f"[bold {color}]{arrow} {name}[/bold {color}]"

        if not tracks:
            self.console.print(f"{header} [dim]No recommendations[/dim]")
            return

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("#", style="dim", width=2)
        table.add_column("Title", style="cyan", width=35)
        table.add_column("Artist", width=20)
        table.add_column("BPM", justify="right", width=5)
        table.add_column("Key", width=4)
        table.add_column("E", justify="center", width=2)
        table.add_column("D", justify="center", width=2)
        table.add_column("Score", justify="right", width=5)
        table.add_column("Vibe", style="dim", width=10)

        for i, scored in enumerate(tracks[:5], 1):
            t = scored.track
            table.add_row(
                str(i),
                t.title[:35],
                t.artist[:20],
                f"{t.bpm:.0f}",
                t.key,
                str(t.energy),
                str(t.danceability),
                f"{scored.total_score:.2f}",
                t.vibe if isinstance(t.vibe, str) else t.vibe.value,
            )

        self.console.print(header)
        self.console.print(table)

    def _handle_input(self):
        """Handle user input in recommendation view."""
        while True:
            choice = self.console.input("\n[cyan]> [/cyan]").strip().lower()

            if choice == "q":
                return

            if choice == "s":
                self._search_mode()
                return

            if choice == "d":
                self._show_details()
                continue

            # Number selection (1-5 for each direction)
            if choice.startswith("u") and len(choice) == 2:
                try:
                    idx = int(choice[1]) - 1
                    if 0 <= idx < len(self.recommendations.up):
                        self._select_track(self.recommendations.up[idx].track)
                        return
                except ValueError:
                    pass

            if choice.startswith("h") and len(choice) == 2:
                try:
                    idx = int(choice[1]) - 1
                    if 0 <= idx < len(self.recommendations.hold):
                        self._select_track(self.recommendations.hold[idx].track)
                        return
                except ValueError:
                    pass

            if choice.startswith("d") and len(choice) == 2:
                try:
                    idx = int(choice[1]) - 1
                    if 0 <= idx < len(self.recommendations.down):
                        self._select_track(self.recommendations.down[idx].track)
                        return
                except ValueError:
                    pass

            # Simple number - assume UP direction
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self.recommendations.up):
                    self._select_track(self.recommendations.up[idx].track)
                    return
            except ValueError:
                pass

            self.console.print("[dim]Use: u1-u5 (up), h1-h5 (hold), d1-d5 (down), s (search), q (quit)[/dim]")

    def _show_details(self):
        """Show detailed scoring breakdown."""
        if not self.recommendations:
            return

        self.console.print("\n[bold]Score Breakdown (Top UP recommendation):[/bold]")

        if self.recommendations.up:
            scored = self.recommendations.up[0]
            self.console.print(f"\n{scored.track.title} - {scored.track.artist}")
            self.console.print(f"Total Score: [bold]{scored.total_score:.3f}[/bold]\n")

            for fs in sorted(scored.factor_scores, key=lambda x: -x.weighted_score):
                bar_len = int(fs.score * 20)
                bar = "█" * bar_len + "░" * (20 - bar_len)
                self.console.print(
                    f"  {fs.name:20s} [{bar}] {fs.score:.2f} × {fs.weight:.1f} = {fs.weighted_score:.2f}"
                )
                if fs.reason:
                    self.console.print(f"  [dim]{' ' * 20} {fs.reason}[/dim]")
