# AWS Forensic Playbook (UltraRecoverPro)

Este playbook define una forma segura de probar UltraRecoverPro con datos reales en AWS usando snapshot + volumen temporal para preservar cadena de custodia.

## Flujo recomendado

1. Crear snapshot del volumen origen.
2. Crear volumen temporal desde snapshot.
3. Adjuntarlo a instancia EC2 de análisis.
4. Montar en solo lectura (si aplica).
5. Escanear con UltraRecoverPro.
6. Subir reportes a S3.

## Script automatizado

Se incluye el script:

```bash
scripts/aws_forensic_pipeline.sh
```

### Requisitos

- `aws` CLI autenticado.
- `jq` instalado.
- Permisos mínimos EC2 + S3.

### Ejemplo de uso

```bash
scripts/aws_forensic_pipeline.sh \
  --instance-id i-0123456789abcdef0 \
  --source-volume-id vol-0123456789abcdef0 \
  --availability-zone us-east-1a \
  --device-name /dev/sdf \
  --region us-east-1 \
  --mount-point /mnt/evidence_ro \
  --report-dir /tmp/reports_case001 \
  --s3-uri s3://mi-bucket/cases/case001/
```

## Notas operativas

- Mantén el origen siempre intacto: analiza snapshot o imagen.
- Usa S3 con cifrado SSE-KMS y versionado.
- Conserva hash del origen y reportes por caso.
- Ejecuta en una instancia dedicada de análisis.
