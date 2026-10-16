# Organic Rankings

Plataforma comunitaria de listas de recursos web, ordenadas por votos de personas.
Stack: FastAPI + PostgreSQL + Redis (rate limiting) + Next.js, todo en Docker.

## Requisitos

- Docker con el plugin de Docker Compose (Docker Desktop, Docker en Linux o Unraid).

Nada más. Ni Node, ni Python, ni PostgreSQL instalados a mano.

## Arranque rápido

```bash
git clone https://github.com/plustechsl/organic-rankings.git
cd organic-rankings
cp .env.example .env
# Edita .env y rellena los valores obligatorios (ver abajo)
docker compose up -d
```

Abre http://localhost:3000 (o el puerto que hayas puesto en `FRONTEND_PORT`).

**Ese es el único puerto expuesto de todo el stack**: postgres, redis y api no
publican puertos; el navegador llega a la API a través del frontend, en `/api/...`.

## Variables obligatorias en `.env`

| Variable | Qué es |
|---|---|
| `POSTGRES_PASSWORD` | Contraseña de la base de datos. |
| `JWT_SECRET` | Secreto para firmar los tokens de sesión. |
| `IP_HASH_SALT` | Sal para hashear las IP de los usuarios. |
| `TURNSTILE_SECRET_KEY` | Clave privada de Cloudflare Turnstile (obligatoria con `APP_ENV=production`). |

Genera los secretos con (uno distinto para cada uno):

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

`JWT_SECRET` e `IP_HASH_SALT` son obligatorios en producción: con
`APP_ENV=production` la API se niega a arrancar con valores por defecto.
En local (`APP_ENV=development`) usa valores por defecto y avisa por log.

Opcionales: `NEXT_PUBLIC_TURNSTILE_SITE_KEY` (widget de captcha en
registro/login), `NEXT_PUBLIC_DONATE_URL` (botón de donar) y `FRONTEND_PORT`.

## Desarrollo

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

El `docker-compose.dev.yml` **no se carga solo** (para que un `docker compose up`
en un servidor arranque en producción): hay que pasarlo con `-f`, como arriba.
Con él, la API arranca con recarga en caliente (`--reload`, con el código montado
desde `./api/app`), el frontend con `npm run dev` y se publica el puerto 8000 para
depurar contra la API directamente.

Si prefieres correr el frontend fuera de Docker (`cd web && npm run dev`), la
API sigue necesitaria levantada; apunta a ella con `API_PROXY_TARGET` (por
defecto `http://localhost:8000`).

## Backup y restauración

```bash
./scripts/backup.sh                  # genera backups/organic-rankings-<fecha>.sql.gz
./scripts/restore.sh backups/xxx.sql.gz   # pide confirmación antes de borrar datos
```

La restauración es un `pg_dump`/`psql` directo: la búsqueda vive en la propia
PostgreSQL, así que no hay ningún paso de reindexado ni servicios que mantener
en sincronía.

## Trasladar el proyecto a otra máquina o servidor

1. `git clone` del repositorio.
2. `cp .env.example .env` y rellenar (si migras, usa el mismo `.env` de antes).
3. `docker compose up -d --build`.
4. Si hay datos previos: `./scripts/restore.sh <backup.sql.gz>`.

No hay nada más que configurar: no hay que rebuildar imágenes por IP, no hay
variables de entorno del navegador, ni CORS, ni índices externos.

### Unraid

Mismo procedimiento en `/mnt/user/Projects/organic-rankings` (o donde quieras).
Publica solo el puerto de `FRONTEND_PORT` (3000) y ya está accesible. Los datos
viven en los volúmenes de Docker (`postgres_data`, `redis_data`).

## Arquitectura (por qué es portable)

- **Un solo puerto**: el frontend hace de proxy en `/api/...` hacia el servicio
  `api` por la red interna de compose (`API_PROXY_TARGET`). Sin CORS y sin
  `NEXT_PUBLIC_API_URL`: mover de servidor no exige rebuildar nada.
- **Búsqueda en PostgreSQL**: texto completo con `unaccent` (acentos) y
  `pg_trgm` (`word_similarity` para erratas). Se crea al arrancar la API
  (`CREATE EXTENSION IF NOT EXISTS`), sin scripts manuales.
- **Redis** se usa solo para el rate limiting (anti-bots). Sus datos son
  desechables: no hace falta incluirlo en backups.
- **Sin Alembic**: el esquema se crea con `create_all` al arrancar; una
  restauración de backup trae su propio esquema.
