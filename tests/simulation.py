import os
import random
import struct

class EvidenceGenerator:
    def __init__(self, filename="evidence.img", size_mb=100):
        self.filename = filename
        self.size = size_mb * 1024 * 1024
        self.signatures = {
            'jpg': b'\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46',
            'png': b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A',
            'zip': b'\x50\x4B\x03\x04',
            'mp3': b'\x49\x44\x33\x03\x00\x00\x00\x00\x00\x00',
            'mp4': b'\x00\x00\x00\x18\x66\x74\x79\x70\x69\x73\x6F\x6D'
        }

    def generate(self):
        print(f"[*] Creando imagen de evidencia: {self.filename} ({self.size // 1024 // 1024} MB)")

        # 1. Crear un archivo lleno de "basura" (alta entropía) y ceros (baja entropía)
        with open(self.filename, "wb") as f:
            # Llenamos con 10MB de ceros iniciales
            f.write(b'\x00' * (1024 * 1024 * 10))
            # El resto con datos aleatorios
            f.write(os.urandom(self.size - (1024 * 1024 * 10)))

        # 2. Inyectar archivos en posiciones específicas
        with open(self.filename, "r+b") as f:
            # Inyectar un JPG (Offset 1MB)
            self._inject(f, 1024*1024, self.signatures['jpg'] + os.urandom(5000) + b'\xFF\xD9')

            # Inyectar un PNG (Offset 5MB)
            self._inject(f, 5*1024*1024, self.signatures['png'] + os.urandom(3000))

            # Inyectar un ZIP (Offset 15MB)
            self._inject(f, 15*1024*1024, self.signatures['zip'] + b"CONTENIDO_SIMULADO" + b'\x50\x4B\x05\x06')

            # Inyectar un MP3 (Offset 20MB)
            self._inject(f, 20*1024*1024, self.signatures['mp3'] + os.urandom(8000))

            # Inyectar un MP4 Fragmentado (Simulación avanzada)
            # Cabecera ftyp en 30MB
            self._inject(f, 30*1024*1024, self.signatures['mp4'] + b"mdat" + os.urandom(15000))
            # Átomo moov (el índice) enterrado mucho más adelante en 40MB
            self._inject(f, 40*1024*1024, b'\x00\x00\x00\x20moov' + os.urandom(100))

        print("[+] Evidencia generada. Los archivos están listos para ser 'rescatados'.")

    def _inject(self, f, offset, data):
        f.seek(offset)
        f.write(data)
        print(f"    - Archivo inyectado en {hex(offset)}")

if __name__ == "__main__":
    gen = EvidenceGenerator()
    gen.generate()
