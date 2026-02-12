from __future__ import annotations

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
        self.scan_metrics: dict[str, Any] = {}
        self.start_time = datetime.datetime.now()

    def set_scan_metrics(self, metrics: dict[str, Any]) -> None:
        self.scan_metrics = metrics

    def add_entry(self, filename: str, ftype: str, size: int, offset: int, hash_sha256: str) -> None:
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
            "scan_metrics": self.scan_metrics,
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

        metrics_html = "".join(
            f"<li><strong>{key}:</strong> {value}</li>" for key, value in sorted(self.scan_metrics.items())
        )

        html_template = f"""
        <!DOCTYPE html>
        <html lang=\"es\">
        <head>
            <meta charset=\"UTF-8\">
            <title>Reporte UltraRecover Pro - {self.case_id}</title>
            <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background: #f4f7f6; }}
                .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                .summary {{ display: flex; justify-content: space-around; margin-bottom: 30px; gap: 20px; align-items: center; }}
                .card {{ background: #3498db; color: white; padding: 20px; border-radius: 5px; text-align: center; min-width: 150px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ padding: 12px; border: 1px solid #ddd; text-align: left; font-size: 14px; }}
                th {{ background-color: #2c3e50; color: white; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .hash {{ font-family: monospace; font-size: 12px; color: #e74c3c; }}
                .metrics {{ background: #eef6ff; border-left: 4px solid #3498db; padding: 12px; margin-top: 16px; }}
                .metrics ul {{ margin: 8px 0 0 20px; }}
            </style>
        </head>
        <body>
            <div class=\"container\">
                <h1>Informe Forense de Recuperación</h1>
                <p><strong>ID de Caso:</strong> {self.case_id} | <strong>Investigador:</strong> {self.investigator}</p>
                <p><strong>Fecha:</strong> {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}</p>

                <div class=\"summary\">
                    <div class=\"card\"><h3>{len(self.files_recovered)}</h3><p>Archivos</p></div>
                    <div style=\"width: 300px;\"><canvas id=\"typeChart\"></canvas></div>
                </div>

                <div class=\"metrics\">
                    <strong>Métricas operativas del escaneo</strong>
                    <ul>{metrics_html}</ul>
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
