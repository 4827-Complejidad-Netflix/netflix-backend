"""Grafo bipartito usuario–película G_B = (U ∪ M, E, w)."""

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class BipartiteGraph:
    # Listas de adyacencia: usuario -> {película: rating} y película -> {usuario: rating}
    user_adj: dict[int, dict[int, float]] = field(default_factory=lambda: defaultdict(dict))
    movie_adj: dict[int, dict[int, float]] = field(default_factory=lambda: defaultdict(dict))

    def add_edge(self, user_id: int, movie_id: int, rating: float) -> None:
        self.user_adj[user_id][movie_id] = rating
        self.movie_adj[movie_id][user_id] = rating

    def movies_of(self, user_id: int) -> dict[int, float]:
        return self.user_adj.get(user_id, {})

    def users_of(self, movie_id: int) -> dict[int, float]:
        return self.movie_adj.get(movie_id, {})

    def has_user(self, user_id: int) -> bool:
        return user_id in self.user_adj

    @property
    def num_users(self) -> int:
        return len(self.user_adj)

    @property
    def num_movies(self) -> int:
        return len(self.movie_adj)

    @property
    def num_edges(self) -> int:
        return sum(len(m) for m in self.user_adj.values())

    def stats(self) -> dict:
        nodes = self.num_users + self.num_movies
        edges = self.num_edges
        possible = self.num_users * self.num_movies
        return {
            "users": self.num_users,
            "movies": self.num_movies,
            "nodes": nodes,
            "edges": edges,
            "density": edges / possible if possible else 0.0,
            "avg_degree": 2 * edges / nodes if nodes else 0.0,
        }
