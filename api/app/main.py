from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.models.user import User
from app.models.category import Category
from app.models.list import LinkList
from app.models.link import Link
from app.models.tag import Tag
from app.models.link_tag import LinkTag
from app.models.user_expertise import UserExpertise
from app.models.vote import Vote
from app.models.user_reputation import UserReputation

from app.auth import router as auth_router
from app.admin import router as admin_router
from app.search import router as search_router
from app.categories import router as categories_router
from app.lists import router as lists_router
from app.links import router as links_router
from app.tags import router as tags_router
from app.expertise import router as expertise_router
from app.votes import router as votes_router
from app.reputation import router as reputation_router
from app.users import router as users_router
from app.admin_seed import router as admin_seed_router

from app.opensearch_client import ensure_links_index


Base.metadata.create_all(bind=engine)

ensure_links_index()


app = FastAPI(
    title="Organic Rankings API",
    description="API del buscador Organic Rankings",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
