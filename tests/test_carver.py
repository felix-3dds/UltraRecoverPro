import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engines.carver import DeepCarver


SIGNATURES = {
    "JPEG": {"header": b"\xff\xd8\xff", "max_size": 1024},
    "PNG": {"header": b"\x89PNG", "max_size": 1024},
}


def test_carver_finds_multiple_occurrences_of_same_signature() -> None:
    carver = DeepCarver(SIGNATURES)
    data = b"AA\xff\xd8\xffBB\xff\xd8\xffCC"

    matches = carver.scan_buffer(data)
    jpeg_offsets = [match["offset"] for match in matches if match["type"] == "JPEG"]

    assert jpeg_offsets == [2, 7]


def test_carver_requires_bytes_like_buffer() -> None:
    carver = DeepCarver(SIGNATURES)

    with pytest.raises(TypeError):
        carver.scan_buffer("not-bytes")
