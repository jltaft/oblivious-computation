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
        # height is 0 of tree with just root node
        if L is None:
            L = int(math.ceil(math.log(max(1, math.ceil(N / Z)), 2)))
        total_N = (2 ** (L + 1) - 1) * Z
        if N > total_N:
            raise ValueError(f"N={N} is too big given L={L} and Z={Z} (total_N={total_N})")
       
        self.N = N # total # blocks outsourced to server (excluding dummy blocks)
        self._total_N = total_N # total # blocks stored on server (including dummy blocks)
        self.L = L # height of binary tree
        self.B = B # block size (in bits)
        self.Z = Z # capacity of each bucket (in blocks)

        self.S = {} # stash
        self.position = self._initialize_position() # position map

        # encryption/decryption
        key = Fernet.generate_key()
        self.f = Fernet(key)

        # client initializes dummy data and starts a new server with it
        self.server = Server(self._generate_initial_data())

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
        return self._encrypt_block((-1, ""))

    def _P(self, x, l):
        return (2 ** l - 1 + x // 2 ** (self.L - l)) * self.Z

    def _read_bucket(self, bucket):
        bucket_blocks = {}
        for i in range(self.Z):
            encrypted_block = self.server.read_block(bucket + i)
            a, data = self._decrypt_block(encrypted_block)
            # TODO for now not storing dummy blocks in stash
            # need to check if this is ok, since paper did say

            # For ReadBucket(bucket),
            # the client reads all Z blocks (including any dummy blocks) from the bucket stored on the server.
            # Blocks are decrypted as they are read

            # but since we need to reencrypt dummy blocks anyways especially after the dummy block is popped from the stash
            # may as well not store it?

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
