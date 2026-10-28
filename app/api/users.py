from fastapi import APIRouter, Depends, Query

from app.api.deps import ensure_user, get_store, movie_out
from app.data.store import DataStore
from app.graph.bfs import bfs_tree, recommend
from app.schemas import GraphOut, RatedMovie, Recommendation, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[int])
def list_users(store: DataStore = Depends(get_store)):
    return sorted(store.graph.user_adj)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, limit: int = Query(20, ge=1, le=200), store: DataStore = Depends(get_store)):
    ensure_user(store, user_id)
    liked = sorted(store.graph.movies_of(user_id).items(), key=lambda kv: -kv[1])
    return UserOut(
        id=user_id,
        positive_ratings=len(liked),
        liked=[RatedMovie(movie=movie_out(store, m), rating=r) for m, r in liked[:limit]],
    )


@router.get("/{user_id}/recommendations", response_model=list[Recommendation])
def get_recommendations(
    user_id: int,
    limit: int = Query(10, ge=1, le=50),
    store: DataStore = Depends(get_store),
):
    ensure_user(store, user_id)
    return [
        Recommendation(movie=movie_out(store, m), score=score)
        for m, score in recommend(store.graph, user_id, limit)
    ]


@router.get("/{user_id}/bfs", response_model=GraphOut)
def get_bfs_tree(
    user_id: int,
    depth: int = Query(3, ge=1, le=3),
    branching: int = Query(2, ge=1, le=5),
    store: DataStore = Depends(get_store),
):
    """Árbol BFS podado (Figura 3 del informe) para dibujarlo en el frontend."""
    ensure_user(store, user_id)
    tree = bfs_tree(store.graph, user_id, depth, branching)
    for node in tree["nodes"]:
        if node["kind"] == "movie":
            node["label"] = store.movies[node["ref"]].title
        else:
            node["label"] = f"Usuario {node['ref']}"
    return tree
