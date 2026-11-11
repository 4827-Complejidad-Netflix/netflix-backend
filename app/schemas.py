from pydantic import BaseModel, Field


class MovieOut(BaseModel):
    id: int
    title: str
    year: int | None
    genres: list[str]
    imdb_id: str | None
    tmdb_id: int | None
    positive_ratings: int = 0


class PaginatedMovies(BaseModel):
    total: int
    items: list[MovieOut]


class RatedMovie(BaseModel):
    movie: MovieOut
    rating: float


class UserOut(BaseModel):
    id: int
    positive_ratings: int
    liked: list[RatedMovie]


class Recommendation(BaseModel):
    movie: MovieOut
    score: int  # nº de usuarios similares (distancia 2 en G_B) que la calificaron positivamente


class GraphNode(BaseModel):
    id: str
    kind: str
    ref: int
    level: int
    label: str


class GraphEdge(BaseModel):
    source: str
    target: str
    rating: float | None = None
    weight: float | None = None


class GraphOut(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class SharedMovieOut(BaseModel):
    movie: MovieOut
    users: list[int]  # miembros de la comunidad que la valoraron positivamente


class GenreShareOut(BaseModel):
    genre: str
    share: float  # fracción de las valoraciones positivas de la comunidad con este género
    lift: float  # share en la comunidad / share en la muestra (> 1: más que el promedio)


class Community(BaseModel):
    id: int
    users: list[int]
    # Por qué se formó: similitud interna y lo que sus miembros tienen en común.
    avg_similarity: float = 0.0  # Jaccard medio de las aristas de G_U dentro de la comunidad
    internal_edges: int = 0
    shared_movies: list[SharedMovieOut] = []
    genres: list[GenreShareOut] = []


class IsolatedUser(BaseModel):
    user: int
    best_match: int | None  # usuario de la muestra con mayor Jaccard (None si no comparte ninguna película)
    similarity: float  # ese Jaccard: quedó aislado porque no alcanza el umbral


class CommunitiesOut(BaseModel):
    theta: float
    sample: list[int]
    communities: list[Community]
    isolated: list[int]
    isolated_details: list[IsolatedUser] = []
    graph: GraphOut


class KruskalOut(BaseModel):
    k: int
    total_similarity: float  # suma de Jaccard de las aristas elegidas por Kruskal
    sample: list[int]
    communities: list[Community]
    isolated: list[int]
    isolated_details: list[IsolatedUser] = []
    graph: GraphOut  # solo las aristas del bosque de expansión máxima


class SharedOut(BaseModel):
    """Películas en común entre dos usuarios: el motivo de su arista en G_U."""

    u: int
    v: int
    similarity: float  # Jaccard = |común| / |unión|
    shared_count: int
    union_count: int
    movies: list[MovieOut]  # las más populares primero


class GraphStats(BaseModel):
    users: int
    movies: int
    nodes: int
    edges: int
    density: float
    avg_degree: float
    total_ratings: int
    min_rating: float


class LikesIn(BaseModel):
    liked: list[int] = Field(min_length=1, max_length=200)  # ids de películas con "me gusta"
    limit: int = Field(50, ge=1, le=200)


class CandidateVia(BaseModel):
    movie: MovieOut  # película con "me gusta" desde la que se llegó a la candidata
    users: int  # usuarios similares que valoraron positivamente ambas


class Candidate(BaseModel):
    movie: MovieOut
    score: int  # nº de usuarios similares (distancia 2 en G_B) que la calificaron positivamente
    via: list[CandidateVia]  # de qué likes viene, más usuarios primero (máx. 3)


class LikesRecommendations(BaseModel):
    liked: list[MovieOut]  # likes reconocidos (los ids desconocidos se ignoran)
    ignored: list[int]  # ids que no existen en el catálogo
    similar_users: int  # usuarios alcanzados en el nivel 2 del BFS
    total_candidates: int  # películas alcanzadas en el nivel 3 (antes de aplicar limit)
    candidates: list[Candidate]
