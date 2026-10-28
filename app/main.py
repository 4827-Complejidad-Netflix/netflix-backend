from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import graph, movies, users
from app.core.config import get_settings
from app.data.store import load_store

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.store = load_store(settings.data_dir, settings.min_rating)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movies.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(graph.router, prefix="/api")


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
