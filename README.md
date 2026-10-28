# netflix-backend

API en **FastAPI** del sistema de recomendación de películas basado en grafos.
Se consume desde el frontend en Next.js (repositorio aparte).

- **Dataset:** MovieLens `ml-latest-small` (GroupLens). Solo se usan calificaciones positivas (`rating >= 4.0`).
- **G_B:** grafo bipartito usuario–película con listas de adyacencia.
- **BFS (3 niveles):** usuario → películas → usuarios similares → películas candidatas.
- **G_U + UFDS:** proyección usuario–usuario por Jaccard (fuerza bruta) y comunidades con Union-Find
  (compresión de caminos + unión por rango).
- **Kruskal (voraz):** árbol de expansión máxima sobre G_U; se detiene al quedar `k` comunidades
  (agrupamiento por enlace simple). O(E log E).

## Puesta en marcha

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
python scripts/download_dataset.py
copy .env.example .env            # opcional
uvicorn app.main:app --reload
```

Docs interactivas: http://localhost:8000/docs

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Healthcheck |
| GET | `/api/movies?q=&genre=&sort=popular\|title\|year&limit=&offset=` | Catálogo paginado |
| GET | `/api/movies/genres` | Lista de géneros |
| GET | `/api/movies/{id}` | Detalle (incluye `tmdb_id` / `imdb_id` para pósters) |
| GET | `/api/users` | IDs de usuarios con calificaciones positivas |
| GET | `/api/users/{id}` | Películas que le gustaron al usuario |
| GET | `/api/users/{id}/recommendations?limit=` | Recomendaciones vía BFS |
| GET | `/api/users/{id}/bfs?depth=3&branching=2` | Árbol BFS (`nodes`/`edges`) para visualizar |
| GET | `/api/graph/stats` | Métricas de G_B (nodos, aristas, densidad, grado) |
| GET | `/api/graph/communities?theta=0.10&sample_size=25&seed=` | Proyección G_U + comunidades UFDS |
| GET | `/api/graph/communities/kruskal?k=3&sample_size=25&seed=` | Kruskal voraz: k comunidades + bosque de expansión máxima |

Los endpoints de grafo devuelven `{ nodes, edges }` para pintarlos directamente con react-flow, vis-network o d3.

## Estructura

```
app/
  main.py            # FastAPI + CORS + carga del dataset al arrancar
  core/config.py     # Settings (.env)
  data/store.py      # Carga de CSV y construcción de G_B
  graph/             # Algoritmos: bipartite, bfs, projection (Jaccard), ufds
  api/               # Routers: movies, users, graph
  schemas.py         # Modelos Pydantic de respuesta
scripts/download_dataset.py
tests/
```

## Tests

```bash
pytest
```

## Frontend (Next.js)

Configura en el proyecto de Next.js:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

y añade su origen a `CORS_ORIGINS` si no es `http://localhost:3000`.
