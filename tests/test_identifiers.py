import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import io
import struct
import zipfile
import zlib

from utils.identifiers import FileValidator


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def _build_png() -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    return signature + _png_chunk(b"IHDR", ihdr_data) + _png_chunk(b"IEND", b"")


def _build_mp4() -> bytes:
    ftyp_payload = b"isom" + struct.pack(">I", 0x200) + b"isomiso2"
    ftyp = struct.pack(">I", 8 + len(ftyp_payload)) + b"ftyp" + ftyp_payload
    mdat_payload = b"\x00\x00\x00\x00"
    mdat = struct.pack(">I", 8 + len(mdat_payload)) + b"mdat" + mdat_payload
    return ftyp + mdat


def _build_zip() -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, mode="w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr("a.txt", "hello")
    return out.getvalue()


def test_validate_jpeg_requires_markers_and_eoi() -> None:
    valid = b"\xff\xd8\xff\xdb\x00\x04\x00\x00\xff\xd9"
    missing_marker = b"\xff\xd8" + b"A" * 16 + b"\xff\xd9"
    missing_eoi = b"\xff\xd8\xff\xdb\x00\x04\x00\x00"

    assert FileValidator.validate_structure(valid, "JPEG")
    assert not FileValidator.validate_structure(missing_marker, "JPEG")
    assert not FileValidator.validate_structure(missing_eoi, "JPEG")
    assert FileValidator.validate_structure(missing_eoi, "JPEG", tolerant=True)


def test_validate_png_checks_chunks_crc_and_iend() -> None:
    valid = _build_png()
    invalid_crc = bytearray(valid)
    invalid_crc[-1] ^= 0xFF
    truncated = valid[:-4]

    assert FileValidator.validate_structure(valid, "PNG")
    assert not FileValidator.validate_structure(bytes(invalid_crc), "PNG")
    assert not FileValidator.validate_structure(truncated, "PNG")


def test_validate_mp4_requires_complete_ftyp_and_box_offsets() -> None:
    valid = _build_mp4()
    bad_ftyp_size = bytearray(valid)
    bad_ftyp_size[0:4] = struct.pack(">I", 12)
    bad_second_box_size = bytearray(valid)
    bad_second_box_size[len(valid) - 12 : len(valid) - 8] = struct.pack(">I", 1000)

    assert FileValidator.validate_structure(valid, "MP4")
    assert not FileValidator.validate_structure(bytes(bad_ftyp_size), "MP4")
    assert not FileValidator.validate_structure(bytes(bad_second_box_size), "MP4")
    assert FileValidator.validate_structure(bytes(bad_second_box_size), "MP4", tolerant=True)


def test_validate_zip_checks_eocd_and_directory_offsets() -> None:
    valid = _build_zip()
    eocd_pos = valid.rfind(b"PK\x05\x06")
    assert eocd_pos != -1

    bad_cd_offset = bytearray(valid)
    bad_cd_offset[eocd_pos + 16 : eocd_pos + 20] = struct.pack("<I", len(valid) + 128)

    bad_cd_size = bytearray(valid)
    bad_cd_size[eocd_pos + 12 : eocd_pos + 16] = struct.pack("<I", len(valid))

    assert FileValidator.validate_structure(valid, "ZIP")
    assert not FileValidator.validate_structure(bytes(bad_cd_offset), "ZIP")
    assert not FileValidator.validate_structure(bytes(bad_cd_size), "ZIP")
    assert FileValidator.validate_structure(bytes(bad_cd_size), "ZIP", tolerant=True)
