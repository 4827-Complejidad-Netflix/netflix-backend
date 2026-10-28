from fastapi import HTTPException, Request

from app.data.store import DataStore, Movie
from app.schemas import MovieOut


def get_store(request: Request) -> DataStore:
    return request.app.state.store


def movie_out(store: DataStore, movie_id: int) -> MovieOut:
    movie: Movie | None = store.movies.get(movie_id)
    if movie is None:
        raise HTTPException(404, f"Película {movie_id} no encontrada")
    return MovieOut(
        **movie.__dict__,
        positive_ratings=len(store.graph.users_of(movie_id)),
    )


def ensure_user(store: DataStore, user_id: int) -> None:
    if not store.graph.has_user(user_id):
        raise HTTPException(404, f"Usuario {user_id} no encontrado o sin calificaciones positivas")
