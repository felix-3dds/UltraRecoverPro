import datetime
import html
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
        template_path = Path(__file__).with_name("report_template.html")
        html_template = template_path.read_text(encoding="utf-8")

        escaped_case_id = html.escape(self.case_id)
        escaped_investigator = html.escape(self.investigator)
        rows = "".join(
            [
                (
                    "<tr><td>{name}</td><td>{type}</td><td>{size}</td>"
                    "<td>{offset}</td><td class='hash'>{hash}</td></tr>"
                ).format(
                    name=html.escape(item["name"]),
                    type=html.escape(item["type"]),
                    size=f"{item['size_kb']:.2f} KB",
                    offset=html.escape(item["offset"]),
                    hash=html.escape(item["hash"]),
                )
                for item in self.files_recovered
            ]
        )

        rendered_html = html_template.format(
            case_id=escaped_case_id,
            investigator=escaped_investigator,
            date=self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            total_files=len(self.files_recovered),
            rows=rows,
            chart_labels=json.dumps([html.escape(label) for label in stats.keys()], ensure_ascii=False),
            chart_data=json.dumps(list(stats.values())),
        )

        Path(output_path).write_text(rendered_html, encoding="utf-8")
