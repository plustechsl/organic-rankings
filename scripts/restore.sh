#!/usr/bin/env bash
set -euo pipefail

# Uso: ./scripts/restore.sh <backup.sql.gz>
# RESTAURA un backup de PostgreSQL: BORRA los datos actuales de la base
# de datos y los sustituye por los del fichero. No hace falta reindexar
# nada mas: la busqueda vive en la propia base de datos.

if [ $# -ne 1 ]; then
    echo "Uso: ./scripts/restore.sh <backup.sql.gz>"
    exit 1
fi

if [ ! -f "$1" ]; then
    echo "No existe el fichero: $1"
    exit 1
fi

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    echo "No existe .env en la raiz del proyecto."
    exit 1
fi

set -a
source .env
set +a

echo "ATENCION: se van a borrar todos los datos de '$POSTGRES_DB'"
echo "y se sustituiran por los de '$1'."
read -r -p "Escribe 'restaurar' para confirmar: " confirm

if [ "$confirm" != "restaurar" ]; then
    echo "Cancelado."
    exit 1
fi

docker compose exec -T postgres psql -U "$POSTGRES_USER" -d postgres \
    -c "DROP DATABASE IF EXISTS $POSTGRES_DB WITH (FORCE);"

docker compose exec -T postgres psql -U "$POSTGRES_USER" -d postgres \
    -c "CREATE DATABASE $POSTGRES_DB OWNER $POSTGRES_USER;"

gunzip -c "$1" | docker compose exec -T postgres psql \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB"

# Reinicia la API para que aplique las migraciones de esquema pendientes
docker compose restart api

echo "Restauracion completada."
