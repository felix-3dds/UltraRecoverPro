import argparse
import logging
import time
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


def _sample_chunk(device: DiskManager, offset: int, max_size: int) -> bytes:
    remaining = max(0, device.size - offset)
    length = min(max_size, remaining)
    return bytes(device.get_segment(offset, length))


def run_scan(source: str, report_dir: str, block_size: int = 1024 * 1024) -> tuple[int, str, str]:
    dev = DiskManager(source, block_size=block_size)
    carver = DeepCarver(DEFAULT_SIGNATURES)
    dashboard = ForensicDashboard()
    reporter = ForensicReporter(case_id=Path(source).stem, investigator="UltraRecoverPro")
    overlap = max(len(signature["header"]) for signature in DEFAULT_SIGNATURES.values()) - 1
    previous_tail = b""
    started_at = time.perf_counter()

    detections = 0
    dev.open_device()
    try:
        for offset in range(0, dev.size, dev.block_size):
            chunk = bytes(dev.get_segment(offset, min(dev.block_size, dev.size - offset)))
            scan_chunk = previous_tail + chunk
            base_offset = offset - len(previous_tail)
            matches = carver.scan_buffer(scan_chunk)

            for match in matches:
                abs_offset = base_offset + match["offset"]
                # Solo descartamos coincidencias totalmente contenidas en el solapamiento
                # de la iteración anterior; así evitamos duplicados sin usar un set creciente.
                if abs_offset <= offset - overlap:
                    continue
                signature = match["signature"]
                file_type = match["type"]
                sample = _sample_chunk(dev, abs_offset, signature.get("max_size", dev.block_size))

                if not FileValidator.check_entropy(sample):
                    continue
                if not FileValidator.validate_structure(sample, file_type):
                    continue

                detections += 1
                dashboard.update_stats(file_type)
                reporter.add_entry(
                    filename=f"{file_type}_{detections:04d}",
                    ftype=file_type,
                    size=len(sample),
                    offset=abs_offset,
                    hash_sha256=FileValidator.get_forensic_hash(sample),
                )

            previous_tail = chunk[-overlap:] if overlap > 0 else b""
            progress = (offset + len(chunk)) / dev.size if dev.size else 1.0
            elapsed = max(time.perf_counter() - started_at, 1e-9)
            speed_mb_s = ((offset + len(chunk)) / (1024 * 1024)) / elapsed
            dashboard.render_layout(progress, speed=speed_mb_s)
    finally:
        dev.close()

    output = Path(report_dir)
    output.mkdir(parents=True, exist_ok=True)
    html_path = str(output / "forensic_report.html")
    json_path = str(output / "forensic_report.json")
    reporter.generate_html(html_path)
    reporter.export_json(json_path)
    return detections, html_path, json_path


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
