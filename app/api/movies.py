from fastapi import APIRouter, Depends, Query

from app.api.deps import get_store, movie_out
from app.data.store import DataStore
from app.schemas import MovieOut, PaginatedMovies

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("", response_model=PaginatedMovies)
def list_movies(
    q: str | None = Query(None, description="Búsqueda por título"),
    genre: str | None = None,
    sort: str = Query("popular", pattern="^(popular|title|year)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    store: DataStore = Depends(get_store),
):
    movies = store.movies.values()
    if q:
        needle = q.lower()
        movies = [m for m in movies if needle in m.title.lower()]
    if genre:
        movies = [m for m in movies if genre in m.genres]

    if sort == "popular":
        key = lambda m: -len(store.graph.users_of(m.id))  # noqa: E731
    elif sort == "year":
        key = lambda m: -(m.year or 0)  # noqa: E731
    else:
        key = lambda m: m.title  # noqa: E731
    movies = sorted(movies, key=key)

    page = movies[offset : offset + limit]
    return PaginatedMovies(total=len(movies), items=[movie_out(store, m.id) for m in page])


@router.get("/genres", response_model=list[str])
def list_genres(store: DataStore = Depends(get_store)):
    return sorted({g for m in store.movies.values() for g in m.genres})


@router.get("/{movie_id}", response_model=MovieOut)
def get_movie(movie_id: int, store: DataStore = Depends(get_store)):
    return movie_out(store, movie_id)
