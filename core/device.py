from __future__ import annotations

import logging
import mmap
import os


class DiskManager:
    """Acceso directo y seguro a dispositivos o imágenes forenses vía mmap."""

    def __init__(self, source_path: str, block_size: int = 4096):
        if block_size <= 0:
            raise ValueError("block_size debe ser mayor que 0")

        self.source_path = source_path
        self.block_size = block_size
        self.fd: int | None = None
        self.mapped_device: mmap.mmap | None = None
        self.size = 0

    def open_device(self) -> None:
        try:
            read_only_flags = os.O_RDONLY | (os.O_BINARY if os.name == "nt" else 0)
            self.fd = os.open(self.source_path, read_only_flags)
            self.size = os.lseek(self.fd, 0, os.SEEK_END)
            os.lseek(self.fd, 0, os.SEEK_SET)

            if self.size == 0:
                raise ValueError(f"La fuente forense está vacía: {self.source_path}")

            self.mapped_device = mmap.mmap(self.fd, 0, access=mmap.ACCESS_READ)
            logging.info("[Device] Mapeado exitoso: %s (%d bytes)", self.source_path, self.size)
        except Exception:
            self.close()
            logging.exception("[Device] Error crítico al acceder al disco")
            raise

    def get_segment(self, start_offset: int, length: int) -> memoryview:
        """Retorna una vista de memoria validada para evitar copias innecesarias."""
        if self.mapped_device is None:
            raise RuntimeError("El dispositivo no está abierto")
        if start_offset < 0:
            raise ValueError("start_offset no puede ser negativo")
        if length < 0:
            raise ValueError("length no puede ser negativo")

        end_offset = min(start_offset + length, self.size)
        return memoryview(self.mapped_device)[start_offset:end_offset]

    def close(self) -> None:
        if self.mapped_device is not None:
            self.mapped_device.close()
            self.mapped_device = None
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def __enter__(self) -> "DiskManager":
        self.open_device()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
