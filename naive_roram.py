import numpy as np
from basic_path_oram import Client as BasicClient

class Client:
    def __init__(self, N, B=2**15, Z=4):
        self.client = BasicClient(N, B=B, Z=Z)

    def __init__(self, N, L=None, B=32768, Z=4):
        self.L = L if L is not None else N # L <= N is the maximum range size supported
        self.client = BasicClient(N, B=B, Z=Z)

    def nice_read(self, a, r):
        data = np.array([self.client.access("read", a + i) for i in range(r)])
        return data
    
    def nice_write(self, a, r, D_star):
        data = {self.client.access("write", a + i, D_star[i]) for i in range(r)}
        # return data # uncomment to return old data