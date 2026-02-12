import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import run_scan
from utils.config_loader import get_runtime_signatures, load_config


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


def test_run_scan_loads_custom_signatures_file(tmp_path: Path) -> None:
    evidence = tmp_path / "custom.img"
    payload = bytearray(os.urandom(2 * 1024 * 1024))

    start = 1024 * 1024
    payload[start : start + 4] = b"\xde\xad\xbe\xef"
    payload[start + 4 :] = os.urandom(len(payload[start + 4 :]))
    evidence.write_bytes(payload)

    custom_config = tmp_path / "custom_signatures.json"
    custom_config.write_text(
        json.dumps(
            {
                "signatures": {
                    "DEAD": {"header": "deadbeef", "max_size": 65536},
                },
                "profiles": {
                    "fast": {"max_size_factor": 0.5, "validate_entropy": False, "validate_structure": False},
                    "balanced": {"max_size_factor": 1.0, "validate_entropy": False, "validate_structure": False},
                    "deep": {"max_size_factor": 2.0, "validate_entropy": True, "validate_structure": False},
                },
            }
        ),
        encoding="utf-8",
    )

    config = load_config(str(custom_config))
    signatures, profile = get_runtime_signatures(config, "balanced")
    detections, _, json_report = run_scan(
        str(evidence),
        str(tmp_path / "reports"),
        block_size=1024 * 1024,
        signatures=signatures,
        profile=profile,
    )

    assert detections >= 1
    data = json.loads(Path(json_report).read_text(encoding="utf-8"))
    assert any(item["type"] == "DEAD" for item in data["files"])
