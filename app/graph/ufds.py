"""Union-Find (UFDS) con compresión de caminos y unión por rango: O(α(n)) amortizado."""

from collections import defaultdict
from collections.abc import Hashable, Iterable


class UnionFind:
    def __init__(self, elements: Iterable[Hashable]):
        self.parent = {e: e for e in elements}
        self.rank = {e: 0 for e in self.parent}

    def find(self, x: Hashable) -> Hashable:
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        # Compresión de caminos
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: Hashable, b: Hashable) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True

    def groups(self) -> list[list[Hashable]]:
        buckets: dict[Hashable, list[Hashable]] = defaultdict(list)
        for e in self.parent:
            buckets[self.find(e)].append(e)
        return sorted(buckets.values(), key=len, reverse=True)
