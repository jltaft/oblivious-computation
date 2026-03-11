import math
import sys
import numpy as np
from cryptography.fernet import Fernet
from abc import ABC, abstractmethod # for position maps
from utils import uniform_random, encrypt_block, decrypt_block

class Server:
    def __init__(self, data):
        self.data = data
    
    def read_block(self, i):
        return self.data[i]
    
    def write_block(self, i, block):
        self.data[i] = block
    
def _tree_height(N, Z):
    return int(math.ceil(math.log(max(1, math.ceil(N / Z)), 2)))

# 8 * math.log10(2 ** L) rather than math.log2(2 ** L) because we convert to string,
# math.log10(2 ** L) should count chars and multiply by 8 bits per char
# need to pad each entry to be (8 * math.log10(2 ** L)) exactly for accessing logic
def _recursive_entry_size(L):
    return 8 * max(1, math.ceil(math.log10(2 ** L)))

# blocks are json of (a, x, data) right now, encrypted with Fernet then put into a bytestring
# Add 2048 bits to account for adding a, x, converting to json, and Fernet encoding (even though it should be less than this)
def _entries_per_block(L, B):
    """How many (block_id, leaf) entries fit in B bit. Leaf in [0, 2^L-1]."""
    return max(1, (B - 2048) // _recursive_entry_size(L))

class PositionMap(ABC):
    @abstractmethod
    def get_and_set(self, a):
        pass

class InMemoryPositionMap(PositionMap):
    def __init__(self, N, L):
        position = {}
        for i in range(N):
            position[i] = uniform_random(2 ** L - 1)
        self.L = L
        self.position = position

    def get_and_set(self, a, new_x):
        x = self.position[a]
        self.position[a] =  new_x
        return x


class ORAMPositionMap(PositionMap):
    def __init__(self, N, B, Z, max_client_size):
        self.L = _tree_height(N, Z)
        self.E = _entries_per_block(self.L, B)
        next_N = math.ceil(N / self.E)
        self.oram = Client(next_N, B=B, Z=Z, max_client_size=max_client_size)

        for i in range(next_N):
            string_val_size = _recursive_entry_size(self.L) // 8
            block = "".join([str(uniform_random(2 ** self.L - 1)).zfill(string_val_size) for _ in range(self.E)])

            self.oram.access("write", i, block)

    def get_and_set(self, a, new_x):
        string_val_size = _recursive_entry_size(self.L) // 8
        val = str(new_x).zfill(string_val_size)
        result = int(self.oram.access("write", a // self.E, val, recursive=True, a_block_index=a % self.E, string_val_size=string_val_size))
        return result

class Client:
    def __init__(self, N, B=2**15, Z=4, max_client_size=2**4):
        # print(f'client with N={N}')
        if N <= 0:
            raise ValueError(f"N={N} is not positive")
        
        # height is 0 of tree with just root node
        L = _tree_height(N, Z)
        total_N = (2 ** (L + 1) - 1) * Z
        if N > total_N:
            raise ValueError(f"N={N} is too big given L={self.L} and Z={Z} (total_N={total_N})")
       
        self.N = N # total # blocks outsourced to server (excluding dummy blocks)
        self._total_N = total_N # total # blocks stored on server (including dummy blocks)
        self.L = L # height of binary tree
        self.B = B # block size (in bits)
        self.Z = Z # capacity of each bucket (in blocks)

        self.S = {} # stash

        if N <= max_client_size:
            self.position_map = InMemoryPositionMap(N, self.L)
        else:
            self.position_map = ORAMPositionMap(N, B, Z, max_client_size)

        # encryption/decryption
        key = Fernet.generate_key()
        self.f = Fernet(key)

        # client initializes dummy data and starts a new server with it
        self.server = Server(np.array(self._generate_initial_data()))

    def access(self, op, a, new_data=None, recursive=False, a_block_index=None, string_val_size=None):
        # print(f'before access in oram N={self.N}')
        # print('before Stash:')
        # for a in self.S.keys():
        #     print(f'a: {a}, p: {self.S[a][0]}, val: {self.S[a][1]}')
        
        # get path of a and assign new randomized path
        new_x = uniform_random(2 ** self.L - 1)
        x = self.position_map.get_and_set(a, new_x)
        
        # reads each bucket on the path and adds to stash
        for l in range(self.L + 1):
            read = (self._read_bucket(self._P(x, l)))
            self.S = self.S | read

        # print(f'after access in oram N={self.N}')
        # print('after Stash:')
        # for a in self.S.keys():
        #     print(f'a: {a}, p: {self.S[a][0]}, val: {self.S[a][1]}')

        if op == "write":
            if new_data is None:
                raise ValueError("write op needs new_data")
            data = self.S.get(a) # None default if a is not in S
            if data is not None:
                _, data = data
            elif recursive:
                raise KeyError(f"a {a} did not exist in data recursive case")

            if recursive:
                new_data = data[:a_block_index * string_val_size] + new_data + data[(a_block_index + 1) * string_val_size:]
                data = data[a_block_index * string_val_size: (a_block_index + 1) * string_val_size]
            self.S[a] = (new_x, new_data)
        elif op == "read":
            try:
                _, data = self.S[a]
            except KeyError as e:
                print(f"Block not found in stash {e}", file=sys.stderr)
                raise
            self.S[a] = (new_x, data)
        else:
            raise ValueError(f"Invalid op {op}")
        for l in range(self.L, -1, -1):
            S_prime = {}
            # choose min(|S_prime}, Z) blocks from S_prime
            for a_prime, (x_prime, _) in self.S.items():
                if self._P(x, l) == self._P(x_prime, l):
                    S_prime[a_prime] = self.S[a_prime]
                    if len(S_prime) >= self.Z:
                        break
            for a_prime in S_prime.keys():
                del self.S[a_prime]

            self._write_bucket(self._P(x, l), S_prime)
        
        return data
    
    def _generate_initial_data(self):
        return [self._create_dummy_block() for _ in range(self._total_N)]
    
    def _create_dummy_block(self):
        return encrypt_block((-1, -1, ""), self.B, self.f)

    def _P(self, x, l):
        return (2 ** l - 1 + x // 2 ** (self.L - l)) * self.Z

    def _read_bucket(self, bucket):
        bucket_blocks = {}
        for i in range(self.Z):
            encrypted_block = self.server.read_block(bucket + i)
            a, x, data = decrypt_block(encrypted_block, self.f)

            if a != -1: # not dummy
                bucket_blocks[a] = (x, data)

        return bucket_blocks

    # _write_bucket write data back to bucket and pads with dummy blocks if needed
    def _write_bucket(self, bucket, data):
        for i, block in enumerate(data.items()):
            encrypted_block = encrypt_block((block[0], block[1][0], block[1][1]), self.B, self.f)
            self.server.write_block(bucket + i, encrypted_block)
        for i in range(len(data), self.Z):
            encrypted_block = self._create_dummy_block()
            self.server.write_block(bucket + i, encrypted_block)
