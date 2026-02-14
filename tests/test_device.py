import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from core.device import DiskManager


def test_read_exact_and_metadata(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence.img"
    evidence.write_bytes(b"ABCDEFGHIJ")

    manager = DiskManager(str(evidence), block_size=4)
    manager.open_device()
    try:
        sample = manager.read_exact(2, 4)
        assert sample.tobytes() == b"CDEF"
        sample.release()

        metadata = manager.get_device_metadata()
        assert metadata["size_bytes"] == 10
        assert metadata["block_size"] == 4
        assert metadata["source"].endswith("evidence.img")
    finally:
        manager.close()


def test_iter_segments_with_overlap(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence.img"
    evidence.write_bytes(b"0123456789")

    manager = DiskManager(str(evidence), block_size=4)
    manager.open_device()
    try:
        chunks = []
        for offset, segment in manager.iter_segments(overlap=1):
            chunks.append((offset, segment.tobytes()))
            segment.release()

        assert chunks == [
            (0, b"0123"),
            (3, b"3456"),
            (6, b"6789"),
            (9, b"9"),
        ]
    finally:
        manager.close()


def test_read_exact_rejects_invalid_ranges(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence.img"
    evidence.write_bytes(b"012345")

    manager = DiskManager(str(evidence), block_size=4)
    manager.open_device()
    try:
        with pytest.raises(ValueError):
            manager.read_exact(-1, 2)
        with pytest.raises(ValueError):
            manager.read_exact(0, -2)
        with pytest.raises(ValueError):
            manager.read_exact(4, 4)

        with pytest.raises(ValueError):
            list(manager.iter_segments(overlap=4))
    finally:
        manager.close()