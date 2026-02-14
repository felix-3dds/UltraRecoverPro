import logging


class MP4Repairer:
    """Reconstrucción básica de contenedores MPEG-4."""

    def __init__(self, corrupted_path: str):
        self.path = corrupted_path
        self.data: bytearray | None = None

    def load_data(self) -> None:
        with open(self.path, "rb") as file:
            self.data = bytearray(file.read())

    def find_atom(self, atom_type: bytes) -> int:
        """Busca la posición del átomo (offset del size field)."""
        if self.data is None:
            raise RuntimeError("Debe cargar datos antes de buscar átomos")
        position = self.data.find(atom_type)
        if position < 4:
            return -1
        return position - 4

    def fix_moov_at_end(self) -> bool:
        if self.data is None:
            raise RuntimeError("Debe cargar datos antes de reparar")

        moov_idx = self.find_atom(b"moov")
        if moov_idx == -1:
            logging.warning("[Repair] No se encontró el átomo moov en %s", self.path)
            return False

        logging.info("[Repair] Átomo moov detectado en offset %d. Re-indexando...", moov_idx)
        return True

    def repair_zip_structure(self) -> None:
        logging.info("[Repair] Reconstrucción ZIP no implementada aún")

    def save_recovered(self, output_path: str) -> None:
        if self.data is None:
            raise RuntimeError("No hay datos cargados para guardar")
        with open(output_path, "wb") as file:
            file.write(self.data)
        logging.info("[Repair] Archivo reparado guardado en: %s", output_path)


class FileRepairService:
    """Heurísticas robustas para intentar recuperar archivos parcialmente corruptos."""

    @staticmethod
    def _repair_jpeg(blob: bytes) -> bytes | None:
        start = blob.find(b"\xff\xd8")
        if start == -1:
            return None
        data = blob[start:]
        eoi = data.find(b"\xff\xd9", 2)
        if eoi != -1:
            return data[: eoi + 2]

        end = len(data)
        while end > 2 and data[end - 1] == 0:
            end -= 1
        core = data[:end] if end > 2 else data
        return core + b"\xff\xd9"

    @staticmethod
    def _repair_png(blob: bytes) -> bytes | None:
        signature = b"\x89PNG\r\n\x1a\n"
        start = blob.find(signature)
        if start == -1:
            return None
        data = blob[start:]
        iend = data.find(b"IEND")
        if iend == -1:
            return None
        end = iend + 8
        if end > len(data):
            return None
        return data[:end]

    @staticmethod
    def _repair_zip(blob: bytes) -> bytes | None:
        start = blob.find(b"PK\x03\x04")
        if start == -1:
            return None
        data = blob[start:]
        eocd = data.find(b"PK\x05\x06")
        if eocd == -1 or eocd + 22 > len(data):
            return None
        comment_len = int.from_bytes(data[eocd + 20:eocd + 22], "little")
        end = eocd + 22 + comment_len
        if end > len(data):
            return None
        return data[:end]

    @staticmethod
    def _repair_mp4(blob: bytes) -> bytes | None:
        ftyp = blob.find(b"ftyp")
        if ftyp == -1 or ftyp < 4:
            return None
        start = ftyp - 4
        data = blob[start:]
        # Conservador: requerimos presencia de al menos un átomo típico
        if b"mdat" not in data and b"moov" not in data:
            return None
        return data

    @staticmethod
    def repair_bytes(blob: bytes, file_type: str) -> bytes | None:
        repairers = {
            "JPEG": FileRepairService._repair_jpeg,
            "PNG": FileRepairService._repair_png,
            "ZIP": FileRepairService._repair_zip,
            "DOCX": FileRepairService._repair_zip,
            "MP4": FileRepairService._repair_mp4,
        }
        repairer = repairers.get(file_type)
        if repairer is None:
            return None
        try:
            repaired = repairer(blob)
            if repaired and len(repaired) > 0:
                return repaired
            return None
        except Exception as exc:
            logging.warning("[Repair] Falló reparación de %s: %s", file_type, exc)
            return None
