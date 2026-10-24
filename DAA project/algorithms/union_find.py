from typing import Dict, Iterable

class DisjointSet:
    """
    Disjoint Set Union (DSU) data structure with:
    - Path compression in find()
    - Union by rank in union()
    Amortized complexity per operation: O(alpha(V)) where alpha is the inverse Ackermann function.
    """
    def __init__(self, elements: Iterable[str]):
        self.parent: Dict[str, str] = {}
        self.rank: Dict[str, int] = {}
        self.num_components: int = 0
        for elem in elements:
            self.parent[elem] = elem
            self.rank[elem] = 0
            self.num_components += 1

    def find(self, i: str) -> str:
        """Finds representative root with two-pass path compression."""
        if i not in self.parent:
            raise KeyError(f"Element '{i}' not in DisjointSet.")
        
        root = i
        while root != self.parent[root]:
            root = self.parent[root]
        
        # Path compression pass
        curr = i
        while curr != root:
            nxt = self.parent[curr]
            self.parent[curr] = root
            curr = nxt
            
        return root

    def union(self, i: str, j: str) -> bool:
        """
        Unions components containing i and j using union by rank.
        Returns True if a merge occurred (i and j were in disjoint components),
        False if they were already in the same component (cycle detected).
        """
        root_i = self.find(i)
        root_j = self.find(j)

        if root_i == root_j:
            return False

        # Union by rank: attach smaller tree under root of larger tree
        if self.rank[root_i] < self.rank[root_j]:
            self.parent[root_i] = root_j
        elif self.rank[root_i] > self.rank[root_j]:
            self.parent[root_j] = root_i
        else:
            self.parent[root_j] = root_i
            self.rank[root_i] += 1

        self.num_components -= 1
        return True

    def connected(self, i: str, j: str) -> bool:
        """Returns True if i and j belong to the same connected component."""
        return self.find(i) == self.find(j)

