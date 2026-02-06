import random
from server import Server


class Client:
    def __init__(self, N, L, B=32768, Z=4):
        # check that N is not too big given L and Z
        if False: # if N > (2 ** (L-1) * Z)?
            raise ValueError("N is too big given L and Z")

        self.N = N
        self.L = L
        self.B = B
        self.Z = Z

        self.S = {} # stash
        self.position = {} # position map
        for i in range(N):
            self.position[i] = self._uniform(2 ** L - 1)
        self.server = Server(N, L, B, Z)

    def access(self, op, a, new_data=None):
        # a is block id
        x = self.position(a)
        self.position[a] = self._uniform(self.L - 1)
        for i in range(self.L):
            S = S | (self.read_bucket(self.position[x]))
        
        if op == "write":
            S[a] = new_data
        elif op == "read":
            data = S[a]
        else:
            raise ValueError("Invalid op")
        
        for l in range(self.L, 0, -1):
            S_prime = {}
            for (a_prime, data_prime) in S:
                if self.server.P(x, l) == self.server.P(self.position[a_prime], l):
                    S_prime[a_prime] = data_prime
            S_prime = _choose_n_blocks(min(len(S_prime), self.Z))
        
    def _uniform(self, n):
        return random.randint(0, n)

    def _choose_n_blocks(n):
        # choose n blocks randomly
        pass

    def _encrypt(self, data):
        pass

    def _decrypt(self, data):
        pass