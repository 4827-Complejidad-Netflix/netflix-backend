"""Carga del dataset MovieLens en memoria y construcción de G_B (una sola vez al arrancar)."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from app.graph.bipartite import BipartiteGraph


@dataclass
class Movie:
    id: int
    title: str
    year: int | None
    genres: list[str]
    imdb_id: str | None
    tmdb_id: int | None


@dataclass
class DataStore:
    movies: dict[int, Movie]
    graph: BipartiteGraph
    total_ratings: int


def _split_title(raw: str) -> tuple[str, int | None]:
    raw = raw.strip()
    if raw.endswith(")") and raw[-6:-5] == "(" and raw[-5:-1].isdigit():
        return raw[:-6].strip(), int(raw[-5:-1])
    return raw, None


def load_store(data_dir: Path, min_rating: float) -> DataStore:
    ratings_path = data_dir / "ratings.csv"
    if not ratings_path.exists():
        raise FileNotFoundError(
            f"No se encontró {ratings_path}. Ejecuta: python scripts/download_dataset.py"
        )

    movies_df = pd.read_csv(data_dir / "movies.csv")
    links_df = pd.read_csv(data_dir / "links.csv", dtype={"imdbId": str})
    ratings_df = pd.read_csv(ratings_path)

    links = links_df.set_index("movieId")
    movies: dict[int, Movie] = {}
    for row in movies_df.itertuples(index=False):
        title, year = _split_title(row.title)
        genres = [] if row.genres == "(no genres listed)" else row.genres.split("|")
        movie_id = int(row.movieId)
        imdb = tmdb = None
        if movie_id in links.index:
            link = links.loc[movie_id]
            imdb = f"tt{link.imdbId}" if pd.notna(link.imdbId) else None
            tmdb = int(link.tmdbId) if pd.notna(link.tmdbId) else None
        movies[movie_id] = Movie(movie_id, title, year, genres, imdb, tmdb)

    graph = BipartiteGraph()
    positive = ratings_df[ratings_df["rating"] >= min_rating]
    for u, m, r in positive[["userId", "movieId", "rating"]].itertuples(index=False):
        graph.add_edge(int(u), int(m), float(r))

    return DataStore(movies=movies, graph=graph, total_ratings=len(ratings_df))
