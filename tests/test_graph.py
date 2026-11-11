from app.graph.bfs import bfs_levels, bfs_tree, recommend, recommend_from_movies
from app.graph.bipartite import BipartiteGraph
from app.graph.kruskal import kruskal
from app.graph.projection import build_projection, detect_communities, jaccard
from app.graph.ufds import UnionFind


def make_graph() -> BipartiteGraph:
    #   u1: m1, m2     u2: m1, m3     u3: m2, m3, m4     u4: m5
    g = BipartiteGraph()
    for u, m in [(1, 1), (1, 2), (2, 1), (2, 3), (3, 2), (3, 3), (3, 4), (4, 5)]:
        g.add_edge(u, m, 4.5)
    return g


def test_bfs_levels():
    levels = {(n.kind, n.id): n.level for n in bfs_levels(make_graph(), 1)}
    assert levels[("movie", 1)] == 1
    assert levels[("user", 2)] == 2
    assert levels[("movie", 3)] == 3
    assert ("user", 4) not in levels


def test_recommend_excludes_seen_movies():
    recs = dict(recommend(make_graph(), 1))
    assert 1 not in recs and 2 not in recs
    assert recs[3] == 2  # u2 y u3 la calificaron
    assert recs[4] == 1


def test_recommend_from_movies_explains_candidates():
    # Likes en m1: llegan u1 y u2 (nivel 2) y sus películas no vistas son m2 y m3 (nivel 3).
    result = recommend_from_movies(make_graph(), {1})
    assert result.similar_users == 2
    assert [(c.movie_id, c.score) for c in result.candidates] == [(2, 1), (3, 1)]
    assert all(c.via == {1: 1} for c in result.candidates)


def test_recommend_from_movies_counts_users_per_like():
    # Likes en m2 y m3: u3 tiene ambas y es el único que valoró m4.
    result = recommend_from_movies(make_graph(), {2, 3})
    by_movie = {c.movie_id: c for c in result.candidates}
    assert by_movie[4].score == 1
    assert by_movie[4].via == {2: 1, 3: 1}
    assert by_movie[1].score == 2  # u1 (vía m2) y u2 (vía m3)


def test_bfs_tree_branching():
    tree = bfs_tree(make_graph(), 3, max_depth=1, branching=2)
    assert len(tree["nodes"]) == 3
    assert len(tree["edges"]) == 2


def test_jaccard():
    assert jaccard({1, 2}, {2, 3}) == 1 / 3
    assert jaccard(set(), set()) == 0.0


def test_union_find():
    uf = UnionFind([1, 2, 3, 4])
    assert uf.union(1, 2)
    assert uf.union(2, 3)
    assert not uf.union(1, 3)
    assert uf.find(1) == uf.find(3)
    assert uf.groups() == [[1, 2, 3], [4]]


def test_kruskal_picks_heaviest_edges_without_cycles():
    edges = [(1, 2, 0.9), (2, 3, 0.8), (1, 3, 0.7), (3, 4, 0.1)]
    chosen, groups = kruskal([1, 2, 3, 4], edges, k=1)
    assert chosen == [(1, 2, 0.9), (2, 3, 0.8), (3, 4, 0.1)]  # (1,3) cerraría un ciclo
    assert len(groups) == 1


def test_kruskal_k_clusters_cuts_weakest_link():
    edges = [(1, 2, 0.9), (2, 3, 0.8), (3, 4, 0.1)]
    _, groups = kruskal([1, 2, 3, 4], edges, k=2)
    assert groups == [[1, 2, 3], [4]]


def test_communities():
    g = make_graph()
    edges = build_projection(g, [1, 2, 3, 4], theta=0.2)
    groups = detect_communities([1, 2, 3, 4], edges)
    assert sorted(groups[0]) == [1, 2, 3]
    assert groups[1] == [4]


def test_shared_movies_counts_members():
    from app.graph.explain import shared_movies

    # m1: u1, u2 · m2: u1, u3 · m3: u2, u3 · m4 y m5 solo tienen un usuario.
    result = shared_movies(make_graph(), [1, 2, 3])
    assert [(s.movie_id, s.users) for s in result] == [(1, [1, 2]), (2, [1, 3]), (3, [2, 3])]


def test_genre_profile_lift_against_sample():
    from app.graph.explain import genre_profile

    genres = {1: ["Drama"], 2: ["Drama"], 3: ["Comedy"], 4: ["Comedy"], 5: ["Horror"]}
    profile = genre_profile(make_graph(), [1], [1, 2, 3, 4], genres)
    # u1 solo valoró dramas; en la muestra, 4 de 8 valoraciones son Drama (lift = 1 / 0,5).
    assert profile[0].genre == "Drama" and profile[0].share == 1.0
    assert profile[0].lift == 2.0


def test_average_similarity_only_counts_internal_edges():
    from app.graph.explain import average_similarity

    edges = [(1, 2, 0.2), (2, 3, 0.4), (3, 4, 0.9)]
    assert average_similarity([1, 2, 3], edges) == (0.3, 2)


def test_best_matches_explain_isolated_users():
    from app.graph.explain import best_matches

    pairs = [(1, 2, 0.05), (1, 3, 0.08), (2, 3, 0.5)]
    assert best_matches([1], pairs) == {1: (3, 0.08)}
