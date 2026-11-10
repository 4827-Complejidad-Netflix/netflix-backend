from fastapi import APIRouter, Depends

from app.api.deps import get_store, movie_out
from app.data.store import DataStore
from app.graph.bfs import recommend_from_movies
from app.schemas import Candidate, CandidateVia, LikesIn, LikesRecommendations

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

VIA_LIMIT = 3


@router.post("", response_model=LikesRecommendations)
def recommend_from_likes(body: LikesIn, store: DataStore = Depends(get_store)):
    """Recomendaciones para un perfil anónimo: BFS de 3 niveles desde las películas con "me gusta".

    likes → usuarios que también las valoraron → películas candidatas que esos usuarios valoraron.
    """
    liked = list(dict.fromkeys(body.liked))  # sin duplicados, conservando el orden
    known = [m for m in liked if m in store.movies]
    result = recommend_from_movies(store.graph, set(known))
    return LikesRecommendations(
        liked=[movie_out(store, m) for m in known],
        ignored=[m for m in liked if m not in store.movies],
        similar_users=result.similar_users,
        total_candidates=len(result.candidates),
        candidates=[
            Candidate(
                movie=movie_out(store, c.movie_id),
                score=c.score,
                via=[
                    CandidateVia(movie=movie_out(store, m), users=n)
                    for m, n in sorted(c.via.items(), key=lambda kv: (-kv[1], kv[0]))[:VIA_LIMIT]
                ],
            )
            for c in result.candidates[: body.limit]
        ],
    )
