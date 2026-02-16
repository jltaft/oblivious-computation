import math
from path_oram import PathORAMClient

class SubORAM:
    def __init__(self, N, B, Z):
        self.path_oram = PathORAMClient(N, B=B, Z=Z)
        self.N = N
        self.B = B
        self.Z = Z

    def read_range(self, a):
        """
            Takes as input a logical address a and
            returns the 2
            i blocks in the range [a, a + 2i
            ) from the
            ORAM. Here a must be a multiple of 2
            i
            , as in a = b · 2
            i
        """
        pass

    def batch_evict(self, k):
        """
            Perform k evictions as a batch
            to write back multiple blocks to the ORAM from the
            stash for each of the k evicted paths. Evictions occur
            in a deterministic order, and a global counter is used to
            maintain this order.
        """
        pass


class RORAMClient:
    def __init__(self, N, L=None, B=32768, Z=4):
        if N <= 0:
            raise ValueError(f"N={N} is not positive")
       
        self.N = N # total # blocks outsourced to server (excluding dummy blocks)
        self.L = L if L is not None else N # L <= N is the maximum range size supported
        self.l = math.ceil(math.log2(self.L)) # we have l + 1 PATH ORAMS labeled R_0, ..., R_l
        self.B = B # block size (in bits)
        self.Z = Z # capacity of each bucket (in blocks)
        self.R = [SubORAM(N, B=B, Z=Z) for i in range(self.l + 1)]

    def access(self, id, r):
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
        a_1 = id // 2 ** i
        a_2 = (a_1 + 2 ** i) % self.N
        
        read_blocks = self.R[i].read_range(a_1) | self.R[i].read_range(a_2)
        
