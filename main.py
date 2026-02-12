from __future__ import annotations

import argparse
import logging
import time
from dataclasses import dataclass
from pathlib import Path

from core.device import DiskManager
from engines.carver import DeepCarver
from post_processing.reporter import ForensicReporter
from ui.dashboard import ForensicDashboard
from utils.identifiers import FileValidator

DEFAULT_SIGNATURES = {
    "JPEG": {"header": b"\xff\xd8\xff", "max_size": 4 * 1024 * 1024},
    "PNG": {"header": b"\x89\x50\x4e\x47", "max_size": 4 * 1024 * 1024},
    "MP4": {"header": b"\x00\x00\x00\x18\x66\x74\x79\x70", "max_size": 8 * 1024 * 1024},
    "ZIP": {"header": b"\x50\x4b\x03\x04", "max_size": 4 * 1024 * 1024},
}


@dataclass
class ScanMetrics:
    scanned_bytes: int = 0
    blocks_scanned: int = 0
    raw_matches: int = 0
    valid_matches: int = 0
    duplicate_matches: int = 0
    rejected_entropy: int = 0
    rejected_structure: int = 0
    elapsed_seconds: float = 0.0


def _sample_chunk(device: DiskManager, offset: int, max_size: int) -> bytes:
    remaining = max(0, device.size - offset)
    return bytes(device.get_segment(offset, min(max_size, remaining)))


def run_scan(source: str, report_dir: str, block_size: int = 1024 * 1024) -> tuple[int, str, str]:
    carver = DeepCarver(DEFAULT_SIGNATURES)
    dashboard = ForensicDashboard()
    reporter = ForensicReporter(case_id=Path(source).stem, investigator="UltraRecoverPro")
    metrics = ScanMetrics()

    start_time = time.perf_counter()
    seen_offsets: set[tuple[int, str]] = set()
    overlap_len = max(carver.max_header_size - 1, 0)

    with DiskManager(source, block_size=block_size) as dev:
        for offset in range(0, dev.size, dev.block_size):
            block_length = min(dev.block_size, dev.size - offset)
            scan_length = min(block_length + overlap_len, dev.size - offset)
            scan_window = bytes(dev.get_segment(offset, scan_length))

            for match in carver.scan_buffer(scan_window):
                abs_offset = offset + match["offset"]
                if abs_offset >= offset + block_length:
                    continue

                metrics.raw_matches += 1
                file_type = match["type"]
                dedupe_key = (abs_offset, file_type)
                if dedupe_key in seen_offsets:
                    metrics.duplicate_matches += 1
                    continue
                seen_offsets.add(dedupe_key)

                signature = match["signature"]
                sample = _sample_chunk(dev, abs_offset, signature.get("max_size", dev.block_size))

                if not FileValidator.check_entropy(sample):
                    metrics.rejected_entropy += 1
                    continue
                if not FileValidator.validate_structure(sample, file_type):
                    metrics.rejected_structure += 1
                    continue

                metrics.valid_matches += 1
                dashboard.update_stats(file_type)
                reporter.add_entry(
                    filename=f"{file_type}_{metrics.valid_matches:04d}",
                    ftype=file_type,
                    size=len(sample),
                    offset=abs_offset,
                    hash_sha256=FileValidator.get_forensic_hash(sample),
                )

            metrics.blocks_scanned += 1
            metrics.scanned_bytes += block_length
            elapsed = max(time.perf_counter() - start_time, 1e-9)
            speed = (metrics.scanned_bytes / (1024 * 1024)) / elapsed
            progress = metrics.scanned_bytes / dev.size if dev.size else 1.0
            dashboard.render_layout(progress, speed)

    metrics.elapsed_seconds = time.perf_counter() - start_time

    output = Path(report_dir)
    output.mkdir(parents=True, exist_ok=True)
    html_path = str(output / "forensic_report.html")
    json_path = str(output / "forensic_report.json")

    reporter.set_scan_metrics(
        {
            "source": source,
            "block_size": block_size,
            "bytes_scanned": metrics.scanned_bytes,
            "blocks_scanned": metrics.blocks_scanned,
            "elapsed_seconds": round(metrics.elapsed_seconds, 4),
            "raw_matches": metrics.raw_matches,
            "valid_matches": metrics.valid_matches,
            "duplicate_matches": metrics.duplicate_matches,
            "rejected_entropy": metrics.rejected_entropy,
            "rejected_structure": metrics.rejected_structure,
        }
    )
    reporter.generate_html(html_path)
    reporter.export_json(json_path)

    return metrics.valid_matches, html_path, json_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="UltraRecoverPro forensic scanner")
    parser.add_argument("source", help="Ruta al disco o imagen forense")
    parser.add_argument("--report-dir", default="reports", help="Directorio de reportes de salida")
    parser.add_argument("--block-size", type=int, default=1024 * 1024, help="Tamaño de bloque en bytes")
    parser.add_argument("--log-level", default="INFO", help="Nivel de logging")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    detections, html_path, json_path = run_scan(args.source, args.report_dir, args.block_size)
    print(f"Análisis completado. Detecciones válidas: {detections}")
    print(f"Reporte HTML: {html_path}")
    print(f"Reporte JSON: {json_path}")


if __name__ == "__main__":
    main()
