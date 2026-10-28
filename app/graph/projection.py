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
