import random

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_store
from app.core.config import get_settings
from app.data.store import DataStore
from app.graph.kruskal import kruskal
from app.graph.projection import build_projection, detect_communities
from app.schemas import CommunitiesOut, Community, GraphOut, GraphStats, KruskalOut

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


def build_communities_response(sample, groups, edges) -> dict:
    communities_ = [Community(id=i, users=sorted(g)) for i, g in enumerate(x for x in groups if len(x) > 1)]
    isolated = sorted(g[0] for g in groups if len(g) == 1)
    community_of = {u: c.id for c in communities_ for u in c.users}

    graph = GraphOut(
        nodes=[
            {"id": f"user-{u}", "kind": "user", "ref": u, "level": community_of.get(u, -1), "label": f"Usuario {u}"}
            for u in sample
        ],
        edges=[{"source": f"user-{u}", "target": f"user-{v}", "weight": round(j, 4)} for u, v, j in edges],
    )
    return {"sample": sample, "communities": communities_, "isolated": isolated, "graph": graph}


@router.get("/communities", response_model=CommunitiesOut)
def communities(
    theta: float = Query(0.10, ge=0.0, le=1.0, description="Umbral de Jaccard"),
    params: SampleParams = Depends(),
    store: DataStore = Depends(get_store),
):
    """Proyección G_U (fuerza bruta) + comunidades con UFDS sobre una muestra de usuarios."""
    sample = sample_users(store, params)
    edges = build_projection(store.graph, sample, theta)
    groups = detect_communities(sample, edges)
    return CommunitiesOut(theta=theta, **build_communities_response(sample, groups, edges))


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
        **build_communities_response(sample, groups, chosen),
    )
