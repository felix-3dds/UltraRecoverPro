import math
import hashlib

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

        entropy = 0
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
    def validate_structure(file_bytes: bytes, file_type: str) -> bool:
        """
        Validación profunda según el tipo de archivo.
        """
        if file_type == 'JPEG':
            # Debe terminar en EOI (End of Image) \xff\xd9
            return file_bytes.rstrip(b'\x00').endswith(b'\xff\xd9')

        if file_type == 'ZIP' or file_type == 'DOCX':
            # Buscar el 'Central Directory End Record' signature
            return b'\x50\x4b\x05\x06' in file_bytes[-1024:]

        return True

    @staticmethod
    def get_forensic_hash(data: bytes) -> str:
        """Genera SHA-256 para mantener la cadena de custodia."""
        return hashlib.sha256(data).hexdigest()
