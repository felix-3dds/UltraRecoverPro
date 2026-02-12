from rich.console import Console
from rich.table import Table


class ForensicDashboard:
    """Interfaz para visualización de telemetría forense en consola."""

    def __init__(self):
        self.console = Console()
        self.stats = {"JPEG": 0, "PNG": 0, "MP4": 0, "ZIP": 0, "Otros": 0}

    def update_stats(self, file_type: str) -> None:
        if file_type in self.stats:
            self.stats[file_type] += 1
        else:
            self.stats["Otros"] += 1

    def render_layout(self, progress_val: float, speed: float) -> None:
        table = Table(title="UltraRecover Pro - Telemetría Forense")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="magenta")

        for ftype, count in self.stats.items():
            table.add_row(f"Archivos {ftype} detectados", str(count))

        table.add_row("Progreso", f"{progress_val * 100:.2f}%")
        table.add_row("Velocidad estimada", f"{speed:.2f} MB/s")

        self.console.clear()
        self.console.print(table)
