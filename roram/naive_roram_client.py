# naive rORAM using path oram
from path_oram import PathORAMClient

class NaiveRORAMClient:
    def __init__(self, N, L=None, B=32768, Z=4):
        if N <= 0:
            raise ValueError(f"N={N} is not positive")
       
        self.N = N # total # blocks outsourced to server (excluding dummy blocks)
        self.L = L if L is not None else N # L <= N is the maximum range size supported
        self.B = B # block size (in bits)
        self.Z = Z # capacity of each bucket (in blocks)
        self.path_oram = PathORAMClient(N, B=B, Z=Z)

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
        pass