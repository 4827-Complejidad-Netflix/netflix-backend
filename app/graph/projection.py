"""Proyección usuario–usuario G_U por similitud de Jaccard (fuerza bruta, O(n² · d))."""

from itertools import combinations

from app.graph.bipartite import BipartiteGraph
from app.graph.ufds import UnionFind


def jaccard(a: set[int], b: set[int]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def build_projection(graph: BipartiteGraph, users: list[int], theta: float) -> list[tuple[int, int, float]]:
    """Compara todos los pares n(n-1)/2 y conecta los que cumplen J(u, v) >= theta."""
    sets = {u: set(graph.movies_of(u)) for u in users}
    edges = []
    for u, v in combinations(users, 2):
        j = jaccard(sets[u], sets[v])
        if j >= theta:
            edges.append((u, v, j))
    return edges


def detect_communities(users: list[int], edges: list[tuple[int, int, float]]) -> list[list[int]]:
    uf = UnionFind(users)
    for u, v, _ in edges:
        uf.union(u, v)
    return uf.groups()


def community_pool(graph: BipartiteGraph, user_id: int, size: int) -> list[int]:
    """El usuario y los `size` usuarios del nivel 2 del BFS con más películas en común con él.

    La proyección es O(n² · d), así que se acota a los vecinos más cercanos en lugar de a todo el dataset.
    """
    shared: dict[int, int] = {}
    for movie_id in graph.movies_of(user_id):
        for other in graph.users_of(movie_id):
            if other != user_id:
                shared[other] = shared.get(other, 0) + 1
    nearest = sorted(shared, key=lambda u: (-shared[u], u))[:size]
    return [user_id, *nearest]


def user_community(
    graph: BipartiteGraph, user_id: int, theta: float, pool_size: int
) -> tuple[list[int], list[int]]:
    """Comunidad UFDS del usuario dentro de su pool: proyección G_U con umbral `theta` y Union-Find.

    Devuelve (pool, comunidad); la comunidad incluye al propio usuario y está ordenada por id.
    """
    pool = community_pool(graph, user_id, pool_size)
    groups = detect_communities(pool, build_projection(graph, pool, theta))
    community = next(g for g in groups if user_id in g)
    return pool, sorted(community)


def recommend_from_community(
    graph: BipartiteGraph, user_id: int, community: list[int], limit: int = 10
) -> list[tuple[int, int]]:
    """Películas que valoraron positivamente los miembros de la comunidad y el usuario aún no tiene.

    Score = nº de miembros que la valoraron; desempate por id. Devuelve [(movie_id, score)].
    """
    seen = set(graph.movies_of(user_id))
    scores: dict[int, int] = {}
    for member in community:
        if member == user_id:
            continue
        for movie_id in graph.movies_of(member):
            if movie_id not in seen:
                scores[movie_id] = scores.get(movie_id, 0) + 1
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    return ranked[:limit]
