import hashlib
import math
import struct
import zlib


class FileValidator:
    """
    Aplica métricas estadísticas y validación estructural para reducir falsos positivos.
    """

    @staticmethod
    def calculate_entropy(data: bytes) -> float:
        """Calcula la entropía de Shannon. Valores cercanos a 8 indican alta compresión/cifrado."""
        if not data:
            return 0.0
        occurences = [0] * 256
        for byte in data:
            occurences[byte] += 1

        entropy = 0.0
        for x in occurences:
            if x > 0:
                p_x = x / len(data)
                entropy -= p_x * math.log2(p_x)
        return entropy

    @staticmethod
    def check_entropy(data_chunk: bytes, threshold: float = 3.0) -> bool:
        """Descarta bloques con baja entropía (ej. ceros repetidos o basura)."""
        return FileValidator.calculate_entropy(data_chunk) > threshold

    @staticmethod
    def _validate_jpeg(file_bytes: bytes, tolerant: bool = False) -> bool:
        if not file_bytes.startswith(b"\xff\xd8"):
            return False

        stripped = file_bytes.rstrip(b"\x00")
        has_eoi = stripped.endswith(b"\xff\xd9")
        if not has_eoi and not tolerant:
            return False

        has_required_marker = any(marker in file_bytes for marker in (b"\xff\xc0", b"\xff\xc2", b"\xff\xdb"))
        return has_required_marker or tolerant

    @staticmethod
    def _validate_png(file_bytes: bytes, tolerant: bool = False) -> bool:
        if not file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return False

        pos = 8
        seen_iend = False

        while pos + 12 <= len(file_bytes):
            chunk_length = struct.unpack(">I", file_bytes[pos : pos + 4])[0]
            chunk_type = file_bytes[pos + 4 : pos + 8]
            data_start = pos + 8
            data_end = data_start + chunk_length
            crc_start = data_end
            crc_end = crc_start + 4

            if crc_end > len(file_bytes):
                return tolerant and seen_iend

            chunk_data = file_bytes[data_start:data_end]
            expected_crc = struct.unpack(">I", file_bytes[crc_start:crc_end])[0]
            actual_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
            if expected_crc != actual_crc and not tolerant:
                return False

            pos = crc_end
            if chunk_type == b"IEND":
                seen_iend = True
                break

        if not seen_iend:
            return False

        if pos != len(file_bytes) and not tolerant:
            return False

        return True

    @staticmethod
    def _validate_mp4(file_bytes: bytes, tolerant: bool = False) -> bool:
        if len(file_bytes) < 16:
            return False

        first_size = struct.unpack(">I", file_bytes[0:4])[0]
        first_type = file_bytes[4:8]
        if first_type != b"ftyp":
            return False

        if first_size == 1:
            if len(file_bytes) < 24:
                return False
            first_size = struct.unpack(">Q", file_bytes[8:16])[0]
            header_size = 16
        else:
            header_size = 8

        if first_size < header_size + 8 or first_size > len(file_bytes):
            return False

        major_brand = file_bytes[header_size : header_size + 4]
        if major_brand == b"\x00\x00\x00\x00":
            return False

        pos = 0
        reached_end = False
        while pos + 8 <= len(file_bytes):
            size = struct.unpack(">I", file_bytes[pos : pos + 4])[0]
            box_type = file_bytes[pos + 4 : pos + 8]
            header = 8

            if size == 0:
                reached_end = True
                pos = len(file_bytes)
                break

            if size == 1:
                if pos + 16 > len(file_bytes):
                    return tolerant
                size = struct.unpack(">Q", file_bytes[pos + 8 : pos + 16])[0]
                header = 16

            if size < header:
                return tolerant

            next_pos = pos + size
            if next_pos > len(file_bytes):
                return tolerant

            if box_type == b"ftyp" and pos != 0 and not tolerant:
                return False

            pos = next_pos
            if pos == len(file_bytes):
                reached_end = True
                break

        if not reached_end and not tolerant:
            return False

        return True

    @staticmethod
    def _validate_zip(file_bytes: bytes, tolerant: bool = False) -> bool:
        if len(file_bytes) < 22:
            return False

        search_start = max(0, len(file_bytes) - 65557)
        eocd_pos = file_bytes.rfind(b"PK\x05\x06", search_start)
        if eocd_pos == -1:
            return False

        if eocd_pos + 22 > len(file_bytes):
            return tolerant

        (
            disk_no,
            cd_start_disk,
            entries_disk,
            total_entries,
            cd_size,
            cd_offset,
            comment_len,
        ) = struct.unpack("<HHHHIIH", file_bytes[eocd_pos + 4 : eocd_pos + 22])

        eocd_end = eocd_pos + 22 + comment_len
        if eocd_end > len(file_bytes):
            return tolerant

        if not tolerant and (disk_no != 0 or cd_start_disk != 0 or entries_disk != total_entries):
            return False

        if cd_offset + cd_size > eocd_pos:
            return tolerant

        if cd_offset >= len(file_bytes):
            return tolerant

        cursor = cd_offset
        parsed_entries = 0
        cd_limit = cd_offset + cd_size

        while cursor + 46 <= min(cd_limit, len(file_bytes)) and parsed_entries < total_entries:
            if file_bytes[cursor : cursor + 4] != b"PK\x01\x02":
                return tolerant

            name_len = struct.unpack("<H", file_bytes[cursor + 28 : cursor + 30])[0]
            extra_len = struct.unpack("<H", file_bytes[cursor + 30 : cursor + 32])[0]
            comment_len = struct.unpack("<H", file_bytes[cursor + 32 : cursor + 34])[0]
            rel_offset = struct.unpack("<I", file_bytes[cursor + 42 : cursor + 46])[0]
            entry_size = 46 + name_len + extra_len + comment_len
            next_cursor = cursor + entry_size
            if next_cursor > cd_limit or next_cursor > len(file_bytes):
                return tolerant

            if rel_offset + 4 > len(file_bytes):
                return tolerant

            if file_bytes[rel_offset : rel_offset + 4] != b"PK\x03\x04" and not tolerant:
                return False

            parsed_entries += 1
            cursor = next_cursor

        if not tolerant and parsed_entries != total_entries:
            return False

        return True

    @staticmethod
    def validate_structure(file_bytes: bytes, file_type: str, tolerant: bool = False) -> bool:
        """Validación profunda según el tipo de archivo."""
        if file_type == "JPEG":
            return FileValidator._validate_jpeg(file_bytes, tolerant=tolerant)

        if file_type in {"ZIP", "DOCX"}:
            return FileValidator._validate_zip(file_bytes, tolerant=tolerant)

        if file_type == "PNG":
            return FileValidator._validate_png(file_bytes, tolerant=tolerant)

        if file_type == "MP4":
            return FileValidator._validate_mp4(file_bytes, tolerant=tolerant)

        return True

    @staticmethod
    def get_forensic_hash(data: bytes) -> str:
        """Genera SHA-256 para mantener la cadena de custodia."""
        return hashlib.sha256(data).hexdigest()
