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
# Entorno
# =============================================================================

APP_ENV = getenv("APP_ENV", "development")

TRUSTED_PROXIES = tuple(
    proxy.strip()
    for proxy in getenv("TRUSTED_PROXIES", "").split(",")
    if proxy.strip()
)

# =============================================================================
# Rate limiting (ventana deslizante sobre Redis)
# =============================================================================

RATE_LIMIT_ENABLED = getenv("RATE_LIMIT_ENABLED", "true").lower() in {
    "1",
    "true",
    "yes",
}

REGISTER_RATE_LIMIT = int(getenv("REGISTER_RATE_LIMIT", "5"))
REGISTER_RATE_WINDOW = int(getenv("REGISTER_RATE_WINDOW", "3600"))

LOGIN_RATE_LIMIT = int(getenv("LOGIN_RATE_LIMIT", "10"))
LOGIN_RATE_WINDOW = int(getenv("LOGIN_RATE_WINDOW", "900"))

LOGIN_FAIL_LIMIT = int(getenv("LOGIN_FAIL_LIMIT", "5"))
LOGIN_FAIL_WINDOW = int(getenv("LOGIN_FAIL_WINDOW", "900"))

VOTE_USER_RATE_LIMIT = int(getenv("VOTE_USER_RATE_LIMIT", "30"))
VOTE_USER_RATE_WINDOW = int(getenv("VOTE_USER_RATE_WINDOW", "60"))

VOTE_IP_RATE_LIMIT = int(getenv("VOTE_IP_RATE_LIMIT", "100"))
VOTE_IP_RATE_WINDOW = int(getenv("VOTE_IP_RATE_WINDOW", "60"))

CREATION_RATE_LIMIT = int(getenv("CREATION_RATE_LIMIT", "20"))
CREATION_RATE_WINDOW = int(getenv("CREATION_RATE_WINDOW", "3600"))

# =============================================================================
# Cloudflare Turnstile (captcha)
# =============================================================================

TURNSTILE_SECRET_KEY = getenv("TURNSTILE_SECRET_KEY", "")

TURNSTILE_VERIFY_URL = getenv(
    "TURNSTILE_VERIFY_URL",
    "https://challenges.cloudflare.com/turnstile/v0/siteverify",
)

TURNSTILE_TIMEOUT = int(getenv("TURNSTILE_TIMEOUT", "5"))

# =============================================================================
# Authentication
# =============================================================================

JWT_SECRET_DEFAULT = "CHANGE_THIS_SECRET_IN_PRODUCTION"

JWT_SECRET = getenv(
    "JWT_SECRET",
    JWT_SECRET_DEFAULT,
)

JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200")
)
