import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.identifiers import FileValidator


def test_validate_structure_rejects_invalid_jpeg() -> None:
    fake_jpeg = b"\xff\xd8\xff" + b"A" * 64 + b"\x00\x00"
    assert not FileValidator.validate_structure(fake_jpeg, "JPEG")


def test_validate_structure_accepts_minimal_mp4_ftyp_prefix() -> None:
    sample = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 32
    assert FileValidator.validate_structure(sample, "MP4")
