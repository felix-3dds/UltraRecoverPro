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
                "offset_int": offset,
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
        data = json.dumps(self.files_recovered, ensure_ascii=False)
        labels = json.dumps(list(stats.keys()), ensure_ascii=False)
        values = json.dumps(list(stats.values()))

        html_template = f"""
        <!DOCTYPE html>
        <html lang=\"es\">
        <head>
            <meta charset=\"UTF-8\">
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
            <title>Reporte UltraRecover Pro - {self.case_id}</title>
            <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>
            <style>
                :root {{
                    --bg-start: #f4f7f6;
                    --bg-end: #ecf3ff;
                    --container-bg: #ffffff;
                    --text-main: #111827;
                    --text-soft: #374151;
                    --primary: #2563eb;
                    --border: #d1d5db;
                    --header-bg: #1f2937;
                    --header-text: #ffffff;
                    --row-alt: #f8fafc;
                    --field-bg: #f9fafb;
                    --card-bg: linear-gradient(120deg, #2563eb, #1d4ed8);
                    --focus-ring: #f59e0b;
                }}
                body.dark {{
                    --bg-start: #0f172a;
                    --bg-end: #111827;
                    --container-bg: #111827;
                    --text-main: #e5e7eb;
                    --text-soft: #d1d5db;
                    --primary: #60a5fa;
                    --border: #334155;
                    --header-bg: #020617;
                    --header-text: #f8fafc;
                    --row-alt: #1f2937;
                    --field-bg: #0b1220;
                    --card-bg: linear-gradient(120deg, #1d4ed8, #1e3a8a);
                    --focus-ring: #fbbf24;
                }}
                * {{ box-sizing: border-box; }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    background: linear-gradient(145deg, var(--bg-start), var(--bg-end));
                    color: var(--text-main);
                }}
                .container {{
                    max-width: 1200px;
                    margin: 30px auto;
                    background: var(--container-bg);
                    padding: 24px;
                    border-radius: 12px;
                    box-shadow: 0 10px 35px rgba(15, 23, 42, 0.25);
                }}
                h1 {{ color: var(--text-main); border-bottom: 2px solid var(--primary); padding-bottom: 10px; margin-top: 0; }}
                .toolbar {{ display: flex; flex-wrap: wrap; gap: 12px; align-items: end; margin-bottom: 16px; }}
                .field {{ display: grid; gap: 6px; min-width: 200px; }}
                label {{ font-weight: 600; color: var(--text-soft); }}
                input, select, button {{
                    border: 1px solid var(--border);
                    border-radius: 8px;
                    padding: 10px;
                    background: var(--field-bg);
                    color: var(--text-main);
                }}
                button {{ cursor: pointer; background: var(--primary); color: #fff; border: none; font-weight: 600; }}
                button:hover {{ filter: brightness(1.1); }}
                :focus-visible {{ outline: 3px solid var(--focus-ring); outline-offset: 2px; }}
                .summary {{
                    display: grid;
                    gap: 12px;
                    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
                    align-items: stretch;
                    margin-bottom: 20px;
                }}
                .card {{ background: var(--card-bg); color: #ffffff; padding: 16px; border-radius: 10px; min-height: 105px; }}
                .card h3 {{ margin: 0 0 8px 0; font-size: 1.75rem; }}
                .card p {{ margin: 0; }}
                .meta-grid {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit,minmax(170px,1fr)); margin: 14px 0 22px; }}
                .meta {{
                    background: var(--field-bg);
                    border-radius: 8px;
                    padding: 10px 12px;
                    border: 1px solid var(--border);
                    color: var(--text-soft);
                }}
                .table-wrap {{ max-height: 500px; overflow: auto; border: 1px solid var(--border); border-radius: 10px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{
                    padding: 12px;
                    border-bottom: 1px solid var(--border);
                    text-align: left;
                    font-size: 14px;
                    vertical-align: top;
                }}
                thead th {{ position: sticky; top: 0; background-color: var(--header-bg); color: var(--header-text); z-index: 2; }}
                th button.sort-btn {{ all: unset; cursor: pointer; color: inherit; font-weight: 700; }}
                tbody tr:nth-child(even) {{ background-color: var(--row-alt); }}
                .hash {{ font-family: monospace; font-size: 12px; color: #dc2626; word-break: break-all; }}
                body.dark .hash {{ color: #fca5a5; }}
                .pager {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; justify-content: space-between; margin-top: 12px; }}
                .pager-controls {{ display: flex; gap: 8px; align-items: center; }}
            </style>
        </head>
        <body>
            <div class=\"container\">
                <h1>Informe Forense de Recuperación</h1>
                <div class=\"meta-grid\">
                    <div class=\"meta\"><strong>ID de Caso:</strong><br>{self.case_id}</div>
                    <div class=\"meta\"><strong>Investigador:</strong><br>{self.investigator}</div>
                    <div class=\"meta\"><strong>Fecha:</strong><br>{self.start_time.strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>

                <div class=\"summary\">
                    <div class=\"card\"><h3>{len(self.files_recovered)}</h3><p>Archivos</p></div>
                    <div class=\"card\"><h3 id=\"totalRecoveredSize\">0 KB</h3><p>Tamaño total recuperado</p></div>
                    <div class=\"card\"><h3 id=\"topType\">N/A</h3><p>Top tipo de archivo</p></div>
                    <div class=\"card\"><h3 id=\"offsetRange\">N/A</h3><p>Offset mínimo/máximo</p></div>
                </div>

                <div style=\"display:grid;grid-template-columns:minmax(220px,320px) 1fr;gap:12px;align-items:center;margin:0 0 18px;\">
                    <div style=\"max-width:320px;\"><canvas id=\"typeChart\" aria-label=\"Distribución por tipo\" role=\"img\"></canvas></div>
                    <div class=\"toolbar\" role=\"region\" aria-label=\"Controles de tabla\">
                        <div class=\"field\">
                            <label for=\"typeFilter\">Filtrar por tipo</label>
                            <select id=\"typeFilter\"><option value=\"all\">Todos</option></select>
                        </div>
                        <div class=\"field\" style=\"flex:1;min-width:260px;\">
                            <label for=\"searchBox\">Buscar (hash / offset / nombre)</label>
                            <input id=\"searchBox\" type=\"search\" placeholder=\"Ej. jpg, 0x1000, a1b2...\" />
                        </div>
                        <div class=\"field\" style=\"min-width:130px;\">
                            <label for=\"pageSize\">Filas por página</label>
                            <select id=\"pageSize\">
                                <option value=\"25\">25</option>
                                <option value=\"50\" selected>50</option>
                                <option value=\"100\">100</option>
                            </select>
                        </div>
                        <div class=\"field\" style=\"min-width:150px;\">
                            <label for=\"themeToggle\">Tema</label>
                            <button id=\"themeToggle\" type=\"button\" aria-pressed=\"false\">Modo oscuro</button>
                        </div>
                    </div>
                </div>

                <div class=\"table-wrap\" role=\"region\" aria-label=\"Resultados recuperados\" tabindex=\"0\">
                    <table>
                        <thead>
                            <tr>
                                <th>Nombre/ID</th>
                                <th><button class=\"sort-btn\" data-sort=\"type\" aria-label=\"Ordenar por tipo\">Tipo ↕</button></th>
                                <th><button class=\"sort-btn\" data-sort=\"size_bytes\" aria-label=\"Ordenar por tamaño\">Tamaño ↕</button></th>
                                <th><button class=\"sort-btn\" data-sort=\"offset_int\" aria-label=\"Ordenar por offset\">Offset (Hex) ↕</button></th>
                                <th>Hash SHA-256 (Cadena de Custodia)</th>
                            </tr>
                        </thead>
                        <tbody id=\"resultsBody\"></tbody>
                    </table>
                </div>
                <div class=\"pager\">
                    <div id=\"pageInfo\" aria-live=\"polite\">Página 1 de 1</div>
                    <div class=\"pager-controls\">
                        <button id=\"prevPage\" type=\"button\">Anterior</button>
                        <button id=\"nextPage\" type=\"button\">Siguiente</button>
                    </div>
                </div>
            </div>

            <script>
                const records = {data};
                const state = {{
                    typeFilter: 'all',
                    search: '',
                    sortBy: 'offset_int',
                    sortDir: 'asc',
                    page: 1,
                    pageSize: 50,
                }};

                const body = document.getElementById('resultsBody');
                const typeFilter = document.getElementById('typeFilter');
                const searchBox = document.getElementById('searchBox');
                const pageSize = document.getElementById('pageSize');
                const prevPage = document.getElementById('prevPage');
                const nextPage = document.getElementById('nextPage');
                const pageInfo = document.getElementById('pageInfo');
                const themeToggle = document.getElementById('themeToggle');

                function formatSize(sizeBytes) {{
                    return `${{(sizeBytes / 1024).toFixed(2)}} KB`;
                }}

                function computeKPIs() {{
                    const totalSizeBytes = records.reduce((acc, item) => acc + item.size_bytes, 0);
                    document.getElementById('totalRecoveredSize').textContent = formatSize(totalSizeBytes);

                    const typeCounts = records.reduce((acc, item) => {{
                        acc[item.type] = (acc[item.type] || 0) + 1;
                        return acc;
                    }}, {{}});
                    const topType = Object.entries(typeCounts).sort((a, b) => b[1] - a[1])[0];
                    document.getElementById('topType').textContent = topType ? `${{topType[0]}} (${{topType[1]}})` : 'N/A';

                    if (records.length > 0) {{
                        const offsets = records.map((item) => item.offset_int);
                        const minOffset = Math.min(...offsets).toString(16);
                        const maxOffset = Math.max(...offsets).toString(16);
                        document.getElementById('offsetRange').textContent = `0x${{minOffset}} / 0x${{maxOffset}}`;
                    }}
                }}

                function getFilteredAndSorted() {{
                    const needle = state.search.trim().toLowerCase();
                    const filtered = records.filter((item) => {{
                        const typeMatch = state.typeFilter === 'all' || item.type === state.typeFilter;
                        const searchMatch = !needle
                            || item.name.toLowerCase().includes(needle)
                            || item.hash.toLowerCase().includes(needle)
                            || item.offset.toLowerCase().includes(needle);
                        return typeMatch && searchMatch;
                    }});

                    return filtered.sort((a, b) => {{
                        const valueA = a[state.sortBy];
                        const valueB = b[state.sortBy];
                        const order = state.sortDir === 'asc' ? 1 : -1;
                        if (typeof valueA === 'string') {{
                            return valueA.localeCompare(valueB) * order;
                        }}
                        return (valueA - valueB) * order;
                    }});
                }}

                function render() {{
                    const rows = getFilteredAndSorted();
                    const totalPages = Math.max(1, Math.ceil(rows.length / state.pageSize));
                    state.page = Math.min(state.page, totalPages);

                    const start = (state.page - 1) * state.pageSize;
                    const currentRows = rows.slice(start, start + state.pageSize);

                    body.innerHTML = '';
                    for (const item of currentRows) {{
                        const tr = document.createElement('tr');
                        tr.innerHTML = '<td></td><td></td><td></td><td></td><td class="hash"></td>';
                        tr.children[0].textContent = item.name;
                        tr.children[1].textContent = item.type;
                        tr.children[2].textContent = formatSize(item.size_bytes);
                        tr.children[3].textContent = item.offset;
                        tr.children[4].textContent = item.hash;
                        body.appendChild(tr);
                    }}

                    pageInfo.textContent = `Página ${{state.page}} de ${{totalPages}} · ${{rows.length}} coincidencias`;
                    prevPage.disabled = state.page <= 1;
                    nextPage.disabled = state.page >= totalPages;
                }}

                function fillTypeFilter() {{
                    const types = [...new Set(records.map((item) => item.type))].sort((a, b) => a.localeCompare(b));
                    for (const t of types) {{
                        const option = document.createElement('option');
                        option.value = t;
                        option.textContent = t;
                        typeFilter.appendChild(option);
                    }}
                }}

                function applyStoredTheme() {{
                    const darkMode = localStorage.getItem('report-theme') === 'dark';
                    document.body.classList.toggle('dark', darkMode);
                    themeToggle.textContent = darkMode ? 'Modo claro' : 'Modo oscuro';
                    themeToggle.setAttribute('aria-pressed', String(darkMode));
                }}

                const ctx = document.getElementById('typeChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'doughnut',
                    data: {{
                        labels: {labels},
                        datasets: [{{
                            data: {values},
                            backgroundColor: ['#3498db', '#2ecc71', '#f1c40f', '#e74c3c', '#9b59b6']
                        }}]
                    }}
                }});

                fillTypeFilter();
                computeKPIs();
                applyStoredTheme();
                render();

                typeFilter.addEventListener('change', (event) => {{
                    state.typeFilter = event.target.value;
                    state.page = 1;
                    render();
                }});
                searchBox.addEventListener('input', (event) => {{
                    state.search = event.target.value;
                    state.page = 1;
                    render();
                }});
                pageSize.addEventListener('change', (event) => {{
                    state.pageSize = Number(event.target.value);
                    state.page = 1;
                    render();
                }});
                prevPage.addEventListener('click', () => {{
                    if (state.page > 1) {{
                        state.page -= 1;
                        render();
                    }}
                }});
                nextPage.addEventListener('click', () => {{
                    state.page += 1;
                    render();
                }});
                for (const button of document.querySelectorAll('.sort-btn')) {{
                    button.addEventListener('click', () => {{
                        const key = button.dataset.sort;
                        if (state.sortBy === key) {{
                            state.sortDir = state.sortDir === 'asc' ? 'desc' : 'asc';
                        }} else {{
                            state.sortBy = key;
                            state.sortDir = 'asc';
                        }}
                        render();
                    }});
                }}
                themeToggle.addEventListener('click', () => {{
                    const darkMode = !document.body.classList.contains('dark');
                    localStorage.setItem('report-theme', darkMode ? 'dark' : 'light');
                    applyStoredTheme();
                }});
            </script>
        </body>
        </html>
        """

        Path(output_path).write_text(html_template, encoding="utf-8")
