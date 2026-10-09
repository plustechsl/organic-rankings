from os import getenv

# =============================================================================
# PostgreSQL
# =============================================================================

POSTGRES_HOST = getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = getenv("POSTGRES_DB", "organic_rankings")
POSTGRES_USER = getenv("POSTGRES_USER", "organic_rankings")
POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD", "organic_rankings_dev")

DATABASE_URL = (
    f"postgresql+psycopg://"
    f"{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# =============================================================================
# Redis
# =============================================================================

REDIS_HOST = getenv("REDIS_HOST", "redis")
REDIS_PORT = int(getenv("REDIS_PORT", "6379"))

# =============================================================================
# OpenSearch
# =============================================================================

OPENSEARCH_HOST = getenv("OPENSEARCH_HOST", "opensearch")
OPENSEARCH_PORT = int(getenv("OPENSEARCH_PORT", "9200"))

LINKS_INDEX = getenv("OPENSEARCH_INDEX", "links")

# =============================================================================
# Authentication
# =============================================================================

JWT_SECRET = getenv(
    "JWT_SECRET",
    "CHANGE_THIS_SECRET_IN_PRODUCTION",
)

JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200")
)