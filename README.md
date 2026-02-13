# UltraRecoverPro

UltraRecoverPro es un escáner forense de archivos orientado a recuperación basada en firmas, validación estructural y generación de reportes para análisis técnico y auditoría.

El proyecto está diseñado como una base sólida para escenarios de **digital forensics**, con énfasis en:
- Lectura eficiente de imágenes/dispositivos con `mmap`.
- Detección rápida de firmas con Aho-Corasick.
- Reducción de falsos positivos por entropía + validación de formato.
- Reportes en HTML, JSON y CSV.

---

## Tabla de contenidos

- [Características principales](#características-principales)
- [Arquitectura del proyecto](#arquitectura-del-proyecto)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Uso rápido](#uso-rápido)
- [Ejemplo de ejecución](#ejemplo-de-ejecución)
- [Salida y reportes](#salida-y-reportes)
- [Pruebas](#pruebas)
- [Generación de evidencia de prueba](#generación-de-evidencia-de-prueba)
- [Roadmap empresarial](#roadmap-empresarial)
- [Buenas prácticas forenses](#buenas-prácticas-forenses)
- [Contribución](#contribución)
- [Licencia](#licencia)

---

## Características principales

- **Escaneo por firmas binarias** de tipos como JPEG, PNG, MP4 y ZIP.
- **Motor de búsqueda eficiente** usando autómata Aho-Corasick (`pyahocorasick`).
- **Lectura zero-copy** sobre imágenes/disco mediante `mmap` y `memoryview`.
- **Validación por entropía** para filtrar bloques de baja información.
- **Validación estructural básica** por formato para disminuir falsos positivos.
- **Dashboard en consola** (Rich) con progreso y estadísticas durante el escaneo.
- **Reportería multipropósito**:
  - HTML (visual ejecutiva/técnica)
  - JSON (automatización e integración)
  - CSV (BI/SIEM/auditoría)

---

## Arquitectura del proyecto

Flujo principal de análisis:

1. `DiskManager` abre y mapea la fuente forense en solo lectura.
2. `DeepCarver` busca firmas en bloques, incluyendo coincidencias en fronteras de bloque.
3. `FileValidator` aplica controles de entropía y estructura.
4. `ForensicReporter` registra hallazgos y exporta reportes.
5. `ForensicDashboard` muestra telemetría en tiempo real.

---

## Estructura del repositorio

```text
UltraRecoverPro/
├── main.py                        # CLI y pipeline principal de escaneo
├── core/
│   └── device.py                  # Acceso al origen con mmap
├── engines/
│   └── carver.py                  # Motor de carving por firmas
├── utils/
│   └── identifiers.py             # Entropía, validación y hashing forense
├── post_processing/
│   ├── reporter.py                # Export HTML/JSON/CSV
│   ├── report_template.html       # Plantilla HTML de informe
│   └── repair.py                  # Reparaciones iniciales (ej. MP4/ZIP)
├── ui/
│   └── dashboard.py               # Dashboard de consola con Rich
├── tests/
│   ├── test_pipeline.py           # Pruebas del pipeline end-to-end
│   ├── test_reporter.py           # Pruebas de reportería
│   └── simulation.py              # Generador de evidencia sintética
└── docs/
    └── ENTERPRISE_RECOMMENDATIONS.md
```

---

## Requisitos

- Python **3.10+** recomendado.
- Dependencias de `requirements.txt`.

Dependencias principales:
- `pyahocorasick`
- `rich`
- `pytest` (testing)

---

## Instalación

```bash
# 1) Clonar repositorio
git clone <tu-repo-url>
cd UltraRecoverPro

# 2) Crear entorno virtual (recomendado)
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate   # Windows PowerShell

# 3) Instalar dependencias
pip install -r requirements.txt
```

---

## Uso rápido

Comando base:

```bash
python main.py <ruta_imagen_o_dispositivo> --report-dir reports
```

Parámetros disponibles:

- `source` (posicional): ruta al disco o imagen forense.
- `--report-dir`: directorio de salida de reportes (default: `reports`).
- `--block-size`: tamaño de bloque en bytes (default: `1048576`).
- `--log-level`: nivel de logging (`DEBUG`, `INFO`, `WARNING`, etc.).

Ejemplo:

```bash
python main.py tests/evidence.img --report-dir reports --block-size 1048576 --log-level INFO
```

---

## Ejemplo de ejecución

Salida típica:

```text
Análisis completado. Detecciones válidas: 3
Reporte HTML: reports/forensic_report.html
Reporte JSON: reports/forensic_report.json
```

Además del HTML/JSON, también se genera:

```text
reports/forensic_report.csv
```

---

## Salida y reportes

### 1) Reporte HTML
Pensado para revisión humana, incluye resumen del caso y tabla de archivos recuperados.

### 2) Reporte JSON
Incluye:
- metadatos del caso (`case_id`, `investigator`, `start_time`)
- totales por tipo
- bloque `integrity` con métricas de hashes
- detalle de archivos recuperados

### 3) Reporte CSV
Formato tabular para exportación a herramientas externas (BI/SIEM/auditorías).

Campos:
- `name`
- `type`
- `size_bytes`
- `size_kb`
- `offset`
- `hash`

---

## Pruebas

Ejecutar todas las pruebas:

```bash
pytest -q
```

Cobertura de pruebas actual:
- generación de reportes del pipeline
- detección en fronteras de bloque
- compatibilidad con `memoryview`
- escape de contenido no confiable en HTML
- export JSON con resumen de integridad
- export CSV

---

## Generación de evidencia de prueba

Para crear una imagen de evidencia sintética:

```bash
python tests/simulation.py
```

Esto crea un archivo con datos aleatorios y firmas inyectadas para pruebas controladas.

---

## Roadmap empresarial

Consulta el documento de evolución empresarial:

- [`docs/ENTERPRISE_RECOMMENDATIONS.md`](docs/ENTERPRISE_RECOMMENDATIONS.md)

Incluye recomendaciones de arquitectura, seguridad, observabilidad, compliance y escalamiento.

---

## Buenas prácticas forenses

- Trabajar siempre sobre **copias forenses** o imágenes, no sobre evidencia original.
- Mantener el origen en modo solo lectura.
- Preservar hash y metadatos para cadena de custodia.
- Versionar reportes y artefactos con identificador de caso.

---

## Contribución

Sugerencias para contribuir:

1. Crear una rama por feature/fix.
2. Añadir/actualizar pruebas cuando se modifique comportamiento.
3. Ejecutar `pytest -q` antes de enviar cambios.
4. Mantener cambios pequeños y bien documentados.

---

## Licencia

Define aquí la licencia oficial del proyecto (por ejemplo MIT, Apache-2.0, GPLv3).

> Si aún no has elegido licencia, añade un archivo `LICENSE` antes de distribución pública/comercial.
