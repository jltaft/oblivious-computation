# copy of path oram since we might need to modify it for this stuff
# (basic path oram for now)


import random
import math
import json
import sys
import numpy as np
from cryptography.fernet import Fernet

class SubORAMServer:
    def __init__(self, data, Z):
        self.data = data
        self.Z = Z

    # i, j are bucket indices not blocks!
    def read_slice(self, i, j): # [i,j)
        return self.data[i*self.Z:j*self.Z]
    
    # i, j are bucket indices not blocks!
    def write_slice(self, i, j, data): # [i,j)
        self.data[i*self.Z:j*self.Z] = data


class SubORAMClient:
    def __init__(self, i, cnt, position, data, N, h, B, Z):
        
        self.i = i # as in R_i
        self.N = N # total # blocks outsourced to server
        self.h = h # height of binary tree
        self.B = B # block size (in bits)
        self.Z = Z # capacity of each bucket (in blocks)
        self.cnt = cnt

        self.position = position # position map
        self.S = data # start with the initial data in stash
        # but will then immediately evict so we only have large amount of data in stash as part of initialization
        # so after initialization, normal stash bounds apply

        # encryption/decryption
        key = Fernet.generate_key()
        self.f = Fernet(key)

        # server
        self.server = SubORAMServer(np.array([self._create_dummy_block() for _ in range(self.Z * (2 ** (self.h + 1) - 1))]), self.Z)
    
    def _uniform_random(self, n):
        # return a uniform random int from 0 to n inclusive
        return random.randint(0, n)
    
    def _create_dummy_block(self):
        return self._encrypt_block((-1, "dummy!"))

    def _read_buckets(self, j, start, length):
        start = start % 2 ** j
        end = (start + length) % 2 ** j
        if start <= end:
            encrypted_blocks = self.server.read_slice(2 ** j - 1 + start, 2 ** j - 1 + end).tolist()
        else:
            encrypted_blocks = self.server.read_slice(2 ** j - 1 + start, 2 ** j - 1 + 2 ** j).tolist() + self.server.read_slice(2 ** j - 1 + 0, 2 ** j - 1 + end).tolist()
        decrypted_blocks = {}
        for encrypted_block in encrypted_blocks:
            a, data = self._decrypt_block(encrypted_block)
            if a != -1: # not dummy
                decrypted_blocks[a] = data
        return decrypted_blocks

    # pads with dummy blocks if needed
    def _write_buckets(self, j, start, length, buckets):
        start = start % 2 ** j
        end = (start + length) % 2 ** j
        if start <= end:
            encrypted_blocks = []
            for r in range(start, end):
                bucket = buckets[r]
                encrypted_blocks += [self._encrypt_block(block) for block in bucket.items()]
                for _ in range(self.Z - len(bucket)):
                    encrypted_blocks.append(self._create_dummy_block())
            self.server.write_slice(2 ** j - 1 + start, 2 ** j - 1 + end, np.array(encrypted_blocks))
        if end < start:
            encrypted_blocks_1 = []
            encrypted_blocks_2 = []
            for r in range(start, 2 ** j):
                bucket = buckets[r]
                encrypted_blocks_1 += [self._encrypt_block(block) for block in bucket.items()]
                for _ in range(self.Z - len(bucket)):
                    encrypted_blocks_1.append(self._create_dummy_block())

            for r in range(0, end):
                bucket = buckets[r]
                encrypted_blocks_2 += [self._encrypt_block(block) for block in bucket.items()]
                for _ in range(self.Z - len(bucket)):
                    encrypted_blocks_2.append(self._create_dummy_block())
                
            self.server.write_slice(2 ** j - 1 + start, 2 ** j - 1 + 2 ** j, np.array(encrypted_blocks_1))
            self.server.write_slice(2 ** j - 1 + 0, 2 ** j - 1 + end, np.array(encrypted_blocks_2))

    def _encrypt_block(self, block):
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
            Reads the range [a, a + 2i)
            a must be a multiple of 2^i
        """
        result = {B[0]:B[1] for B in self.S.items() if a <= B[0] < a + 2 ** self.i}
        p = self.position[a]
        p_prime = self._uniform_random(self.N - 1)
        self.position[a] = p_prime
        for j in range(self.h + 1):
            V = self._read_buckets(j, p, 2 ** self.i)
            for B in V.items():
                if a <= B[0] < a + 2 ** self.i and B[0] not in result:
                    result.update([B])
        return (result, p_prime)
            

    def batch_evict(self, k):
        """
            Perform k evictions as a batch
            to write back multiple blocks to the ORAM from the
            stash for each of the k evicted paths. Evictions occur
            in a deterministic order, and a global counter is used to
            maintain this order.
        """
        cnt = self.cnt[0]
        for j in range(self.h + 1):
            V = self._read_buckets(j, cnt, k)
            for B in V.items():
                if B[0] not in self.S.keys():
                    self.S.update([B])

        # evict paths
        v = {j: ([{}] * 2 ** j) for j in range(0, self.h + 1)}
        for j in range(self.h, -1, -1):
            start = cnt % 2 ** j
            end = (cnt + k) % 2 ** j
            if start <= end:
                r_range = range(start, end)
            else:
                r_range = [*range(start, 2 ** j), *range(0, end)]
            for r in r_range:
                S_prime = {}
                for B in self.S.items():
                    if B[1][self.i+1] % 2 ** j == r:
                        S_prime.update([B])
                        if len(S_prime) == self.Z:
                            break
                for a in S_prime.keys():
                    del self.S[a]
                v[j][r] = S_prime

        # write back buckets to server
        for j in range(self.h + 1):
            self._write_buckets(j, cnt, k, v[j])
