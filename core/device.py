import os
import mmap
import logging

class DiskManager:
    """
    Gestiona el acceso directo a dispositivos o imágenes forenses.    Implementa mmap para permitir Zero-Copy I/O en los motores de escaneo.
    """
    def __init__(self, source_path: str, block_size: int = 4096):
        self.source_path = source_path
        self.block_size = block_size
        self.fd = None
        self.mapped_device = None
        self.size = 0

    def open_device(self):
        try:
            # Abrir en modo lectura binaria
            self.fd = os.open(self.source_path, os.O_RDONLY | (os.O_BINARY if os.name == 'nt' else 0))
            self.size = os.lseek(self.fd, 0, os.SEEK_END)

            # Mapeo de memoria: permite tratar el disco como un array gigante
            # prot=PROT_READ asegura integridad forense (solo lectura)
            self.mapped_device = mmap.mmap(self.fd, 0, access=mmap.ACCESS_READ)
            logging.info(f"[Device] Mapeado exitoso: {self.source_path} ({self.size} bytes)")
        except Exception as e:
            logging.error(f"[Device] Error crítico al acceder al disco: {e}")
            raise

    def get_segment(self, start_offset: int, length: int):
        """Retorna una vista (memoryview) para evitar copias de datos."""
        return memoryview(self.mapped_device)[start_offset:start_offset + length]

    def close(self):
        if self.mapped_device:
            self.mapped_device.close()
        if self.fd:
            os.close(self.fd)
