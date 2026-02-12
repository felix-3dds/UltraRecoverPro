from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

class ForensicDashboard:
    """
    Interfaz profesional para la visualización de telemetría forense.
    """
    def __init__(self):
        self.console = Console()
        self.stats = {"JPEG": 0, "MP4": 0, "DOCX": 0, "Otros": 0}

    def update_stats(self, file_type: str):
        if file_type in self.stats:
            self.stats[file_type] += 1
        else:
            self.stats["Otros"] += 1

    def render_layout(self, progress_val: float, speed: float):
        table = Table(title="UltraRecover Pro - Telemetría Forense")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="magenta")

        for ftype, count in self.stats.items():
            table.add_row(f"Archivos {ftype} detectados", str(count))

        table.add_row("Velocidad actual", f"{speed:.2f} MB/s")

        self.console.clear()
        self.console.print(table)
