"""Kruskal (voraz) sobre G_U: árbol de expansión máxima por similitud de Jaccard y k-comunidades.

Estrategia voraz: se ordenan las aristas de mayor a menor similitud y en cada paso se toma la
más similar que une dos componentes distintas (UFDS evita ciclos). Detenerse cuando quedan k
componentes equivale a un agrupamiento por enlace simple (single-linkage) en k comunidades.
Complejidad: O(E log E) por el ordenamiento + O(E · α(n)) por las operaciones de UFDS.
"""

from app.graph.ufds import UnionFind


def kruskal(
    nodes: list[int],
    edges: list[tuple[int, int, float]],
    k: int = 1,
) -> tuple[list[tuple[int, int, float]], list[list[int]]]:
    """Devuelve (aristas elegidas, comunidades). Con k=1 es el árbol/bosque de expansión máxima."""
    uf = UnionFind(nodes)
    components = len(nodes)
    chosen: list[tuple[int, int, float]] = []

    for u, v, w in sorted(edges, key=lambda e: e[2], reverse=True):
        if components <= k:
            break
        if uf.union(u, v):
            chosen.append((u, v, w))
            components -= 1

    return chosen, uf.groups()
