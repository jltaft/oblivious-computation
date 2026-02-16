import random
import math
import json
import sys
from cryptography.fernet import Fernet
from path_oram_server import PathORAMServer as Server


class _InMemoryPositionMap:
    """position map stored in client memory (get/set by block id)"""

    def __init__(self, position_dict):
        self._position = position_dict

    def get(self, a):
        return self._position[a]

    def set(self, a, x):
        self._position[a] = x

    #necessary for batched updates 
    def set_many(self, updates):
        """updates: dict block_id -> leaf index"""
        for a, x in updates.items():
            self._position[a] = x

    def get_and_set(self, a, new_x):
        x = self._position[a]
        self._position[a] = new_x
        return x


class _RecursivePositionMap:
    """position map stored in a recursive ORAM as chunks. Each chunk holds E entries."""

    def __init__(self, N, L, E, recursive_oram, num_leaves):
        self.N = N
        self.L = L
        self.E = E
        self._oram = recursive_oram
        self._num_leaves = num_leaves  
        self._num_chunks = (N + E - 1) // E

    def get_and_set(self, a, new_x):
        chunk_id = a // self.E
        raw = self._oram.access("read", chunk_id)
        chunk = json.loads(raw) if isinstance(raw, str) else raw
        chunk = {int(k): v for k, v in chunk.items()}
        x = chunk.get(a, random.randint(0, self._num_leaves - 1))
        chunk[a] = new_x
        self._oram.access("write", chunk_id, json.dumps(chunk))
        return x

    def set(self, a, x):
        """Update position of block a to x (e.g. after evicting onto path to x)."""
        self.get_and_set(a, x)

    def set_many(self, updates):
        """updates: dict block_id -> leaf index. Batched by chunk to minimize ORAM accesses."""
        if not updates:
            return
        by_chunk = {}
        for a, x in updates.items():
            cid = a // self.E
            by_chunk.setdefault(cid, {})[a] = x
        for chunk_id, chunk_updates in by_chunk.items():
            raw = self._oram.access("read", chunk_id)
            chunk = json.loads(raw) if isinstance(raw, str) else raw
            chunk = {int(k): v for k, v in chunk.items()}
            for a, x in chunk_updates.items():
                chunk[a] = x
            self._oram.access("write", chunk_id, json.dumps(chunk))

    def initialize(self):
        """all position map chunks initialize with random leaf indices"""
        for chunk_id in range(self._num_chunks):
            start = chunk_id * self.E
            end = min(self.N, start + self.E)
            chunk = {a: random.randint(0, self._num_leaves - 1) for a in range(start, end)}
            self._oram.access("write", chunk_id, json.dumps(chunk))


def _tree_height(N, Z):
    return int(math.ceil(math.log(max(1, math.ceil(N / Z)), 2)))


