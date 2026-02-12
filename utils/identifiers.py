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
    def validate_structure(file_bytes: BytesLike, file_type: str) -> bool:
        """
        Validación profunda según el tipo de archivo.
        """
        view = file_bytes if isinstance(file_bytes, memoryview) else memoryview(file_bytes)

        if file_type == "JPEG":
            # Debe terminar en EOI (End of Image) \xff\xd9
            end = len(view)
            while end > 0 and view[end - 1] == 0:
                end -= 1
            return end >= 2 and view[end - 2] == 0xFF and view[end - 1] == 0xD9

        if file_type == "ZIP" or file_type == "DOCX":
            # Buscar el 'Central Directory End Record' signature
            tail = view[-1024:].tobytes()
            return b"\x50\x4b\x05\x06" in tail

        if file_type == "PNG":
            header_ok = len(view) >= 8 and view[:8].tobytes() == b"\x89PNG\r\n\x1a\n"
            tail = view[-256:].tobytes()
            return header_ok and b"IEND" in tail

        if file_type == "MP4":
            return b"ftyp" in view[:32].tobytes()

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
