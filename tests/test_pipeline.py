import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import run_scan


def test_run_scan_generates_reports_with_metrics(tmp_path: Path) -> None:
    evidence = tmp_path / "sample.img"
    payload = bytearray(os.urandom(2 * 1024 * 1024))

    start = len(payload) - 7000
    payload[start : start + 3] = b"\xff\xd8\xff"
    payload[start + 3 : -2] = os.urandom(len(payload[start + 3 : -2]))
    payload[-2:] = b"\xff\xd9"

    evidence.write_bytes(payload)

    detections, html_report, json_report = run_scan(str(evidence), str(tmp_path / "reports"), block_size=1024 * 1024)

    assert detections >= 1
    assert Path(html_report).exists()
    assert Path(json_report).exists()

    data = json.loads(Path(json_report).read_text(encoding="utf-8"))
    assert data["totals"]["files"] >= 1
    assert any(item["type"] == "JPEG" for item in data["files"])
    assert data["scan_metrics"]["bytes_scanned"] == 2 * 1024 * 1024
    assert data["scan_metrics"]["valid_matches"] >= 1


def test_detects_signature_crossing_block_boundary(tmp_path: Path) -> None:
    evidence = tmp_path / "boundary.img"
    block_size = 1024
    payload = bytearray(os.urandom(3 * block_size))

    # Inserta JPEG header cruzando frontera de bloque: offsets 1022,1023,1024.
    payload[1022:1025] = b"\xff\xd8\xff"
    payload[1025:-2] = os.urandom(len(payload[1025:-2]))
    payload[-2:] = b"\xff\xd9"

    evidence.write_bytes(payload)

    detections, _, json_report = run_scan(str(evidence), str(tmp_path / "reports_boundary"), block_size=block_size)

    assert detections >= 1
    data = json.loads(Path(json_report).read_text(encoding="utf-8"))
    assert any(item["type"] == "JPEG" for item in data["files"])
