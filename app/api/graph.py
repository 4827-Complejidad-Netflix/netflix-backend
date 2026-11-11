import random

from fastapi import APIRouter, Depends, Query

from app.api.deps import ensure_user, get_store, movie_out
from app.core.config import get_settings
from app.data.store import DataStore
from app.graph.explain import average_similarity, best_matches, genre_profile, shared_movies
from app.graph.kruskal import kruskal
from app.graph.projection import build_projection, detect_communities, jaccard
from app.schemas import (
    CommunitiesOut,
    Community,
    GenreShareOut,
    GraphOut,
    GraphStats,
    IsolatedUser,
    KruskalOut,
    SharedMovieOut,
    SharedOut,
)

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/stats", response_model=GraphStats)
def graph_stats(store: DataStore = Depends(get_store)):
    return GraphStats(
        **store.graph.stats(),
        total_ratings=store.total_ratings,
        min_rating=get_settings().min_rating,
    )


class SampleParams:
    def __init__(
        self,
        sample_size: int = Query(25, ge=2, le=300),
        min_positive: int = Query(20, ge=1),
        max_positive: int = Query(300, ge=1),
        seed: int | None = Query(None, description="Semilla para reproducir la muestra"),
    ):
        self.sample_size = sample_size
        self.min_positive = min_positive
        self.max_positive = max_positive
        self.seed = seed


def sample_users(store: DataStore, params: SampleParams) -> list[int]:
    eligible = [
        u for u, movies in store.graph.user_adj.items()
        if params.min_positive <= len(movies) <= params.max_positive
    ]
    rng = random.Random(params.seed)
    return sorted(rng.sample(eligible, min(params.sample_size, len(eligible))))


def explain_community(store: DataStore, cid: int, members: list[int], sample: list[int], edges) -> Community:
    """Comunidad con lo que explica su formación: similitud interna, películas y géneros compartidos."""
    genres_of = {m.id: m.genres for m in store.movies.values()}
    avg, internal = average_similarity(members, edges)
    return Community(
        id=cid,
        users=members,
        avg_similarity=avg,
        internal_edges=internal,
        shared_movies=[
            SharedMovieOut(movie=movie_out(store, s.movie_id), users=s.users)
            for s in shared_movies(store.graph, members)
        ],
        genres=[GenreShareOut(**g.__dict__) for g in genre_profile(store.graph, members, sample, genres_of)],
    )


def build_communities_response(store: DataStore, sample, groups, edges, all_pairs) -> dict:
    """`edges` son las aristas que se dibujan; `all_pairs`, todos los pares de la muestra con su Jaccard."""
    members = [sorted(g) for g in groups if len(g) > 1]
    communities_ = [explain_community(store, i, users, sample, edges) for i, users in enumerate(members)]
    isolated = sorted(g[0] for g in groups if len(g) == 1)
    community_of = {u: c.id for c in communities_ for u in c.users}

    matches = best_matches(isolated, all_pairs)
    isolated_details = [
        IsolatedUser(
            user=u,
            best_match=matches[u][0] if u in matches and matches[u][1] > 0 else None,
            similarity=round(matches[u][1], 4) if u in matches else 0.0,
        )
        for u in isolated
    ]

    graph = GraphOut(
        nodes=[
            {"id": f"user-{u}", "kind": "user", "ref": u, "level": community_of.get(u, -1), "label": f"Usuario {u}"}
            for u in sample
        ],
        edges=[{"source": f"user-{u}", "target": f"user-{v}", "weight": round(j, 4)} for u, v, j in edges],
    )
    return {
        "sample": sample,
        "communities": communities_,
        "isolated": isolated,
        "isolated_details": isolated_details,
        "graph": graph,
    }


@router.get("/communities", response_model=CommunitiesOut)
def communities(
    theta: float = Query(0.10, ge=0.0, le=1.0, description="Umbral de Jaccard"),
    params: SampleParams = Depends(),
    store: DataStore = Depends(get_store),
):
    """Proyección G_U (fuerza bruta) + comunidades con UFDS sobre una muestra de usuarios."""
    sample = sample_users(store, params)
    # Se comparan todos los pares una vez (θ = 0) y luego se filtra: así también se sabe
    # qué tan cerca quedó cada usuario aislado del umbral, sin repetir la fuerza bruta.
    all_pairs = build_projection(store.graph, sample, theta=0.0)
    edges = [e for e in all_pairs if e[2] >= theta]
    groups = detect_communities(sample, edges)
    return CommunitiesOut(theta=theta, **build_communities_response(store, sample, groups, edges, all_pairs))


@router.get("/communities/kruskal", response_model=KruskalOut)
def kruskal_communities(
    k: int = Query(3, ge=1, le=300, description="Número de comunidades deseadas"),
    params: SampleParams = Depends(),
    store: DataStore = Depends(get_store),
):
    """Kruskal voraz sobre G_U: une primero los pares más similares hasta dejar k comunidades.

    Solo se consideran aristas con similitud > 0; si la muestra tiene más de k componentes
    desconectadas, el resultado tendrá más de k comunidades.
    """
    sample = sample_users(store, params)
    edges = [e for e in build_projection(store.graph, sample, theta=0.0) if e[2] > 0]
    chosen, groups = kruskal(sample, edges, k)
    return KruskalOut(
        k=k,
        total_similarity=round(sum(w for _, _, w in chosen), 4),
        **build_communities_response(store, sample, groups, chosen, edges),
    )


@router.get("/shared", response_model=SharedOut)
def shared(
    u: int = Query(..., description="Primer usuario"),
    v: int = Query(..., description="Segundo usuario"),
    limit: int = Query(12, ge=1, le=100),
    store: DataStore = Depends(get_store),
):
    """Películas que ambos valoraron positivamente: la intersección que da su Jaccard en G_U."""
    ensure_user(store, u)
    ensure_user(store, v)
    a, b = set(store.graph.movies_of(u)), set(store.graph.movies_of(v))
    common = sorted(a & b, key=lambda m: (-len(store.graph.users_of(m)), m))
    return SharedOut(
        u=u,
        v=v,
        similarity=round(jaccard(a, b), 4),
        shared_count=len(a & b),
        union_count=len(a | b),
        movies=[movie_out(store, m) for m in common[:limit]],
    )