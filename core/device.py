import os
import mmap
import logging
from pathlib import Path


class DiskManager:
    """
    Gestiona el acceso directo a dispositivos o imágenes forenses.
    Implementa mmap para permitir Zero-Copy I/O en los motores de escaneo.
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

    def read_exact(self, offset: int, size: int):
        """Lee exactamente `size` bytes desde `offset` validando límites."""
        if offset < 0 or size < 0:
            raise ValueError("offset y size deben ser valores no negativos")
        if offset + size > self.size:
            raise ValueError("El rango solicitado excede el tamaño del dispositivo")
        return self.get_segment(offset, size)

    def iter_segments(self, overlap: int = 0):
        """Itera segmentos de tamaño block_size con soporte opcional de solapamiento."""
        if overlap < 0:
            raise ValueError("overlap debe ser un valor no negativo")

        offset = 0
        while offset < self.size:
            length = min(self.block_size, self.size - offset)
            segment = self.get_segment(offset, length)
            yield offset, segment
            step = self.block_size - overlap
            if step <= 0:
                raise ValueError("overlap debe ser menor que block_size")
            offset += step

    def get_device_metadata(self) -> dict:
        """Retorna metadata básica útil para cadena de custodia."""
        stats = os.stat(self.source_path)
        return {
            "source": str(Path(self.source_path).resolve()),
            "size_bytes": self.size,
            "block_size": self.block_size,
            "inode": stats.st_ino,
            "device_id": stats.st_dev,
            "mtime_epoch": stats.st_mtime,
        }

    def close(self):
        if self.mapped_device:
            self.mapped_device.close()
        if self.fd:
            os.close(self.fd)
