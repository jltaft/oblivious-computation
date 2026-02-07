import random
import math
import json
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
            data = S.get(a) # None default if a is not in S
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
        # returns an initialized position map
        position = {}
        for i in range(self.N):
            position[i] = self._uniform_random(2 ** self.L - 1) # 0 to num leafs - 1 (inclusive)
        return position
    
    def _uniform_random(self, n):
        # return a uniform random int from 0 to n inclusive
        return random.randint(0, n)
    
    def _generate_initial_data(self):
        return [self._create_dummy_block() for _ in range(self._total_N)]
    
    def _create_dummy_block(self):
        return self._encrypt_block(-1, "")

    def _P(self, x, l):
        pass
    
    def _read_bucket():
        pass

    def _write_bucket():
        pass

    def _encrypt_block(self, a, data):
        block = json.dumps((a, data)).encode("utf-8")
        padded_block = self._pad(block, self.B)
        if len(block) > self.B:
            raise ValueError(f"Block size {len(block)} is larger than B={self.B}")
        padded_block = block + b"\x00" * (self.B - len(block)) # need to change (see _decrypt_block comment)
        encrypted_block = self._encrypt(padded_block)
        return encrypted_block

    def _decrypt_block(self, block):
        padded_decrypted_byte_block = self._decrypt(block)
        # need a better way to remove padding
        # I saw something that last byte should be the amount of padding,
        # but what if amount of padding is more than 255?
        # Do we need to choose how many trailing bytes represent amount of padding based on total_N?
        # for now, just removing trailing \x00 but it's bad
        decrypted_byte_block = padded_decrypted_byte_block.rstrip(b"\x00")
        decrypted_block = decrypted_byte_block.decode("utf-8")
        a, data = json.loads(decrypted_block)
        return a, data

    def _encrypt(self, data):
        return data # for now, identity

    def _decrypt(self, data):
        return data # for now, identity