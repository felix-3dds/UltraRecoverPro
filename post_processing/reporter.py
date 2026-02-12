import datetime                                                   import json

class ForensicReporter:                                               """
    Genera reportes técnicos y ejecutivos en formato HTML.
    Incluye validación de integridad (Hashes) y estadísticas de distribución.
    """
                                                                      def __init__(self, case_id: str, investigator: str):
        self.case_id = case_id
        self.investigator = investigator
        self.files_recovered = []
        self.start_time = datetime.datetime.now()
                                                                      def add_entry(self, filename: str, ftype: str, size: int, offset: int, hash_sha256: str):
        """Añade un registro de archivo recuperado al informe."""
        self.files_recovered.append({
            "name": filename,
            "type": ftype,
            "size": f"{size / 1024:.2f} KB",                                  "offset": hex(offset),
            "hash": hash_sha256
        })

    def _generate_stats(self):
        """Calcula la distribución por tipo para el gráfico."""
        stats = {}
        for f in self.files_recovered:
            stats[f['type']] = stats.get(f['type'], 0) + 1
        return stats

    def generate_html(self, output_path: str):
        stats = self._generate_stats()

        html_template = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Reporte UltraRecover Pro - {self.case_id}</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background: #f4f7f6; }}
                .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                .summary {{ display: flex; justify-content: space-around; margin-bottom: 30px; }}
                .card {{ background: #3498db; color: white; padding: 20px; border-radius: 5px; text-align: center; min-width: 150px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ padding: 12px; border: 1px solid #ddd; text-align: left; font-size: 14px; }}
                th {{ background-color: #2c3e50; color: white; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .hash {{ font-family: monospace; font-size: 12px; color: #e74c3c; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Informe Forense de Recuperación</h1>
                <p><strong>ID de Caso:</strong> {self.case_id} | <strong>Investigador:</strong> {self.investigator}</p>
                <p><strong>Fecha:</strong> {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}</p>

                <div class="summary">
                    <div class="card"><h3>{len(self.files_recovered)}</h3><p>Archivos</p></div>
                    <div style="width: 300px;"><canvas id="typeChart"></canvas></div>
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
                    <tbody>
                        {"".join([f"<tr><td>{f['name']}</td><td>{f['type']}</td><td>{f['size']}</td><td>{f['offset']}</td><td class='hash'>{f['hash']}</td></tr>" for f in self.files_recovered])}
                    </tbody>
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

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_template)
        print(f"[Reporter] Informe generado con éxito en: {output_path}")
