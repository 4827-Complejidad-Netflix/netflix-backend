from app.graph.bfs import bfs_levels, bfs_tree, recommend
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
