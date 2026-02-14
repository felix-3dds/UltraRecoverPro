import datetime
import csv
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

    def add_entry(
        self,
        filename: str,
        ftype: str,
        size: int,
        offset: int,
        hash_sha256: str,
        recovered_path: str | None = None,
        repaired: bool = False,
    ) -> None:
        """Añade un registro de archivo recuperado al informe."""
        self.files_recovered.append(
            {
                "name": filename,
                "type": ftype,
                "size_bytes": size,
                "size_kb": round(size / 1024, 2),
                "offset": hex(offset),
                "hash": hash_sha256,
                "recovered_path": recovered_path,
                "repaired": repaired,
            }
        )

    def add_batch_entries(self, entries: list[dict[str, Any]]) -> None:
        """Ingiere múltiples entradas en una sola operación."""
        for entry in entries:
            self.add_entry(
                filename=str(entry["filename"]),
                ftype=str(entry["ftype"]),
                size=int(entry["size"]),
                offset=int(entry["offset"]),
                hash_sha256=str(entry["hash_sha256"]),
                recovered_path=str(entry.get("recovered_path")) if entry.get("recovered_path") else None,
                repaired=bool(entry.get("repaired", False)),
            )

    def _generate_stats(self) -> dict[str, int]:
        stats: dict[str, int] = {}
        for recovered in self.files_recovered:
            ftype = recovered["type"]
            stats[ftype] = stats.get(ftype, 0) + 1
        return stats

    def _generate_integrity_summary(self) -> dict[str, int]:
        hashes = [item["hash"] for item in self.files_recovered]
        return {
            "hashes_total": len(hashes),
            "hashes_unicos": len(set(hashes)),
            "hashes_duplicados": len(hashes) - len(set(hashes)),
        }

    def _bytes_recovered(self) -> int:
        return sum(item["size_bytes"] for item in self.files_recovered)

    def _human_size(self, size_bytes: int) -> str:
        units = ["B", "KB", "MB", "GB"]
        value = float(size_bytes)
        for unit in units:
            if value < 1024 or unit == units[-1]:
                return f"{value:.2f} {unit}"
            value /= 1024
        return f"{value:.2f} GB"

    def _rows_html(self) -> str:
        return "".join(
            [
                (
                    "<tr><td data-label='Nombre/ID'>{name}</td><td data-label='Tipo'>{type}</td>"
                    "<td data-label='Tamaño'>{size}</td><td data-label='Offset (Hex)'>{offset}</td>"
                    "<td data-label='Hash SHA-256' class='hash'>{hash}</td></tr>"
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

    def export_json(self, output_path: str) -> None:
        payload = {
            "case_id": self.case_id,
            "investigator": self.investigator,
            "start_time": self.start_time.isoformat(),
            "totals": {
                "files": len(self.files_recovered),
                "by_type": self._generate_stats(),
            },
            "integrity": self._generate_integrity_summary(),
            "files": self.files_recovered,
        }
        Path(output_path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def export_csv(self, output_path: str) -> None:
        """Exporta resultados tabulares para SIEM/BI o auditorías externas."""
        with Path(output_path).open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=["name", "type", "size_bytes", "size_kb", "offset", "hash"],
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(self.files_recovered)

    def generate_html(self, output_path: str) -> None:
        stats = self._generate_stats()
        integrity = self._generate_integrity_summary()
        bytes_recovered = self._bytes_recovered()
        template_path = Path(__file__).with_name("report_template.html")
        html_template = template_path.read_text(encoding="utf-8")

        escaped_case_id = html.escape(self.case_id)
        escaped_investigator = html.escape(self.investigator)
        rows = self._rows_html() or "<tr><td colspan='5'>No se detectaron archivos válidos.</td></tr>"

        rendered_html = html_template.format(
            case_id=escaped_case_id,
            investigator=escaped_investigator,
            date=self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            total_files=len(self.files_recovered),
            recovered_size=self._human_size(bytes_recovered),
            hash_total=integrity["hashes_total"],
            hash_unique=integrity["hashes_unicos"],
            hash_duplicates=integrity["hashes_duplicados"],
            rows=rows,
            chart_labels=json.dumps([html.escape(label) for label in stats.keys()], ensure_ascii=False),
            chart_data=json.dumps(list(stats.values())),
        )

        Path(output_path).write_text(rendered_html, encoding="utf-8")
