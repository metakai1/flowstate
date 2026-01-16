"""Rich terminal dashboard UI for live recommendations."""

import random
import sys
import tty
import termios
from datetime import datetime
from typing import Optional

from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from rich.columns import Columns

from ..models import Corpus, Direction, Recommendations, ScoredTrack, Track
from ..engine import RecommendationEngine


class Dashboard:
    """Live-updating DJ dashboard centered on the current track."""

    def __init__(self, corpus: Corpus, engine: RecommendationEngine, rekordbox_sync: bool = True):
        self.corpus = corpus
        self.engine = engine
        self.console = Console()
        self.current_track: Optional[Track] = None
        self.recommendations: Optional[Recommendations] = None
        self.set_history: list[Track] = []
        self.set_start_time: Optional[datetime] = None
        self.rekordbox_sync = rekordbox_sync
        self._rb_monitor = None
        self._rb_available = False

    def _render_header(self) -> Panel:
        """Render the header."""
        set_time = ""
        if self.set_start_time:
            elapsed = datetime.now() - self.set_start_time
            mins = int(elapsed.total_seconds() // 60)
            set_time = f"  │  Set: {mins}min | {len(self.set_history)} tracks"

        rb_status = "[green]●[/green] RB" if self._rb_available else "[dim]○[/dim] RB"
        time_str = datetime.now().strftime('%H:%M:%S')

        header_text = f"[bold cyan]FLOWSTATE[/bold cyan]  │  {rb_status}{set_time}  │  {time_str}"
        return Panel(header_text, box=box.SIMPLE, style="white on dark_blue")

    def _render_now_playing(self) -> Panel:
        """Render the current track panel."""
        if not self.current_track:
            return Panel(
                "[dim]No track selected - press [bold]s[/bold] to search[/dim]",
                title="[bold cyan]NOW PLAYING[/bold cyan]",
                border_style="cyan",
            )

        t = self.current_track
        vibe = t.vibe if isinstance(t.vibe, str) else t.vibe.value
        intensity = t.intensity if isinstance(t.intensity, str) else t.intensity.value

        # Build compact display
        lines = []
        lines.append(f"[bold white]{t.title}[/bold white]")
        lines.append(f"[cyan]{t.artist}[/cyan]")
        lines.append("")
        lines.append(f"[yellow]{t.bpm:.0f}[/yellow] BPM  │  Key [yellow]{t.key}[/yellow]  │  {int(t.duration_seconds//60)}:{int(t.duration_seconds%60):02d}")

        # Energy bar
        energy_bar = "█" * t.energy + "░" * (10 - t.energy)
        energy_color = "green" if t.energy >= 7 else "yellow" if t.energy >= 4 else "red"
        lines.append(f"Energy [{energy_color}]{energy_bar}[/{energy_color}] {t.energy}")

        # Vibe and intensity
        lines.append(f"[magenta]{vibe}[/magenta] │ [yellow]{intensity}[/yellow]")

        return Panel(
            "\n".join(lines),
            title="[bold cyan]NOW PLAYING[/bold cyan]",
            border_style="cyan",
        )

    def _render_track_info(self) -> Panel:
        """Render track analysis info."""
        if not self.current_track:
            return Panel("", title="INFO", border_style="blue")

        t = self.current_track
        groove = t.groove_style if isinstance(t.groove_style, str) else t.groove_style.value
        vocal = t.vocal_presence if isinstance(t.vocal_presence, str) else t.vocal_presence.value

        lines = []

        # Mixability
        lines.append(f"[bold]Mix:[/bold] In={t.mix_in_ease} Out={t.mix_out_ease}")
        if t.mixability_notes:
            lines.append(f"[dim]{t.mixability_notes[:60]}...[/dim]")

        # Character
        lines.append(f"[bold]Feel:[/bold] {groove} │ {t.tempo_feel}")
        lines.append(f"[bold]Vocals:[/bold] {vocal} │ {t.vocal_style}")

        # Structure
        if t.structure:
            struct = " → ".join(t.structure[:6])
            lines.append(f"[bold]Structure:[/bold] {struct}")

        # Description
        lines.append("")
        lines.append(f"[italic]{t.description[:100]}...[/italic]")

        return Panel(
            "\n".join(lines),
            title="[bold]ANALYSIS[/bold]",
            border_style="blue",
        )

    def _render_recommendations(self, name: str, tracks: list[ScoredTrack], color: str, arrow: str) -> Panel:
        """Render a recommendation panel."""
        if not tracks:
            return Panel(
                "[dim]No matches[/dim]",
                title=f"[bold {color}]{arrow} {name}[/bold {color}]",
                border_style=color,
            )

        table = Table(show_header=True, box=None, padding=(0, 1), expand=True)
        table.add_column("#", style="bold", width=2)
        table.add_column("Title", style="white", no_wrap=True)
        table.add_column("Artist", style="cyan", no_wrap=True)
        table.add_column("BPM", justify="right", width=4)
        table.add_column("Key", width=3)
        table.add_column("E", justify="center", width=2)
        table.add_column("Score", justify="right", width=5)

        for i, scored in enumerate(tracks[:5], 1):
            t = scored.track
            energy_delta = t.energy - (self.current_track.energy if self.current_track else 0)
            energy_style = "green" if energy_delta > 0 else "red" if energy_delta < 0 else "yellow"

            table.add_row(
                str(i),
                t.title[:20],
                t.artist[:12],
                f"{t.bpm:.0f}",
                t.key,
                Text(str(t.energy), style=energy_style),
                f"{scored.total_score:.2f}",
            )

        return Panel(
            table,
            title=f"[bold {color}]{arrow} {name}[/bold {color}] ({len(tracks)})",
            border_style=color,
        )

    def _render_footer(self) -> Panel:
        """Render the footer with controls."""
        controls = "[bold]s[/bold] search  │  [bold]1-5[/bold] UP  │  [bold]u/h/d[/bold]+# direction  │  [bold]r[/bold] refresh  │  [bold]q[/bold] quit"
        return Panel(controls, box=box.SIMPLE, style="dim")

    def _render_dashboard(self) -> Group:
        """Render the full dashboard as a simple vertical stack."""
        elements = []

        # Header
        elements.append(self._render_header())

        # Now playing + Info side by side using Columns
        now_playing = self._render_now_playing()
        track_info = self._render_track_info()
        elements.append(Columns([now_playing, track_info], equal=True, expand=True))

        # Recommendations in a row
        up_panel = self._render_recommendations("UP", self.recommendations.up if self.recommendations else [], "green", "↑")
        hold_panel = self._render_recommendations("HOLD", self.recommendations.hold if self.recommendations else [], "yellow", "→")
        down_panel = self._render_recommendations("DOWN", self.recommendations.down if self.recommendations else [], "red", "↓")
        elements.append(Columns([up_panel, hold_panel, down_panel], equal=True, expand=True))

        # Footer
        elements.append(self._render_footer())

        return Group(*elements)

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
                vibe = track.vibe if isinstance(track.vibe, str) else track.vibe.value
                self.console.print(
                    f"  [cyan]{i:2d}[/cyan]. {track.title[:30]:30s} - {track.artist[:15]:15s} "
                    f"[dim]{track.bpm:3.0f} {track.key:3s}[/dim] E={track.energy} {vibe}"
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
                    continue

    def _getch(self):
        """Get a single character from stdin without waiting for enter."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def _start_rekordbox_sync(self):
        """Start Rekordbox sync if available."""
        if not self.rekordbox_sync:
            return

        try:
            from ..integrations.rekordbox import RekordboxMonitor

            def on_track_change(track: Track):
                self._select_track(track)

            self._rb_monitor = RekordboxMonitor(
                self.corpus,
                on_track_change=on_track_change,
                poll_interval=2.0,
            )

            if self._rb_monitor.start():
                self._rb_available = True
                self.console.print("[green]✓[/green] Rekordbox sync enabled")
            else:
                self.console.print("[yellow]![/yellow] Rekordbox not available - using manual mode")

        except ImportError:
            self.console.print("[dim]Rekordbox integration not available[/dim]")
        except Exception as e:
            self.console.print(f"[yellow]Rekordbox sync error: {e}[/yellow]")

    def _stop_rekordbox_sync(self):
        """Stop Rekordbox monitoring."""
        if self._rb_monitor:
            self._rb_monitor.stop()
            self._rb_monitor = None

    def run(self):
        """Run the dashboard."""
        # Start Rekordbox sync
        self._start_rekordbox_sync()

        # Try to get current track from Rekordbox first
        if self._rb_available:
            try:
                from ..integrations.rekordbox import get_now_playing
                rb_track = get_now_playing(self.corpus)
                if rb_track:
                    self._select_track(rb_track)
                    self.console.print(f"[cyan]▶[/cyan] Synced: {rb_track.artist} - {rb_track.title}")
            except Exception:
                pass

        # If no track from Rekordbox, show search
        if not self.current_track:
            selected = self._show_search_popup()
            if selected:
                self._select_track(selected)
            elif not self.current_track:
                self._stop_rekordbox_sync()
                return

        # Main dashboard loop with Live display
        with Live(self._render_dashboard(), console=self.console, refresh_per_second=2, screen=True) as live:
            while True:
                try:
                    live.update(self._render_dashboard())

                    # Get keypress
                    key = self._getch()

                    if key == "q" or key == "\x03":  # q or Ctrl+C
                        break

                    elif key == "s":
                        live.stop()
                        selected = self._show_search_popup()
                        if selected:
                            self._select_track(selected)
                        live.start()

                    elif key == "r":
                        if self.current_track:
                            self.recommendations = self.engine.recommend(self.current_track)

                    elif key in "12345" and self.recommendations and self.recommendations.up:
                        idx = int(key) - 1
                        if idx < len(self.recommendations.up):
                            self._select_track(self.recommendations.up[idx].track)

                    elif key == "u":
                        num = self._getch()
                        if num in "12345" and self.recommendations and self.recommendations.up:
                            idx = int(num) - 1
                            if idx < len(self.recommendations.up):
                                self._select_track(self.recommendations.up[idx].track)

                    elif key == "h":
                        num = self._getch()
                        if num in "12345" and self.recommendations and self.recommendations.hold:
                            idx = int(num) - 1
                            if idx < len(self.recommendations.hold):
                                self._select_track(self.recommendations.hold[idx].track)

                    elif key == "d":
                        num = self._getch()
                        if num in "12345" and self.recommendations and self.recommendations.down:
                            idx = int(num) - 1
                            if idx < len(self.recommendations.down):
                                self._select_track(self.recommendations.down[idx].track)

                except KeyboardInterrupt:
                    break

        # Cleanup
        self._stop_rekordbox_sync()


# Keep old class for compatibility
class TerminalUI(Dashboard):
    """Alias for Dashboard."""
    pass
