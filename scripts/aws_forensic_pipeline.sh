#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Uso:
  scripts/aws_forensic_pipeline.sh \
    --instance-id i-xxxxxxxx \
    --source-volume-id vol-xxxxxxxx \
    --availability-zone us-east-1a \
    --device-name /dev/sdf \
    --region us-east-1 \
    --mount-point /mnt/evidence_ro \
    --report-dir /tmp/reports_case001 \
    --s3-uri s3://mi-bucket/cases/case001/

Descripción:
  Automatiza un flujo forense en AWS:
  1) Snapshot de volumen origen
  2) Creación de volumen temporal desde snapshot
  3) Adjuntar volumen a instancia de análisis
  4) Montaje de solo lectura (si existe filesystem)
  5) Ejecución de UltraRecoverPro
  6) Subida de reportes a S3

Requisitos:
  - aws cli autenticado con permisos EC2 + S3
  - jq instalado
  - Ejecutar desde la raíz del repositorio (donde está main.py)
EOF
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "[ERROR] Comando requerido no encontrado: $1" >&2
    exit 1
  }
}

cleanup() {
  if [[ "${DETACH_ON_EXIT:-}" == "1" && -n "${TEMP_VOL_ID:-}" ]]; then
    echo "[*] Desadjuntando volumen temporal ${TEMP_VOL_ID}"
    aws ec2 detach-volume --volume-id "${TEMP_VOL_ID}" --region "${REGION}" >/dev/null || true
  fi
}

require_cmd aws
require_cmd jq
require_cmd python

INSTANCE_ID=""
SOURCE_VOLUME_ID=""
AVAILABILITY_ZONE=""
DEVICE_NAME=""
REGION=""
MOUNT_POINT=""
REPORT_DIR=""
S3_URI=""
BLOCK_SIZE="1048576"
LOG_LEVEL="INFO"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --instance-id) INSTANCE_ID="$2"; shift 2 ;;
    --source-volume-id) SOURCE_VOLUME_ID="$2"; shift 2 ;;
    --availability-zone) AVAILABILITY_ZONE="$2"; shift 2 ;;
    --device-name) DEVICE_NAME="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    --mount-point) MOUNT_POINT="$2"; shift 2 ;;
    --report-dir) REPORT_DIR="$2"; shift 2 ;;
    --s3-uri) S3_URI="$2"; shift 2 ;;
    --block-size) BLOCK_SIZE="$2"; shift 2 ;;
    --log-level) LOG_LEVEL="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "[ERROR] Parámetro desconocido: $1"; usage; exit 1 ;;
  esac
done

if [[ -z "$INSTANCE_ID" || -z "$SOURCE_VOLUME_ID" || -z "$AVAILABILITY_ZONE" || -z "$DEVICE_NAME" || -z "$REGION" || -z "$MOUNT_POINT" || -z "$REPORT_DIR" || -z "$S3_URI" ]]; then
  echo "[ERROR] Faltan parámetros obligatorios."
  usage
  exit 1
fi

trap cleanup EXIT

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
SNAPSHOT_DESC="UltraRecoverPro forensic snapshot ${TIMESTAMP}"

echo "[*] Creando snapshot desde ${SOURCE_VOLUME_ID}"
SNAPSHOT_ID="$(aws ec2 create-snapshot \
  --volume-id "$SOURCE_VOLUME_ID" \
  --description "$SNAPSHOT_DESC" \
  --region "$REGION" | jq -r '.SnapshotId')"

echo "[*] Esperando snapshot completado: ${SNAPSHOT_ID}"
aws ec2 wait snapshot-completed --snapshot-ids "$SNAPSHOT_ID" --region "$REGION"

echo "[*] Creando volumen temporal desde snapshot"
TEMP_VOL_ID="$(aws ec2 create-volume \
  --snapshot-id "$SNAPSHOT_ID" \
  --availability-zone "$AVAILABILITY_ZONE" \
  --tag-specifications "ResourceType=volume,Tags=[{Key=Name,Value=ultrarecover-temp-${TIMESTAMP}}]" \
  --region "$REGION" | jq -r '.VolumeId')"

echo "[*] Esperando volumen disponible: ${TEMP_VOL_ID}"
aws ec2 wait volume-available --volume-ids "$TEMP_VOL_ID" --region "$REGION"

echo "[*] Adjuntando volumen temporal ${TEMP_VOL_ID} a ${INSTANCE_ID} en ${DEVICE_NAME}"
aws ec2 attach-volume \
  --volume-id "$TEMP_VOL_ID" \
  --instance-id "$INSTANCE_ID" \
  --device "$DEVICE_NAME" \
  --region "$REGION" >/dev/null

DETACH_ON_EXIT=1

echo "[*] Esperando estado in-use"
aws ec2 wait volume-in-use --volume-ids "$TEMP_VOL_ID" --region "$REGION"

sleep 5

mkdir -p "$MOUNT_POINT" "$REPORT_DIR"

echo "[*] Detectando dispositivo real del volumen"
REAL_DEVICE="$(lsblk -o NAME,SERIAL -J | jq -r '.blockdevices[] | select(.serial != null) | "/dev/" + .name' | head -n 1)"
if [[ -z "${REAL_DEVICE}" ]]; then
  REAL_DEVICE="$DEVICE_NAME"
fi

echo "[*] Intentando montar en solo lectura: ${REAL_DEVICE} -> ${MOUNT_POINT}"
set +e
mount -o ro,noload "$REAL_DEVICE" "$MOUNT_POINT" >/dev/null 2>&1
MOUNT_STATUS=$?
set -e

SCAN_SOURCE="$REAL_DEVICE"
if [[ $MOUNT_STATUS -eq 0 ]]; then
  echo "[+] Montado en solo lectura correctamente"
  SCAN_SOURCE="$REAL_DEVICE"
else
  echo "[!] No se pudo montar (puede ser volumen raw/sin FS). Se escaneará bloque directo."
fi

echo "[*] Ejecutando UltraRecoverPro"
python main.py "$SCAN_SOURCE" --report-dir "$REPORT_DIR" --block-size "$BLOCK_SIZE" --log-level "$LOG_LEVEL"

echo "[*] Subiendo reportes a ${S3_URI}"
aws s3 cp "$REPORT_DIR" "$S3_URI" --recursive --region "$REGION"

echo "[+] Flujo completado. Snapshot: ${SNAPSHOT_ID}, Volume: ${TEMP_VOL_ID}"
