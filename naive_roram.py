import numpy as np
from basic_path_oram import Client as BasicClient

class Client:
    def __init__(self, N, L=None, B=32768, Z=4, initial_data=None):
        self.L = L if L is not None else N  # L <= N is the maximum range size supported
        self.client = BasicClient(N, B=B, Z=Z, initial_data=initial_data)

    def nice_read(self, a, r):
        data = np.array([self.client.access("read", a + i) for i in range(r)])
        return data

    def nice_write(self, a, r, D_star):
        for i in range(r):
            self.client.access("write", a + i, D_star[i])
        # return old data here if needed

    def get_seeks(self):
        return self.client.get_seeks()
    
    def reset_seeks(self):
        self.client.reset_seeks()