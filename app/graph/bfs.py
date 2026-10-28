"""BFS sobre G_B limitado a 3 niveles: usuario -> películas -> usuarios -> películas candidatas."""

from collections import Counter, deque
from dataclasses import dataclass

from app.graph.bipartite import BipartiteGraph


@dataclass
class BFSNode:
    kind: str  # "user" | "movie"
    id: int
    level: int
    parent: tuple[str, int] | None


def bfs_levels(graph: BipartiteGraph, source_user: int, max_depth: int = 3) -> list[BFSNode]:
    """Recorrido BFS completo hasta max_depth. Complejidad O(V + E) sobre el subgrafo explorado."""
    visited: set[tuple[str, int]] = {("user", source_user)}
    order: list[BFSNode] = [BFSNode("user", source_user, 0, None)]
    queue: deque[BFSNode] = deque(order)

    while queue:
        node = queue.popleft()
        if node.level >= max_depth:
            continue
        if node.kind == "user":
            neighbors = (("movie", m) for m in graph.movies_of(node.id))
        else:
            neighbors = (("user", u) for u in graph.users_of(node.id))
        for key in neighbors:
            if key in visited:
                continue
            visited.add(key)
            child = BFSNode(key[0], key[1], node.level + 1, (node.kind, node.id))
            order.append(child)
            queue.append(child)
    return order


def recommend(graph: BipartiteGraph, user_id: int, limit: int = 10) -> list[tuple[int, int]]:
    """Películas a distancia 3 que user_id no ha visto, ordenadas por nº de vecinos (dist. 2) que las calificaron.

    Devuelve [(movie_id, score)].
    """
    seen = set(graph.movies_of(user_id))

    # Nivel 2: usuarios que comparten al menos una película con user_id
    neighbors: set[int] = set()
    for movie_id in seen:
        neighbors.update(graph.users_of(movie_id))
    neighbors.discard(user_id)

    # Nivel 3: películas de esos usuarios que user_id aún no vio
    scores: Counter[int] = Counter()
    for v in neighbors:
        for movie_id in graph.movies_of(v):
            if movie_id not in seen:
                scores[movie_id] += 1

    return scores.most_common(limit)


def bfs_tree(graph: BipartiteGraph, source_user: int, max_depth: int = 3, branching: int = 2) -> dict:
    """Árbol BFS podado a `branching` hijos por nodo, pensado para visualizar en el frontend.

    Devuelve {"nodes": [...], "edges": [...]} listo para una librería de grafos (react-flow, vis, d3...).
    """
    visited: set[tuple[str, int]] = {("user", source_user)}
    nodes = [{"id": f"user-{source_user}", "kind": "user", "ref": source_user, "level": 0}]
    edges: list[dict] = []
    queue: deque[tuple[str, int, int]] = deque([("user", source_user, 0)])

    while queue:
        kind, ref, level = queue.popleft()
        if level >= max_depth:
            continue
        if kind == "user":
            candidates = sorted(graph.movies_of(ref).items(), key=lambda kv: -kv[1])
            child_kind = "movie"
        else:
            candidates = sorted(graph.users_of(ref).items(), key=lambda kv: -kv[1])
            child_kind = "user"

        added = 0
        for child_ref, rating in candidates:
            if added >= branching:
                break
            key = (child_kind, child_ref)
            if key in visited:
                continue
            visited.add(key)
            added += 1
            child_id = f"{child_kind}-{child_ref}"
            nodes.append({"id": child_id, "kind": child_kind, "ref": child_ref, "level": level + 1})
            edges.append({"source": f"{kind}-{ref}", "target": child_id, "rating": rating})
            queue.append((child_kind, child_ref, level + 1))

    return {"nodes": nodes, "edges": edges}
