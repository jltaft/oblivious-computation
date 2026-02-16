import math
from roram.sub_oram import SubORAMClient


class RORAMClient:
    def __init__(self, N, L=None, B=32768, Z=4):
        if N <= 0:
            raise ValueError(f"N={N} is not positive")
       
        self.N = N # total # blocks outsourced to server (excluding dummy blocks)
        self.L = L if L is not None else N # L <= N is the maximum range size supported
        self.l = math.ceil(math.log2(self.L)) # we have l + 1 PATH ORAMS labeled R_0, ..., R_l
        self.B = B # block size (in bits)
        self.Z = Z # capacity of each bucket (in blocks)
        self.cnt = [0]
        self.R = [SubORAMClient(i, self.cnt, self.l, N, B=B, Z=Z) for i in range(self.l + 1)]
        

    def access(self, a, r, op, D_star=None):
        """
            Given a range of size r beginning at logical
            identifier id, with ⌈log2
            r⌉ = i, run Ri
            .ReadRange(a1)
            and Ri
            .ReadRange(a2) with a1 = ⌊id/2
            i
            ⌋ and a2 =
            (a1 + 2i
            ) mod N.

            The updated data blocks are then appended to the stash
            of all ℓ + 1 sub-ORAMs. Then, for each Rj , call
            Rj .BatchEvict(2i+1
            ,stash).
        """
        if r > self.L:
            raise ValueError(f"Range size r={r} is greater than max range size supported L={self.L}")
        i = math.ceil(math.log2(r))
        a_0 = (a // (2 ** i)) * 2 ** i
        D = {}
        for a_prime in range(a_0, a_0 + 2 ** i):
            Bs, p_prime = self.R[i].read_range(a_prime) # read_range returns (result, p_prime)

            for j in range(2 ** i):
                if a_prime + j not in Bs:
                    Bs[a_prime + j] = ["", *[-1] * ((self.l) + 1)]
                Bs[a_prime + j][1 + i] = p_prime + j
            
            D = D | Bs
        
        # update if write
        if op == "write":
            for j in range(r):
                Bs[a_prime + j][1] = D_star[j]

        # Update stashes and evict in each tree
        for j in range(self.l + 1):                
            Rj = self.R[j]
            for block in Rj.S.items():
                if a_0 <= block[0] < a_0 + 2 ** (i + 1):
                    Rj.S[block[0]] = Bs[block[0]]
            Rj.S = Rj.S | Bs
            Rj.batch_evict(2**(i+1))

        self.cnt[0] += 2 ** (i + 1)

        if op == "read":
            return D
        
    def print_debug(self):
        for i in range(self.l + 1):
            Ri = self.R[i]
            # print(f'HERE IS SERVER for {i}: {[Ri._decrypt_block(Ri.server.read_block(idk)) for idk in range(Ri._total_N)]}')
            print(f"Here is the stash for {i}: {Ri.S}")
