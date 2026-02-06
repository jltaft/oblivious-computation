
from tree import Tree

class Server:
    def __init__(self, N, L, B, Z):
        self.N = N
        self.L = L
        self.B = B
        self.Z = Z
        self.tree = Tree(N, L, Z)

    def P(self, x, l):
        return self.tree.P(x, l)