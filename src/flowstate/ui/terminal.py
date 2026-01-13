"""Rich terminal dashboard UI for live recommendations."""

import random
from datetime import datetime
from typing import Optional

from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from ..models import Corpus, Direction, Recommendations, ScoredTrack, Track
from ..engine import RecommendationEngine


class Dashboard:
    """Live-updating DJ dashboard."""

    def __init__(self, corpus: Corpus, engine: RecommendationEngine):
        self.corpus = corpus
        self.engine = engine
        self.console = Console()
        self.current_track: Optional[Track] = None
        self.recommendations: Optional[Recommendations] = None
        self.set_history: list[Track] = []
        self.set_start_time: Optional[datetime] = None

    def _make_layout(self) -> Layout:
        """Create the dashboard layout."""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )

        layout["main"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=2),
        )

        layout["left"].split_column(
            Layout(name="now_playing", ratio=2),
            Layout(name="set_info", ratio=1),
        )

        layout["right"].split_column(
            Layout(name="up", ratio=1),
            Layout(name="hold", ratio=1),
            Layout(name="down", ratio=1),
        )

        return layout

    def _render_header(self) -> Panel:
        """Render the header."""
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="right", ratio=1)

        grid.add_row(
            "[bold cyan]FLOWSTATE[/bold cyan]",
            f"[dim]Corpus: {len(self.corpus.tracks)} tracks[/dim]",
            f"[dim]{datetime.now().strftime('%H:%M:%S')}[/dim]",
        )

        return Panel(grid, style="white on dark_blue", box=box.SIMPLE)

    def _render_now_playing(self) -> Panel:
        """Render the current track panel."""
        if not self.current_track:
            return Panel(
                "[dim]No track selected\n\nPress [bold]s[/bold] to search[/dim]",
                title="[bold]NOW PLAYING[/bold]",
                border_style="cyan",
                box=box.ROUNDED,
            )

        t = self.current_track
        vibe = t.vibe if isinstance(t.vibe, str) else t.vibe.value

        # Energy bar
        energy_bar = "█" * t.energy + "░" * (10 - t.energy)
        dance_bar = "█" * t.danceability + "░" * (10 - t.danceability)

        content = Text()
        content.append(f"{t.title}\n", style="bold cyan")
        content.append(f"{t.artist}\n\n", style="dim")
        content.append(f"BPM: {t.bpm:.0f}  Key: {t.key}\n")
        content.append(f"Energy:      [{energy_bar}] {t.energy}\n", style="green" if t.energy >= 7 else "yellow" if t.energy >= 4 else "red")
        content.append(f"Danceability:[{dance_bar}] {t.danceability}\n", style="green" if t.danceability >= 7 else "yellow")
        content.append(f"\nVibe: {vibe} | {t.intensity}\n", style="magenta")

        if t.mixability_notes:
            content.append(f"\n[Mix tip] {t.mixability_notes[:60]}...\n", style="dim italic")

        return Panel(
            content,
            title="[bold]NOW PLAYING[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
        )

    def _render_set_info(self) -> Panel:
        """Render set history and stats."""
        lines = []

        if self.set_start_time:
            elapsed = datetime.now() - self.set_start_time
            mins = int(elapsed.total_seconds() // 60)
            lines.append(f"Set time: {mins} min")

        lines.append(f"Tracks played: {len(self.set_history)}")

        if self.set_history:
            lines.append("\n[dim]Recent:[/dim]")
            for track in self.set_history[-3:]:
                lines.append(f"  • {track.title[:25]}")

        return Panel(
            "\n".join(lines) if lines else "[dim]Set not started[/dim]",
            title="[bold]SET INFO[/bold]",
            border_style="blue",
            box=box.ROUNDED,
        )

    def _render_direction(self, name: str, tracks: list[ScoredTrack], color: str, arrow: str) -> Panel:
        """Render a recommendation direction panel."""
        if not tracks:
            return Panel(
                "[dim]No compatible tracks[/dim]",
                title=f"[bold {color}]{arrow} {name}[/bold {color}]",
                border_style=color,
                box=box.ROUNDED,
            )

        table = Table(show_header=True, box=None, padding=(0, 1), expand=True)
        table.add_column("#", style="dim", width=2)
        table.add_column("Title", style="cyan", no_wrap=True)
        table.add_column("Artist", no_wrap=True)
        table.add_column("BPM", justify="right", width=4)
        table.add_column("Key", width=3)
        table.add_column("E", justify="center", width=2)
        table.add_column("Score", justify="right", width=4)

        for i, scored in enumerate(tracks[:5], 1):
            t = scored.track
            energy_delta = t.energy - (self.current_track.energy if self.current_track else 0)
            energy_style = "green" if energy_delta > 0 else "red" if energy_delta < 0 else "yellow"

            table.add_row(
                str(i),
                t.title[:28],
                t.artist[:15],
                f"{t.bpm:.0f}",
                t.key,
                Text(str(t.energy), style=energy_style),
                f"{scored.total_score:.2f}",
            )

        return Panel(
            table,
            title=f"[bold {color}]{arrow} {name}[/bold {color}]",
            subtitle=f"[dim]{len(tracks)} options[/dim]",
            border_style=color,
            box=box.ROUNDED,
        )

    def _render_footer(self) -> Panel:
        """Render the footer with controls."""
        controls = (
            "[bold]s[/bold] search  "
            "[bold]1-5[/bold] select UP  "
            "[bold]u/h/d[/bold]+1-5 select direction  "
            "[bold]r[/bold] refresh  "
            "[bold]i[/bold] info  "
            "[bold]q[/bold] quit"
        )
        return Panel(controls, style="dim", box=box.SIMPLE)

    def _render_dashboard(self) -> Layout:
        """Render the full dashboard."""
        layout = self._make_layout()

        layout["header"].update(self._render_header())
        layout["now_playing"].update(self._render_now_playing())
        layout["set_info"].update(self._render_set_info())
        layout["footer"].update(self._render_footer())

        if self.recommendations:
            layout["up"].update(self._render_direction("UP", self.recommendations.up, "green", "↑"))
            layout["hold"].update(self._render_direction("HOLD", self.recommendations.hold, "yellow", "→"))
            layout["down"].update(self._render_direction("DOWN", self.recommendations.down, "red", "↓"))
        else:
            layout["up"].update(Panel("[dim]Select a track to see recommendations[/dim]", title="↑ UP", border_style="green"))
            layout["hold"].update(Panel("", title="→ HOLD", border_style="yellow"))
            layout["down"].update(Panel("", title="↓ DOWN", border_style="red"))

        return layout

    def _select_track(self, track: Track):
        """Select a track and update recommendations."""
        self.current_track = track
        self.recommendations = self.engine.recommend(track)

        # Add to history
        if not self.set_start_time:
            self.set_start_time = datetime.now()
        self.set_history.append(track)

    def _search_tracks(self, query: str) -> list[Track]:
        """Search for tracks."""
        if not query:
            return random.sample(self.corpus.tracks, min(10, len(self.corpus.tracks)))
        return self.corpus.search(query)[:10]

    def _show_search_popup(self) -> Optional[Track]:
        """Show search popup and return selected track."""
        self.console.clear()
        self.console.print("[bold cyan]FLOWSTATE[/bold cyan] - Search\n")

        while True:
            query = self.console.input("[bold]Search:[/bold] ").strip()

            if query.lower() == "q":
                return None

            results = self._search_tracks(query)

            if not results:
                self.console.print("[yellow]No tracks found. Try again.[/yellow]\n")
                continue

            self.console.print()
            for i, track in enumerate(results, 1):
                energy_bar = "█" * track.energy + "░" * (10 - track.energy)
                self.console.print(
                    f"  [cyan]{i:2d}[/cyan]. {track.title[:35]:35s} - {track.artist[:18]:18s} "
                    f"[dim]{track.bpm:3.0f} {track.key:3s}[/dim] [{energy_bar}]"
                )

            self.console.print("\n[dim]Enter number to select, new search, or 'q' to cancel[/dim]")
            choice = self.console.input("[cyan]> [/cyan]").strip()

            if choice.lower() == "q":
                return None

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(results):
                    return results[idx]
            except ValueError:
                if choice:
                    # Treat as new search query
                    query = choice
                    results = self._search_tracks(query)
                    continue

    def _show_track_info(self):
        """Show detailed track info popup."""
        if not self.current_track:
            return

        t = self.current_track
        self.console.clear()
        self.console.print(f"\n[bold cyan]{t.title}[/bold cyan]")
        self.console.print(f"[dim]{t.artist}[/dim]\n")

        self.console.print(f"[bold]Audio[/bold]")
        self.console.print(f"  BPM: {t.bpm:.1f} | Key: {t.key} | Duration: {t.duration_seconds:.0f}s")

        self.console.print(f"\n[bold]Energy & Feel[/bold]")
        self.console.print(f"  Energy: {t.energy}/10 | Danceability: {t.danceability}/10")
        self.console.print(f"  Vibe: {t.vibe} | Intensity: {t.intensity} | Groove: {t.groove_style}")

        self.console.print(f"\n[bold]Vocals[/bold]")
        self.console.print(f"  {t.vocal_presence} | {t.vocal_style} | {t.language or 'N/A'}")

        self.console.print(f"\n[bold]Mixability[/bold]")
        self.console.print(f"  In: {t.mix_in_ease}/10 | Out: {t.mix_out_ease}/10")
        if t.mixability_notes:
            self.console.print(f"  [italic]{t.mixability_notes}[/italic]")

        self.console.print(f"\n[bold]Production[/bold]")
        self.console.print(f"  Quality: {t.production_quality}/10 | Fidelity: {t.audio_fidelity}/10")
        if t.instrumentation:
            self.console.print(f"  Sounds: {', '.join(t.instrumentation[:5])}")

        self.console.print(f"\n[bold]Structure[/bold]")
        if t.structure:
            self.console.print(f"  {' → '.join(t.structure)}")
        if t.drop_intensity:
            self.console.print(f"  Drop: {t.drop_intensity}/10")

        self.console.print(f"\n[bold]Description[/bold]")
        self.console.print(f"  [italic]{t.description}[/italic]")

        if self.recommendations:
            self.console.print(f"\n[bold]Score Breakdown (Top UP pick):[/bold]")
            if self.recommendations.up:
                scored = self.recommendations.up[0]
                for fs in sorted(scored.factor_scores, key=lambda x: -x.weighted_score)[:5]:
                    bar = "█" * int(fs.score * 10) + "░" * (10 - int(fs.score * 10))
                    self.console.print(f"  {fs.name:18s} [{bar}] {fs.weighted_score:.2f}")

        self.console.input("\n[dim]Press Enter to return...[/dim]")

    def run(self):
        """Run the dashboard."""
        # Initial track selection
        selected = self._show_search_popup()
        if selected:
            self._select_track(selected)

        # Main dashboard loop
        with Live(self._render_dashboard(), console=self.console, refresh_per_second=1, screen=True) as live:
            while True:
                try:
                    # Non-blocking input check
                    import sys
                    import select

                    # Update display
                    live.update(self._render_dashboard())

                    # Check for input (with timeout)
                    if select.select([sys.stdin], [], [], 0.5)[0]:
                        key = sys.stdin.read(1)

                        if key == "q":
                            break

                        elif key == "s":
                            live.stop()
                            selected = self._show_search_popup()
                            if selected:
                                self._select_track(selected)
                            live.start()

                        elif key == "i":
                            live.stop()
                            self._show_track_info()
                            live.start()

                        elif key == "r":
                            if self.current_track:
                                self.recommendations = self.engine.recommend(self.current_track)

                        elif key in "12345" and self.recommendations and self.recommendations.up:
                            idx = int(key) - 1
                            if idx < len(self.recommendations.up):
                                self._select_track(self.recommendations.up[idx].track)

                        elif key == "u":
                            # Wait for number
                            num = sys.stdin.read(1)
                            if num in "12345" and self.recommendations and self.recommendations.up:
                                idx = int(num) - 1
                                if idx < len(self.recommendations.up):
                                    self._select_track(self.recommendations.up[idx].track)

                        elif key == "h":
                            num = sys.stdin.read(1)
                            if num in "12345" and self.recommendations and self.recommendations.hold:
                                idx = int(num) - 1
                                if idx < len(self.recommendations.hold):
                                    self._select_track(self.recommendations.hold[idx].track)

                        elif key == "d":
                            num = sys.stdin.read(1)
                            if num in "12345" and self.recommendations and self.recommendations.down:
                                idx = int(num) - 1
                                if idx < len(self.recommendations.down):
                                    self._select_track(self.recommendations.down[idx].track)

                except KeyboardInterrupt:
                    break


# Keep old class for compatibility
class TerminalUI(Dashboard):
    """Alias for Dashboard."""
    pass
