import math
import random
import copy
from roram.sub_oram import SubORAMClient


class RORAMClient:
    def __init__(self, N, L=None, B=32768, Z=4):
        if N <= 0:
            raise ValueError(f"N={N} is not positive")
        self.h = math.ceil(math.log2(N))
        self.L = L if L is not None else N # L <= N is the maximum range size supported
        N = 2 ** self.h # move N up to be a power of 2
        self.N = N # number of logical blocks, also number of leaf nodes
        self.l = math.ceil(math.log2(self.L)) # we have l + 1 PATH ORAMS labeled R_0, ..., R_l
        self.B = B # block size (in bits)
        self.Z = Z # capacity of each bucket (in blocks)
        self.cnt = [0] # global counter
        self.R = self._initialize_sub_orams()

    def access(self, a, r, op, D_star=None):
        if r > self.L:
            raise ValueError(f"Range size r={r} is greater than max range size supported L={self.L}")
        i = math.ceil(math.log2(r))
        a_0 = (a // (2 ** i)) * 2 ** i
        D = {}
        for a_prime in [a_0, a_0 + 2 ** i]:
            Bs, p_prime = self.R[i].read_range(a_prime) # read_range returns (result, p_prime)
            for j in range(2 ** i):
                Bs[a_prime + j][1 + i] = p_prime + j
            D = D | Bs
        
        # update if write
        if op == "write":
            for j in range(r):
                D[a + j][0] = D_star[j]
        # Update stashes and evict in each tree
        for j in range(self.l + 1):                
            Rj = self.R[j]
            as_to_remove = set()
            for a_to_maybe_remove in Rj.S.keys():
                if a_0 <= a_to_maybe_remove < a_0 + 2 ** (i + 1):
                    as_to_remove.add(a_to_maybe_remove)
            for a_to_remove in as_to_remove:
                del Rj.S[a_to_remove]
            Rj.S = Rj.S | D
            Rj.batch_evict(2 ** (i + 1))

        self.cnt[0] += 2 ** (i + 1)
        if op == "read":
            return D
        
    def _print_debug(self, i):
        Ri = self.R[i]
        print(f'HERE IS SERVER for {i}: {[Ri._decrypt_block(block) for block in Ri.server.read_slice(0, len(Ri.server.data)) ]}')
        print(f"Here is the stash for {i}: {Ri.S}")

    def _uniform_random(self, n):
        # return a uniform random int from 0 to n inclusive
        return random.randint(0, n)
    
    def _initialize_sub_orams(self):
        # initialize positions
        positions = []
        for i in range(self.l + 1):
            position = []
            for j in range(0, self.N, 2 ** i):
                position.append(self._uniform_random(self.N - 1))
                for k in range(1, 2 ** i):
                    position.append((position[j] + k) % self.N)
            positions.append(position)
        
        data = {}
        for a in range(self.N):
            data[a] = ["", *[positions[i][a] for i in range(self.l + 1)]]
        return [SubORAMClient(i, self.cnt, positions[i], copy.deepcopy(data), self.N, self.h, B=self.B, Z=self.Z) for i in range(self.l + 1)]
        # need to move stash to server so that post-initialization there is not too much in stash
