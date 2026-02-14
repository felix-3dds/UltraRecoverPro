import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import run_scan
from utils.identifiers import FileValidator


def test_run_scan_generates_reports(tmp_path: Path) -> None:
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
    assert (tmp_path / "reports" / "forensic_report.csv").exists()

    data = json.loads(Path(json_report).read_text(encoding="utf-8"))
    assert data["totals"]["files"] >= 1
    assert data["files"][0]["type"] == "JPEG"


def test_run_scan_detects_signature_across_block_boundary(tmp_path: Path) -> None:
    evidence = tmp_path / "boundary.img"
    payload = bytearray(os.urandom(2 * 1024 * 1024))

    boundary = 1024 * 1024
    payload[boundary - 1 : boundary + 2] = b"\xff\xd8\xff"
    payload[boundary + 2 : -2] = os.urandom(len(payload[boundary + 2 : -2]))
    payload[-2:] = b"\xff\xd9"
    evidence.write_bytes(payload)

    detections, _, json_report = run_scan(str(evidence), str(tmp_path / "reports"), block_size=1024 * 1024)

    assert detections >= 1
    data = json.loads(Path(json_report).read_text(encoding="utf-8"))
    assert any(item["offset"] == hex(boundary - 1) for item in data["files"])


def test_memoryview_pipeline_and_json_report(tmp_path: Path) -> None:
    evidence = tmp_path / "memoryview.img"
    payload = bytearray(os.urandom(2 * 1024 * 1024))

    start = 1024 * 1024 + 128
    payload[start : start + 3] = b"\xff\xd8\xff"
    payload[start + 3 : -2] = os.urandom(len(payload[start + 3 : -2]))
    payload[-2:] = b"\xff\xd9"
    evidence.write_bytes(payload)

    detections, _, json_report = run_scan(str(evidence), str(tmp_path / "reports"), block_size=1024 * 1024)

    assert detections >= 1

    data = json.loads(Path(json_report).read_text(encoding="utf-8"))
    assert data["totals"]["files"] >= 1
    first = data["files"][0]
    assert isinstance(first["hash"], str)
    assert len(first["hash"]) == 64

    mem_payload = memoryview(payload)
    assert FileValidator.check_entropy(mem_payload)
    assert FileValidator.validate_structure(mem_payload[start:], "JPEG")
    assert len(FileValidator.get_forensic_hash(mem_payload)) == 64
