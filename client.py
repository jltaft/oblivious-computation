import random
import math
from server import Server


class Client:
    def __init__(self, N, L=None, B=32768, Z=4):
        # check that N is not too big given L and Z

        if N <= 0:
            raise ValueError(f"N={N} is not positive")
        if L is None:
            L = int(math.ceil(math.log(math.ceil(N // Z), 2))) + 1 # TODO double check this works
        total_N = (2 ** L - 1) * Z
        if N > total_N:
            raise ValueError(f"N={N} is too big given L={L} and Z={Z} (total_N={total_N})")
       
        self.N = N # total # blocks outsourced to server (excluding dummy blocks)
        self._total_N = total_N # total # blocks stored on server (including dummy blocks)
        self.L = L # height of binary tree
        self.B = B # block size (in bits)
        self.Z = Z # capacity of each bucket (in blocks)

        self.S = {} # stash
        self.position = self._initialize_position() # position map

        # client initializes dummy data and starts a new server with it
        self.server = Server(self._generate_initial_data())

    def access(self, op, a, new_data=None):
        # a is block id
        x = self.position(a)
        self.position[a] = self._uniform_random(self.L - 1)
        for l in range(self.L):
            S = S | (self._read_bucket(self._P(x, l)))
        
        if op == "write":
            S[a] = new_data
            # a might not be in S (ex if all blocks were dummy)
            data = S.get(a) # None default
        elif op == "read":
            try:
                data = S[a]
            except KeyError as e:
                print(f"Block not found in stash {e}")
                raise
        else:
            raise ValueError(f"Invalid op {op}")
        
        for l in range(self.L, -1, -1):
            S_prime = {}
            # choose min(|S_prime}, Z) blocks from S_prime
            for a_prime in S.keys():
                if self._P(x, l) == self._P(self.position[a_prime], l):
                    S_prime[a_prime] = S.pop[a_prime]
                    if len(S_prime) >= self.Z:
                        break
            self._write_bucket(self._P(x, l), S_prime)
        
        return data
    
    def _initialize_position(self):
        # returns an initizlied position map
        position = {}
        for i in range(self.N):
            position[i] = self._uniform_random(2 ** self.L - 1)
        return position

    def _uniform_random(self, n):
        # return a uniform random int from 0 to n inclusive
        return random.randint(0, n)
    
    def _create_dummy_block(self):
        pass
    
    def _generate_initial_data(self, N, L, B, Z):
        pass

    def _P(self, x, l):
        pass
    
    def _read_bucket():
        pass

    def _write_bucket():
        pass

    def _encrypt(self, data):
        pass

    def _decrypt(self, data):
        pass