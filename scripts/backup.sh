#!/usr/bin/env bash
set -euo pipefail

# Uso: ./scripts/backup.sh [directorio_salida]
# Genera un backup de PostgreSQL comprimido con gzip.
# El stack debe estar levantado (docker compose up -d).

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    echo "No existe .env en la raiz del proyecto."
    exit 1
fi

set -a
source .env
set +a

outdir="${1:-backups}"
mkdir -p "$outdir"

file="$outdir/organic-rankings-$(date +%Y-%m-%d_%H%M%S).sql.gz"

docker compose exec -T postgres pg_dump \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    | gzip > "$file"

echo "Backup guardado en $file"
