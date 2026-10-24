from typing import Dict, Iterable

class DisjointSet:
    """
    Disjoint Set Union (DSU) data structure with:
    - Path compression in find()
    - Union by rank in union()
    
    Academic Complexity:
    - Time: O(alpha(V)) amortized per operation where alpha is the inverse Ackermann function.
    - Space: O(V) auxiliary space for parent and rank arrays.
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
        """Finds representative root with path compression."""
        if i not in self.parent:
            raise KeyError(f"Element '{i}' not in DisjointSet.")
        
        root = i
        while root != self.parent[root]:
            root = self.parent[root]
        
        # Two-pass path compression
        curr = i
        while curr != root:
            nxt = self.parent[curr]
            self.parent[curr] = root
            curr = nxt
            
        return root

    def union(self, i: str, j: str) -> bool:
        """
        Unions sets containing i and j by rank.
        Returns True if merged (disjoint), False if in same set (cycle).
        """
        root_i = self.find(i)
        root_j = self.find(j)

        if root_i == root_j:
            return False

        if self.rank[root_i] < self.rank[root_j]:
            self.parent[root_i] = root_j
        elif self.rank[root_i] > self.rank[root_j]:
            self.parent[root_j] = root_i
        else:
            self.parent[root_j] = root_i
            self.rank[root_i] += 1

        self.num_components -= 1
        return True

