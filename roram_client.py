# for now using basic until we have verified recursive version is 100% good
from basic_path_oram_client import PathORAMClient

class rORAMClient():
    def __init__(self, N, L=None, B=32768, Z=4):
        self.
        self.client = PathORAMClient(10)


import random
import math
import json
import sys
from cryptography.fernet import Fernet
from path_oram_server import Server


class PathORAMClient:
    def __init__(self, N, L=None, B=32768, Z=4):
        if N <= 0:
            raise ValueError(f"N={N} is not positive")
       
        self.N = N # total # blocks outsourced to server (excluding dummy blocks)
        self.L = L if L is not None else N # L <= N is the maximum range size supported
        self.l = math.ceil(math.log2(self.L)) # we have l + 1 PATH ORAMS labeled R_0, ..., R_l
        self.B = B # block size (in bits)
        self.Z = Z # capacity of each bucket (in blocks)
        self.path_orams = []
        for i in range(self.l + 1):
            self.path_orams.append(PathORAMClient(N, B=B, Z=Z))

