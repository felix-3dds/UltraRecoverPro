import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import run_scan


def _load_report(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_run_scan_detects_multiple_jpegs_at_distinct_offsets(tmp_path: Path) -> None:
    evidence = tmp_path / "multiple_jpeg.img"
    payload = bytearray(os.urandom(3 * 1024 * 1024))

    first_offset = 128 * 1024
    second_offset = 2 * 1024 * 1024 + 321
    payload[first_offset : first_offset + 3] = b"\xff\xd8\xff"
    payload[second_offset : second_offset + 3] = b"\xff\xd8\xff"
    payload[-2:] = b"\xff\xd9"
    evidence.write_bytes(payload)

    detections, _, json_report = run_scan(str(evidence), str(tmp_path / "reports"), block_size=1024 * 1024)

    data = _load_report(json_report)
    offsets = [item["offset"] for item in data["files"] if item["type"] == "JPEG"]

    assert detections >= 2
    assert hex(first_offset) in offsets
    assert hex(second_offset) in offsets


def test_run_scan_small_block_size_and_overlap_deduplication(tmp_path: Path) -> None:
    evidence = tmp_path / "small_block.img"
    block_size = 4 * 1024
    payload = bytearray(os.urandom(20 * 1024))

    signature_offset = block_size - 1
    payload[signature_offset : signature_offset + 3] = b"\xff\xd8\xff"
    payload[-2:] = b"\xff\xd9"
    evidence.write_bytes(payload)

    detections, _, json_report = run_scan(str(evidence), str(tmp_path / "reports"), block_size=block_size)

    data = _load_report(json_report)
    matched_offsets = [item["offset"] for item in data["files"] if item["type"] == "JPEG"]

    assert detections >= 1
    assert matched_offsets.count(hex(signature_offset)) == 1


def test_run_scan_handles_empty_and_too_small_images(tmp_path: Path) -> None:
    for filename, content in (("empty.img", b""), ("small.img", b"\xff\xd8")):
        evidence = tmp_path / filename
        evidence.write_bytes(content)

        detections, html_report, json_report = run_scan(
            str(evidence),
            str(tmp_path / f"reports_{filename}"),
            block_size=4 * 1024,
        )

        assert detections == 0
        assert Path(html_report).exists()
        data = _load_report(json_report)
        assert data["totals"]["files"] == 0


def test_run_scan_discards_invalid_jpeg_structure(tmp_path: Path) -> None:
    evidence = tmp_path / "invalid_jpeg.img"
    payload = bytearray(os.urandom(64 * 1024))

    payload[1024:1027] = b"\xff\xd8\xff"
    payload[-2:] = b"\x00\x00"
    evidence.write_bytes(payload)

    detections, _, json_report = run_scan(str(evidence), str(tmp_path / "reports"), block_size=4 * 1024)

    data = _load_report(json_report)
    assert detections == 0
    assert data["totals"]["files"] == 0
