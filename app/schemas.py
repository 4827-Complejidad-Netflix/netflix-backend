from pydantic import BaseModel


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
