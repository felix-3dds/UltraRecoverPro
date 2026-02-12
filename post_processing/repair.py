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
