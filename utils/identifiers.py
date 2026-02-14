import hashlib
import math

BytesLike = bytes | bytearray | memoryview
HASH_STREAMING_THRESHOLD = 1024 * 1024
HASH_STREAMING_CHUNK_SIZE = 1024 * 1024


class FileValidator:
    """
    Aplica métricas estadísticas y validación estructural para reducir falsos positivos.
    """

    @staticmethod
    def calculate_entropy(data: BytesLike) -> float:
        """Calcula la entropía de Shannon. Valores cercanos a 8 indican alta compresión/cifrado."""
        if not data:
            return 0.0
        occurences = [0] * 256
        for byte in data:
            occurences[byte] += 1

        entropy = 0.0
        size = len(data)
        for x in occurences:
            if x > 0:
                p_x = x / size
                entropy -= p_x * math.log2(p_x)
        return entropy

    @staticmethod
    def check_entropy(data_chunk: BytesLike, threshold: float = 3.0) -> bool:
        """Descarta bloques con baja entropía (ej. ceros repetidos o basura)."""
        return FileValidator.calculate_entropy(data_chunk) > threshold

    @staticmethod
    def _candidate_length(view: memoryview, file_type: str) -> int | None:
        """Intenta estimar el final real de un archivo embebido dentro de una ventana de bytes."""
        blob = view.tobytes()

        if file_type == "JPEG":
            if len(blob) < 2 or blob[:2] != b"\xff\xd8":
                return None
            eoi_index = blob.find(b"\xff\xd9", 2)
            return eoi_index + 2 if eoi_index != -1 else None

        if file_type == "PNG":
            if len(blob) < 8 or blob[:8] != b"\x89PNG\r\n\x1a\n":
                return None
            iend_index = blob.find(b"IEND", 8)
            return iend_index + 8 if iend_index != -1 else None

        if file_type in {"ZIP", "DOCX"}:
            eocd_index = blob.find(b"\x50\x4b\x05\x06")
            if eocd_index == -1 or eocd_index + 22 > len(blob):
                return None
            comment_len = int.from_bytes(blob[eocd_index + 20:eocd_index + 22], "little")
            end = eocd_index + 22 + comment_len
            return end if end <= len(blob) else None

        if file_type == "MP4":
            if b"ftyp" in blob[:4096]:
                return None
            return None

        return None

    @staticmethod
    def trim_to_structure(file_bytes: BytesLike, file_type: str) -> memoryview:
        """Devuelve una vista recortada al final estructural detectado cuando sea posible."""
        view = file_bytes if isinstance(file_bytes, memoryview) else memoryview(file_bytes)
        length = FileValidator._candidate_length(view, file_type)
        if length is None:
            return view
        return view[:length]

    @staticmethod
    def validate_structure(file_bytes: BytesLike, file_type: str) -> bool:
        """
        Validación profunda según el tipo de archivo.
        """
        view = file_bytes if isinstance(file_bytes, memoryview) else memoryview(file_bytes)
        blob = view.tobytes()

        if file_type == "JPEG":
            return len(blob) >= 4 and blob[:2] == b"\xff\xd8" and b"\xff\xd9" in blob[2:]

        if file_type in {"ZIP", "DOCX"}:
            return b"\x50\x4b\x05\x06" in blob

        if file_type == "PNG":
            header_ok = len(blob) >= 8 and blob[:8] == b"\x89PNG\r\n\x1a\n"
            return header_ok and b"IEND" in blob

        if file_type == "MP4":
            return b"ftyp" in blob[:4096]

        return True

    @staticmethod
    def get_forensic_hash(data: BytesLike) -> str:
        """Genera SHA-256 para mantener la cadena de custodia."""
        hasher = hashlib.sha256()
        if len(data) <= HASH_STREAMING_THRESHOLD:
            hasher.update(data)
            return hasher.hexdigest()

        view = data if isinstance(data, memoryview) else memoryview(data)
        for start in range(0, len(view), HASH_STREAMING_CHUNK_SIZE):
            hasher.update(view[start:start + HASH_STREAMING_CHUNK_SIZE])
        return hasher.hexdigest()
