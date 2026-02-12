from rich.console import Console
from rich.table import Table
import time


class ForensicDashboard:
    """Interfaz para visualización de telemetría forense en consola."""

    def __init__(self):
        self.console = Console()
        self.stats = {"JPEG": 0, "PNG": 0, "MP4": 0, "ZIP": 0, "Otros": 0}
        self._last_render = 0.0
        self._milestones = {0.10, 0.25, 0.50, 0.75, 1.0}
        self._rendered_milestones: set[float] = set()

    def update_stats(self, file_type: str) -> None:
        if file_type in self.stats:
            self.stats[file_type] += 1
        else:
            self.stats["Otros"] += 1

    def _pending_milestone(self, progress_val: float) -> bool:
        return any(
            progress_val >= milestone and milestone not in self._rendered_milestones
            for milestone in self._milestones
        )

    def _mark_milestones(self, progress_val: float) -> None:
        for milestone in self._milestones:
            if progress_val >= milestone:
                self._rendered_milestones.add(milestone)

    def render_layout(
        self,
        progress_val: float,
        current_speed: float,
        average_speed: float,
        eta_seconds: float | None,
    ) -> None:
        now = time.monotonic()
        hit_milestone = self._pending_milestone(progress_val)
        if not hit_milestone and progress_val < 1.0 and now - self._last_render < 0.2:
            return

        table = Table(title="UltraRecover Pro - Telemetría Forense")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="magenta")

        for ftype, count in self.stats.items():
            table.add_row(f"Archivos {ftype} detectados", str(count))

        table.add_row("Progreso", f"{progress_val * 100:.2f}%")
        table.add_row("Velocidad actual", f"{current_speed:.2f} MB/s")
        table.add_row("Velocidad promedio", f"{average_speed:.2f} MB/s")

        if eta_seconds is not None and eta_seconds >= 0:
            table.add_row("ETA aproximada", f"{eta_seconds:.1f} s")
        else:
            table.add_row("ETA aproximada", "N/A")

        self.console.clear()
        self.console.print(table)
        self._last_render = now
        if hit_milestone:
            self._mark_milestones(progress_val)
