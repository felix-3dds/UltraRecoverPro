import datetime
import json
from pathlib import Path
from typing import Any


class ForensicReporter:
    """Genera reportes técnicos y ejecutivos en formato HTML + JSON."""

    def __init__(self, case_id: str, investigator: str):
        self.case_id = case_id
        self.investigator = investigator
        self.files_recovered: list[dict[str, Any]] = []
        self.start_time = datetime.datetime.now()

    def add_entry(self, filename: str, ftype: str, size: int, offset: int, hash_sha256: str) -> None:
        """Añade un registro de archivo recuperado al informe."""
        self.files_recovered.append(
            {
                "name": filename,
                "type": ftype,
                "size_bytes": size,
                "size_kb": round(size / 1024, 2),
                "offset": hex(offset),
                "hash": hash_sha256,
            }
        )

    def _generate_stats(self) -> dict[str, int]:
        stats: dict[str, int] = {}
        for recovered in self.files_recovered:
            ftype = recovered["type"]
            stats[ftype] = stats.get(ftype, 0) + 1
        return stats

    def export_json(self, output_path: str) -> None:
        payload = {
            "case_id": self.case_id,
            "investigator": self.investigator,
            "start_time": self.start_time.isoformat(),
            "totals": {
                "files": len(self.files_recovered),
                "by_type": self._generate_stats(),
            },
            "files": self.files_recovered,
        }
        Path(output_path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def generate_html(self, output_path: str) -> None:
        stats = self._generate_stats()
        rows = "".join(
            [
                (
                    "<tr><td>{name}</td><td>{type}</td><td>{size}</td>"
                    "<td>{offset}</td><td class='hash'>{hash}</td></tr>"
                ).format(
                    name=item["name"],
                    type=item["type"],
                    size=f"{item['size_kb']:.2f} KB",
                    offset=item["offset"],
                    hash=item["hash"],
                )
                for item in self.files_recovered
            ]
        )

        html_template = f"""
        <!DOCTYPE html>
        <html lang=\"es\">
        <head>
            <meta charset=\"UTF-8\">
            <title>Reporte UltraRecover Pro - {self.case_id}</title>
            <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background: linear-gradient(145deg, #f4f7f6, #ecf3ff); color: #1f2937; }}
                .container {{ max-width: 1100px; margin: 30px auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 10px 35px rgba(44,62,80,0.15); }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-top: 0; }}
                .summary {{ display: flex; gap: 16px; align-items: center; margin-bottom: 30px; flex-wrap: wrap; }}
                .card {{ background: linear-gradient(120deg, #3498db, #2563eb); color: white; padding: 20px; border-radius: 10px; text-align: center; min-width: 170px; }}
                .card h3 {{ margin: 0 0 8px 0; font-size: 2rem; }}
                .meta-grid {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit,minmax(170px,1fr)); margin: 14px 0 22px; }}
                .meta {{ background: #f3f7ff; border-radius: 8px; padding: 10px 12px; border: 1px solid #dbeafe; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ padding: 12px; border: 1px solid #ddd; text-align: left; font-size: 14px; }}
                th {{ background-color: #2c3e50; color: white; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .hash {{ font-family: monospace; font-size: 12px; color: #e74c3c; }}
            </style>
        </head>
        <body>
            <div class=\"container\">
                <h1>Informe Forense de Recuperación</h1>
                <div class="meta-grid">
                    <div class="meta"><strong>ID de Caso:</strong><br>{self.case_id}</div>
                    <div class="meta"><strong>Investigador:</strong><br>{self.investigator}</div>
                    <div class="meta"><strong>Fecha:</strong><br>{self.start_time.strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>

                <div class=\"summary\">
                    <div class=\"card\"><h3>{len(self.files_recovered)}</h3><p>Archivos</p></div>
                    <div style=\"width: 300px;\"><canvas id=\"typeChart\"></canvas></div>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>Nombre/ID</th>
                            <th>Tipo</th>
                            <th>Tamaño</th>
                            <th>Offset (Hex)</th>
                            <th>Hash SHA-256 (Cadena de Custodia)</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>

            <script>
                const ctx = document.getElementById('typeChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'doughnut',
                    data: {{
                        labels: {list(stats.keys())},
                        datasets: [{{
                            data: {list(stats.values())},
                            backgroundColor: ['#3498db', '#2ecc71', '#f1c40f', '#e74c3c', '#9b59b6']
                        }}]
                    }}
                }});
            </script>
        </body>
        </html>
        """

        Path(output_path).write_text(html_template, encoding="utf-8")
