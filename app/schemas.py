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


class Community(BaseModel):
    id: int
    users: list[int]


class CommunitiesOut(BaseModel):
    theta: float
    sample: list[int]
    communities: list[Community]
    isolated: list[int]
    graph: GraphOut


class KruskalOut(BaseModel):
    k: int
    total_similarity: float  # suma de Jaccard de las aristas elegidas por Kruskal
    sample: list[int]
    communities: list[Community]
    isolated: list[int]
    graph: GraphOut  # solo las aristas del bosque de expansión máxima


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