def _entries_per_block(N, L, B):
    """How many (block_id, leaf) entries fit in B bits. Leaf in [0, 2^L-1]."""
    bits_per_entry = max(1, (N - 1).bit_length() + L)  # ceil(log2(N)) + L
    return max(1, B // bits_per_entry)


class Client:
    """Single-level Path ORAM. Position map is in-memory or provided by position_map."""

    def __init__(self, N, L=None, B=32768, Z=4, position_map=None):
        if N <= 0:
            raise ValueError(f"N={N} is not positive")
        # height is 0 of tree with just root node
        if L is None:
            L = int(math.ceil(math.log(max(1, math.ceil(N / Z)), 2)))
        total_N = (2 ** (L + 1) - 1) * Z
        if N > total_N:
            raise ValueError(f"N={N} is too big given L={L} and Z={Z} (total_N={total_N})")
       
        self.N = N  # total # blocks outsourced to server (excluding dummy blocks)
        self._total_N = total_N  # total # blocks stored on server (including dummy blocks)
        self.L = L  # height of binary tree
        self.B = B  # block size (in bits)
        self.Z = Z  # capacity of each bucket (in blocks)

        self.S = {}  # stash: block_id -> (data, position)
        if position_map is not None:
            self.position_map = position_map
            self.position = None  # no in-memory dict in recursive case
        else:
            pos_dict = self._initialize_position()
            self.position_map = _InMemoryPositionMap(pos_dict)
            self.position = pos_dict  # backward compat for tests

        # encryption/decryption
        key = Fernet.generate_key()
        self.f = Fernet(key)

        # client initializes dummy data and starts a new server with it
        self.server = Server(self._generate_initial_data())

    def access(self, op, a, new_data=None):
        # a is block id
        new_x = self._uniform_random(2 ** self.L - 1)
        x = self.position_map.get_and_set(a, new_x)

        # reads each bucket on the path and adds to stash (blocks carry their position)
        for l in range(self.L + 1):
            read = self._read_bucket(self._P(x, l))
            self.S = self.S | read

        if op == "write":
            if new_data is None:
                raise ValueError("write op needs new_data")
            entry = self.S.get(a)
            old_data = entry[0] if entry else None
            self.S[a] = (new_data, new_x)
        elif op == "read":
            try:
                old_data, _ = self.S[a]
            except KeyError as e:
                print(f"Block not found in stash {e}", file=sys.stderr)
                raise
        else:
            raise ValueError(f"Invalid op {op}")

        for l in range(self.L, -1, -1):
            S_prime = {}
            # choose min(|S_prime|, Z) blocks that belong on this bucket's path
            for a_prime in self.S.keys():
                _, pos_prime = self.S[a_prime]
                if self._P(x, l) == self._P(pos_prime, l):
                    S_prime[a_prime] = self.S[a_prime]
                    if len(S_prime) >= self.Z:
                        break
            # blocks are now on path P(x); keep position map in sync (batched)
            if S_prime:
                self.position_map.set_many({a_prime: x for a_prime in S_prime})
            for a_prime in S_prime.keys():
                del self.S[a_prime]
            self._write_bucket(self._P(x, l), S_prime)

        return old_data
    
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
        return self._encrypt_block((-1, "", -1))

    def _P(self, x, l):
        return (2 ** l - 1 + x // 2 ** (self.L - l)) * self.Z

    def _read_bucket(self, bucket):
        bucket_blocks = {}
        for i in range(self.Z):
            encrypted_block = self.server.read_block(bucket + i)
            a, data, pos = self._decrypt_block(encrypted_block)
            if a != -1:
                bucket_blocks[a] = (data, pos)
        return bucket_blocks

    def _write_bucket(self, bucket, data):
        # data: dict block_id -> (data, position)
        for i, (a_prime, (data_val, pos_val)) in enumerate(data.items()):
            encrypted_block = self._encrypt_block((a_prime, data_val, pos_val))
            self.server.write_block(bucket + i, encrypted_block)
        for i in range(len(data), self.Z):
            encrypted_block = self._create_dummy_block()
            self.server.write_block(bucket + i, encrypted_block)

    def _encrypt_block(self, block):
        # block: (a, data, pos) or (-1, "", -1) for dummy
        byte_block = json.dumps(block).encode("utf-8")
        padded_block = self._pad_block(byte_block)
        encrypted_block = self._encrypt(padded_block)
        return encrypted_block

    def _decrypt_block(self, block):
        padded_decrypted_byte_block = self._decrypt(block)
        decrypted_byte_block = self._depad_block(padded_decrypted_byte_block)
        decrypted_block = decrypted_byte_block.decode("utf-8")
        parsed = json.loads(decrypted_block)
        if len(parsed) == 2:
            a, data = parsed
            pos = -1
        else:
            a, data, pos = parsed
        return a, data, pos
    
    def _pad_block(self, block):
        if len(block) > self.B:
            raise ValueError(f"Block size {len(block)} is larger than B={self.B}")
        if len(block) == self.B:
            return block
        return block + b"\x01" + b"\x00" * (self.B - len(block) - 1)

    def _depad_block(self, block):
        return block.rstrip(b"\x00").removesuffix(b"\x01")

    def _encrypt(self, data, identity=False):
        return self.f.encrypt(data) if not identity else data

    def _decrypt(self, data, identity=False):
        return self.f.decrypt(data) if not identity else data


def recursiveClient(N, B=1<<15, Z=4):
    """Path ORAM with the position map stored recursively in smaller ORAM(s)"""
    L = _tree_height(N, Z)
    E = _entries_per_block(N, L, B)
    N_1 = (N + E - 1) // E

    if N_1 <= 1:
        return Client(N, B=B, Z=Z)

    recursive_oram = recursiveClient(N_1, B, Z)
    num_leaves = 2 ** L
    position_map = _RecursivePositionMap(N, L, E, recursive_oram, num_leaves)
    data_oram = Client(N, B=B, Z=Z, position_map=position_map)
    position_map.initialize()
    return data_oram
