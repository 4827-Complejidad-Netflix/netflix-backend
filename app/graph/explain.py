"""Explicación de las comunidades de G_U: qué películas y géneros comparten sus miembros.

Una comunidad se forma porque sus usuarios valoraron positivamente las mismas películas
(Jaccard alto entre sus conjuntos de vecinos en G_B). Estas funciones lo hacen visible:
- shared_movies: las películas que más miembros de la comunidad tienen en común.
- genre_profile: qué géneros pesan más en la comunidad que en la muestra completa.
- best_matches: el par más parecido de cada usuario aislado (por qué no alcanzó θ).
"""

from collections import Counter
from dataclasses import dataclass, field

from app.graph.bipartite import BipartiteGraph


@dataclass
class SharedMovie:
    movie_id: int
    users: list[int] = field(default_factory=list)  


@dataclass
class GenreShare:
    genre: str
    share: float  
    lift: float  


def shared_movies(graph: BipartiteGraph, members: list[int], limit: int = 8) -> list[SharedMovie]:
    """Películas valoradas por más miembros (al menos 2). O(Σ grado(u)) + ordenamiento."""
    holders: dict[int, list[int]] = {}
    for u in members:
        for m in graph.movies_of(u):
            holders.setdefault(m, []).append(u)
    common = [SharedMovie(m, sorted(us)) for m, us in holders.items() if len(us) >= 2]
    common.sort(key=lambda s: (-len(s.users), s.movie_id))
    return common[:limit]


def _genre_counts(graph: BipartiteGraph, users: list[int], genres_of: dict[int, list[str]]) -> tuple[Counter, int]:
    counts: Counter = Counter()
    total = 0
    for u in users:
        for m in graph.movies_of(u):
            total += 1
            counts.update(genres_of.get(m, []))
    return counts, total


def genre_profile(
    graph: BipartiteGraph,
    members: list[int],
    sample: list[int],
    genres_of: dict[int, list[str]],
    limit: int = 4,
) -> list[GenreShare]:
    """Géneros más frecuentes en la comunidad, con su peso relativo frente a toda la muestra."""
    counts, total = _genre_counts(graph, members, genres_of)
    base_counts, base_total = _genre_counts(graph, sample, genres_of)
    if total == 0 or base_total == 0:
        return []
    profile = []
    for genre, n in counts.most_common(limit):
        share = n / total
        base = base_counts[genre] / base_total
        profile.append(GenreShare(genre, round(share, 4), round(share / base, 2) if base else 0.0))
    return profile


def average_similarity(members: list[int], edges: list[tuple[int, int, float]]) -> tuple[float, int]:
    """Jaccard medio y número de aristas de G_U dentro de la comunidad."""
    inside = set(members)
    weights = [w for u, v, w in edges if u in inside and v in inside]
    return (round(sum(weights) / len(weights), 4) if weights else 0.0), len(weights)


def best_matches(users: list[int], all_pairs: list[tuple[int, int, float]]) -> dict[int, tuple[int, float]]:
    """Para cada usuario, su par con mayor Jaccard en la muestra (requiere los pares sin filtrar por θ)."""
    targets = set(users)
    best: dict[int, tuple[int, float]] = {}
    for u, v, w in all_pairs:
        for a, b in ((u, v), (v, u)):
            if a in targets and w > best.get(a, (0, -1.0))[1]:
                best[a] = (b, w)
    return best
