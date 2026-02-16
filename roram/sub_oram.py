# copy of path oram since we might need to modify it for this stuff
# (basic path oram for now)


import random
import math
import json
import sys
import numpy as np
from cryptography.fernet import Fernet
from path_oram_server import PathORAMServer

class SubORAMServer:
    def __init__(self, data):
        self.data = data
    
    def read_block(self, i):
        return self.data[i]
    
    def write_block(self, i, block):
        self.data[i] = block


class SubORAMClient:
    def __init__(self, i, cnt, l, N, L=None, B=32768, Z=4):
        if N <= 0:
            raise ValueError(f"N={N} is not positive")
        # height is 0 of tree with just root node
        if L is None:
            L = int(math.ceil(math.log(max(1, math.ceil(N / Z)), 2)))
        total_N = (2 ** (L + 1) - 1) * Z
        if N > total_N:
            raise ValueError(f"N={N} is too big given L={L} and Z={Z} (total_N={total_N})")
       
        self.i = i # as in R_i
        self.N = N # total # blocks outsourced to server (excluding dummy blocks)
        self._total_N = total_N # total # blocks stored on server (including dummy blocks)
        self.L = L # height of binary tree (L for leaf node level)
        self.B = B # block size (in bits)
        self.Z = Z # capacity of each bucket (in blocks)
        self.cnt = cnt
        self.l = l

        self.S = {} # stash
        self.position = self._initialize_position() # position map

        # encryption/decryption
        key = Fernet.generate_key()
        self.f = Fernet(key)

        # client initializes dummy data and starts a new server with it
        self.server = PathORAMServer(np.array(self._generate_initial_data()))

    def access(self, op, a, new_data=None):
        # a is block id
        x = self.position[a]
        self.position[a] = self._uniform_random(2 ** self.L - 1)
        
        # reads each bucket on the path and adds to stash
        for l in range(self.L + 1):
            read = (self._read_bucket(self._P(x, l)))
            self.S = self.S | read
        

        if op == "write":
            if new_data is None:
                raise ValueError("write op needs new_data")
            data = self.S.get(a) # None default if a is not in S
            self.S[a] = new_data
        elif op == "read":
            try:
                data = self.S[a]
            except KeyError as e:
                print(f"Block not found in stash {e}", file=sys.stderr)
                raise
        else:
            raise ValueError(f"Invalid op {op}")
        for l in range(self.L, -1, -1):
            S_prime = {}
            # choose min(|S_prime}, Z) blocks from S_prime
            for a_prime in self.S.keys():
                if self._P(x, l) == self._P(self.position[a_prime], l):
                    S_prime[a_prime] = self.S[a_prime]
                    if len(S_prime) >= self.Z:
                        break
            for a_prime in S_prime.keys():
                del self.S[a_prime]

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
        return self._encrypt_block((-1, ["", *[-1] * ((self.l) + 1)]))

    # change to use bit reversed order, etc.
    def _P(self, x, l):
        return (2 ** l - 1 + x // 2 ** (self.L - l)) * self.Z

    def _read_bucket(self, bucket):
        bucket_blocks = {}
        for i in range(self.Z):
            encrypted_block = self.server.read_block(bucket + i)
            a, data = self._decrypt_block(encrypted_block)
            if a != -1: # not dummy
                bucket_blocks[a] = data

        return bucket_blocks

    # _write_bucket write data back to bucket and pads with dummy blocks if needed
    def _write_bucket(self, bucket, data):
        for i, block in enumerate(data.items()):
            encrypted_block = self._encrypt_block(block)
            self.server.write_block(bucket + i, encrypted_block)
        for i in range(len(data), self.Z):
            encrypted_block = self._create_dummy_block()
            self.server.write_block(bucket + i, encrypted_block)

    def _encrypt_block(self, block): # block should be (a, data)
        byte_block = json.dumps(block).encode("utf-8")
        padded_block = self._pad_block(byte_block)
        encrypted_block = self._encrypt(padded_block)
        return encrypted_block

    def _decrypt_block(self, block):
        padded_decrypted_byte_block = self._decrypt(block)
        decrypted_byte_block = self._depad_block(padded_decrypted_byte_block)
        decrypted_block = decrypted_byte_block.decode("utf-8")
        a, data = json.loads(decrypted_block)
        return a, data
    
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
    
    # block is now (a, (d, p_0, ..., p_l))
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
        result = {}
        for B in self.S.items():
            if a <= B[0] < a + 2 ** self.i:
                result[B[0]] = B[1]
        p = self.position[a]
        self.position[a] = self._uniform_random(2 ** self.L - 1) # or should it be N? need to verify
        for j in range(self.L + 1): # j from 0 to h (0 is root, h (what we call L) is the level of the leaf nodes)
            # for _P(x, l), x is the path and l is the level
            V = {}
            for t in self._get_possible_t(p, 2 ** self.i, j):
                B = self._read_bucket(self._P(t, j))
                V = V | B
            for B in V:
                if a <= B[0] < a + 2 ** self.i:
                    if B[0] not in result:
                        result[B[0]] = B[1]
        return (result, self.position[a])
            

    def batch_evict(self, k):
        """
            Perform k evictions as a batch
            to write back multiple blocks to the ORAM from the
            stash for each of the k evicted paths. Evictions occur
            in a deterministic order, and a global counter is used to
            maintain this order.
        """
        for j in range(self.L):
            V = {}
            for t in self._get_possible_t(self.cnt[0], k, j):
                B = self._read_bucket(self._P(t, j))
                V = V | B
            for B in V:
                if B[0] not in self.S:
                    self.S[B[0]] = B[1]

        # evict paths and write buckets back to server
        for j in range(self.L, -1):
            for r in self._get_possible_t(self.cnt[0], k, j):
                done_blocks = 0
                for block in self.S:
                    # block = (a, (d, p_0, p_1, ..., p_l))
                    if r == block[1][self.i + 1] % (2 ** j):
                        done_blocks += 1
                        self._write_bucket(self._P(r, j), block)
                    if done_blocks == self.Z:
                        break
        # TODO!!!: actually batch up the write backs to make use of batching...


    def _get_possible_t(self, start, k, j):
        possible_t = set()
        t = start
        possible_t.add(t)
        for i in range(k):
            t = (start + i) % (2 ** j)
            possible_t.add(t)
            if t == (start - 1) % (2 ** j):
                break
        return possible_t
