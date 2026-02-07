import random
import math
import json
import sys
from server import Server


class Client:
    def __init__(self, N, L=None, B=32768, Z=4):
        if N <= 0:
            raise ValueError(f"N={N} is not positive")
        # height is 0 of tree with just root node
        if L is None:
            L = int(math.ceil(math.log(math.ceil(N // Z), 2))) # TODO double check this works
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

        # client initializes dummy data and starts a new server with it
        self.server = Server(self._generate_initial_data())

    def access(self, op, a, new_data=None):
        # a is block id
        x = self.position[a]
        self.position[a] = self._uniform_random(2 ** self.L - 1)
        for l in range(self.L + 1):
            read = (self._read_bucket(self._P(x, l)))
            self.S = self.S | read
        
        if op == "write":
            if new_data is None:
                raise ValueError("write op needs new_data")
            self.S[a] = new_data
            data = self.S.get(a) # None default if a is not in S
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
            print("before write server state: ", [self._decrypt_block(block) for block in self.server.data])
            print("selected blocks to write: ", S_prime)
            self._write_bucket(self._P(x, l), S_prime)
            print("after write server state: ", [self._decrypt_block(block) for block in self.server.data])
        
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
        return 2 ** l - 1 + x // 2 ** (self.L - l)

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

    def _write_bucket(self, bucket, data):
        for i, block in enumerate(data.items()):
            encrypted_block = self._encrypt_block(block)
            self.server.write_block(bucket + i, encrypted_block)
        for i in range(len(data), self.Z):
            encrypted_block = self._create_dummy_block()
            self.server.write_block(bucket + i, encrypted_block)

    def _encrypt_block(self, block): # block should be (a, data)
        byte_block = json.dumps(block).encode("utf-8")
        if len(byte_block) > self.B:
            raise ValueError(f"Block size {len(byte_block)} is larger than B={self.B}")
        padded_block = byte_block + b"\x00" * (self.B - len(byte_block)) # need to change (see _decrypt_block comment)
        encrypted_block = self._encrypt(padded_block)
        return encrypted_block

    def _decrypt_block(self, block):
        padded_decrypted_byte_block = self._decrypt(block)
        # TODO need a better way to remove padding
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
