import random
from server import Server

class Client:
    def __init__(self, N, L, B=32768, Z=4):
        # check that N is not too big given L and Z
        if N > L * Z:
            raise ValueError("N is too big given L and Z")

        self.N = N
        self.L = L
        self.B = B
        self.Z = Z

        self.position = {} # position map
        self.server = Server()

    def access(self, op, a, new_data=None):
        # a is block id
        x = self.position(a)
        self.position(a) = self.uniform(self.L - 1)
        S = {}
        for i in range(self.L):
            S = S | (self.read_bucket(self.position[x]))
        
        if op == "write":
            S[a] = new_data
        elif op == "read":
            data = S[a]
        else:
            raise ValueError("Invalid op")
        
        for l in range(self.L, 0, -1):
            S_new = 
        


    def uniform(self, n):
        return random.randint(0, n)
    
    def read_bucket(self):
        # return a set of tuples (id, data)

        pass

    def write_bucket(self):
