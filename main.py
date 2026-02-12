import sys
from core.device import DiskManager
from engines.carver import DeepCarver
from ui.dashboard import ForensicDashboard

def main(source: str):
    # 1. Inicializar Hardware
    dev = DiskManager(source)
    dev.open_device()

    # 2. Definir Firmas (Magic Numbers)
    signatures = {
        'JPEG': {'header': b'\xff\xd8\xff'},
        'PNG':  {'header': b'\x89\x50\x4e\x47'},
        'MP4':  {'header': b'\x00\x00\x00\x18\x66\x74\x79\x70'},
        'ZIP':  {'header': b'\x50\x4b\x03\x04'}
    }

    # 3. Lanzar Motores
    carver = DeepCarver(signatures)
    dashboard = ForensicDashboard()

    # Simulación de flujo de trabajo
    # En producción, aquí se manejaría la shared_memory y el loop de eventos
    print(f"Iniciando análisis forense en {source}...")
    # ... lógica de escaneo ...

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python main.py <ruta_disco_o_imagen>")
    else:
        main(sys.argv[1])
