import logging

from fastapi import FastAPI

from app.config import (
    APP_ENV,
    JWT_SECRET,
    JWT_SECRET_DEFAULT,
    TURNSTILE_SECRET_KEY,
)
from app.database import Base, engine
from app.utils import IP_HASH_SALT, IP_HASH_SALT_DEFAULT
from app.models.user import User
from app.models.category import Category
from app.models.list import LinkList
from app.models.link import Link
from app.models.tag import Tag
from app.models.link_tag import LinkTag
from app.models.user_expertise import UserExpertise
from app.models.vote import Vote
from app.models.user_reputation import UserReputation
from app.models.referral import Invitation, ReferralCode

from app.auth import router as auth_router
from app.admin import router as admin_router
from app.search import ensure_search_ready, router as search_router
from app.categories import router as categories_router
from app.lists import router as lists_router
from app.links import router as links_router
from app.tags import router as tags_router
from app.expertise import router as expertise_router
from app.votes import router as votes_router
from app.reputation import router as reputation_router
from app.users import router as users_router
from app.referrals import router as referrals_router
from app.admin_seed import router as admin_seed_router


logger = logging.getLogger("uvicorn.error")

INSECURE_DEFAULT_SECRETS = {
    "JWT_SECRET": (JWT_SECRET, JWT_SECRET_DEFAULT),
    "IP_HASH_SALT": (IP_HASH_SALT, IP_HASH_SALT_DEFAULT),
}


def check_insecure_defaults() -> None:
    insecure = [
        name
        for name, (value, default) in INSECURE_DEFAULT_SECRETS.items()
        if not value or value == default
    ]

    if not insecure:
        return

    if APP_ENV == "production":
        raise RuntimeError(
            "Insecure default secrets in production: " + ", ".join(insecure)
        )

    logger.warning(
        "Using insecure default secrets (%s); set them before production.",
        ", ".join(insecure),
    )


def check_production_requirements() -> None:
    if APP_ENV != "production":
        return

    missing = []

    if not TURNSTILE_SECRET_KEY:
        missing.append("TURNSTILE_SECRET_KEY")

    if missing:
        raise RuntimeError(
            "Missing required production configuration: " + ", ".join(missing)
        )


check_insecure_defaults()
check_production_requirements()

Base.metadata.create_all(bind=engine)

ensure_search_ready()


app = FastAPI(
    title="Organic Rankings API",
    description="API del buscador Organic Rankings",
    version="0.1.0",
)


app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(search_router)
app.include_router(categories_router)
app.include_router(lists_router)
app.include_router(links_router)
app.include_router(tags_router)
app.include_router(expertise_router)
app.include_router(votes_router)
app.include_router(reputation_router)
app.include_router(users_router)
app.include_router(referrals_router)
app.include_router(admin_seed_router)


@app.get("/")
def root():
    return {
        "name": "organic_rankings",
        "status": "online",
        "version": "0.1.0",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
    }
