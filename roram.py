import math
import copy
import numpy as np
from cryptography.fernet import Fernet
from utils import uniform_random, encrypt_block, decrypt_block

class Client:
    def __init__(self, N, L=None, B=32768, Z=4):
        if N <= 0:
            raise ValueError(f"N={N} is not positive")
        self.h = math.ceil(math.log2(N))
        self.L = L if L is not None else N # L <= N is the maximum range size supported
        N = 2 ** self.h # move N up to be a power of 2
        self.N = N # number of logical blocks, also number of leaf nodes
        self.l = math.ceil(math.log2(self.L)) # we have l + 1 PATH ORAMS labeled R_0, ..., R_l
        self.B = B # block size (in bits)
        self.Z = Z # capacity of each bucket (in blocks)
        self.cnt = [0] # global counter
        self.R = self._initialize_sub_orams()

    def nice_read(self, a, r):
        data = self.access(a, r, "read")
        return [data[i][0] for i in range(a, a + r)]
    
    def nice_write(self, a, r, D_star):
        try:
            data = self.access(a, r, "write", D_star)
        except:
            print('error')
            for o in self.R:
                print(o.cnt)
            raise
        # return [data[i][0] for i in range(a, a + r)] # uncomment to return the old data

    def access(self, a, r, op, D_star=None):
        if r > self.L:
            raise ValueError(f"Range size r={r} is greater than max range size supported L={self.L}")
        i = math.ceil(math.log2(r))
        a_0 = (a // (2 ** i)) * 2 ** i
        D = {}
        for a_prime in [a_0, a_0 + 2 ** i]:
            if a_prime >= self.N:
                break
            Bs, p_prime = self.R[i].read_range(a_prime)
            for j in range(2 ** i):
                try:
                    Bs[a_prime + j][1 + i] = (p_prime + j) % self.N
                except:
                    raise
                    # try:
                    #     Bs[a_prime + j + 2**j][1 + i] = (p_prime + j) % self.N
                    # except:
                    #     print(f'Bs: {Bs}')
                    #     print(f'i: {i}')
                    #     print(f'a_prime: {a_prime}')
                        
                    #     raise

            D = D | Bs
        try:
            assert len(D) == 2 * 2 ** i
        except:
            assert a_prime == self.N
        # update if write
        if op == "write":
            for j in range(r):
                D[a + j][0] = D_star[j]
        # Update stashes and evict in each tree
        for j in range(self.l + 1):                
            Rj = self.R[j]
            # as_to_remove = {Ba for Ba in Rj.S.keys() if a_0 <= Ba < a_0 + 2 ** (i + 1)}
            as_to_remove = {Ba for Ba in Rj.S.keys() if a_0 <= Ba < a_0 + len(D)}
            for a_to_remove in as_to_remove:
                del Rj.S[a_to_remove]
            Rj.S = Rj.S | copy.deepcopy(D)
            # Rj.S = Rj.S | D
            # Rj.batch_evict(2 ** (i + 1))
            Rj.batch_evict(len(D))

        self.cnt[0] += len(D) # 2 ** (i + 1)
        if op == "read":
            return D

    def _initialize_sub_orams(self):
        # initialize positions
        positions = []
        for i in range(self.l + 1):
            position = []
            for j in range(0, self.N, 2 ** i):
                position.append(uniform_random(self.N - 1))
                for k in range(1, 2 ** i):
                    position.append((position[j] + k) % self.N)
            positions.append(position)
        
        data = {}
        for a in range(self.N):
            data[a] = ["", *[positions[i][a] for i in range(self.l + 1)]]
        return [SubORAMClient(i, self.cnt, positions[i], copy.deepcopy(data), self.N, self.h, B=self.B, Z=self.Z) for i in range(self.l + 1)]
        # need to move stash to server so that post-initialization there is not too much in stash


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
    
    def _is_valid(self, block):
        a, data = block
        if a < 0 or a >= self.N:
            return False
        for i in range(1, len(data)):
            if data[i] < 0 or data[i] >= self.N:
                return False
        return True

    def _create_dummy_block(self):
        return encrypt_block((-1, "dummy!"), self.B, self.f)

    def _read_buckets(self, j, start, length, p=None):
        # rs = {t % 2 ** j for t in range(start, start + length)}
        # decrypted_blocks = {}
        # for r in rs:
        #     encrypted_blocks = self.server.read_slice(2 ** j - 1 + r, 2 ** j -1 + r + 1)
        #     for encrypted_block in encrypted_blocks:
        #         a, data = decrypt_block(encrypted_block, self.f)
        #         if a == -1:
        #             continue
        #         try:
        #             assert a not in decrypted_blocks
        #         except:
        #             print(f'old: {(a, decrypted_blocks[a])}')
        #             print(f'new: {(a, data)}')
        #             raise
        #         if self._is_valid((a, data)): # not dummy and not already there
        #             decrypted_blocks[a] = data
        # return decrypted_blocks
    
        start = start % 2 ** j
        end = (start + length) % 2 ** j
        assert (start != end or length >= 2 ** j)

        if start == end:
            end += 2 ** j
        if length >= 2 ** j:
            encrypted_blocks = self.server.read_slice(2 ** j - 1 + 0, 2 ** j - 1 + 2 ** j).tolist()
        elif start <= end:
            encrypted_blocks = self.server.read_slice(2 ** j - 1 + start, 2 ** j - 1 + end).tolist()
        else:
            encrypted_blocks = self.server.read_slice(2 ** j - 1 + start, 2 ** j - 1 + 2 ** j).tolist() + self.server.read_slice(2 ** j - 1 + 0, 2 ** j - 1 + end).tolist()
        decrypted_blocks = {}
        for encrypted_block in encrypted_blocks:
            block = decrypt_block(encrypted_block, self.f)
            if self._is_valid(block) and block[0] not in decrypted_blocks: # not dummy and not already there
                decrypted_blocks.update([block])
        return decrypted_blocks

    # pads with dummy blocks if needed
    def _write_buckets(self, j, start, length, buckets):
        start = start % 2 ** j
        end = (start + length) % 2 ** j
        if length >= 2 ** j:
            encrypted_blocks = []
            for r in range(0, 2 ** j):
                bucket = buckets[r]
                encrypted_blocks += [encrypt_block(block, self.B, self.f) for block in bucket.items()]
                for _ in range(self.Z - len(bucket)):
                    encrypted_blocks.append(self._create_dummy_block())
            self.server.write_slice(2 ** j - 1 + 0, 2 ** j - 1 + 2 ** j, np.array(encrypted_blocks))
        elif start <= end:
            encrypted_blocks = []
            for r in range(start, end):
                bucket = buckets[r]
                encrypted_blocks += [encrypt_block(block, self.B, self.f) for block in bucket.items()]
                for _ in range(self.Z - len(bucket)):
                    encrypted_blocks.append(self._create_dummy_block())
            self.server.write_slice(2 ** j - 1 + start, 2 ** j - 1 + end, np.array(encrypted_blocks))
        else:
            encrypted_blocks_1 = []
            encrypted_blocks_2 = []
            for r in range(start, 2 ** j):
                bucket = buckets[r]
                encrypted_blocks_1 += [encrypt_block(block, self.B, self.f) for block in bucket.items()]
                for _ in range(self.Z - len(bucket)):
                    encrypted_blocks_1.append(self._create_dummy_block())

            for r in range(0, end):
                bucket = buckets[r]
                encrypted_blocks_2 += [encrypt_block(block, self.B, self.f) for block in bucket.items()]
                for _ in range(self.Z - len(bucket)):
                    encrypted_blocks_2.append(self._create_dummy_block())
                
            self.server.write_slice(2 ** j - 1 + start, 2 ** j - 1 + 2 ** j, np.array(encrypted_blocks_1))
            self.server.write_slice(2 ** j - 1 + 0, 2 ** j - 1 + end, np.array(encrypted_blocks_2))

    
    # block is now (a, (d, p_0, ..., p_l))
    # a must be a multiple of 2^i
    def read_range(self, a):
        result = {B[0]:B[1] for B in self.S.items() if a <= B[0] < a + 2 ** self.i}
        p = self.position[a]
        p_prime = uniform_random(self.N - 1)
        self.position[a] = p_prime
        for j in range(self.h + 1):
            V = self._read_buckets(j, p, 2 ** self.i, p)
            for B in V.items():
                if a <= B[0] < a + 2 ** self.i and B[0] not in result:
                    result.update([B])
        return (copy.deepcopy(result), p_prime)
        # return (result, p_prime)

    def batch_evict(self, k):
        cnt = self.cnt[0]
        for j in range(self.h + 1):
            V = self._read_buckets(j, cnt, k, self.position[cnt])
            for B in V.items():
                if B[0] not in self.S.keys():
                    self.S.update([B])

        # for j in range(self.h, -1, -1):
        #     rs = {t % 2 ** j for t in range(cnt, cnt + k)}
        #     for r in rs:
        #         S_prime = {}
        #         for a, data in self.S.items():
        #             # print(data)
        #             if data[self.i + 1] % 2 ** j == r:
        #                 S_prime[a] = data
        #                 if len(S_prime) == self.Z:
        #                     break
        #         for a in S_prime.keys():
        #             del self.S[a]
        #         bucket = S_prime
        #         # print(f'bucket{bucket}')
        #         encrypted_bucket = [encrypt_block(block, self.B, self.f) for block in bucket.items()]
        #         for _ in range(self.Z - len(bucket)):
        #             encrypted_bucket.append(self._create_dummy_block())

        #         # server.write_slice uses bucket indices, not block indices:
        #         self.server.write_slice(2 ** j - 1 + r, 2 ** j - 1 + r + 1, np.array(encrypted_bucket))
                # self.server.data[2 ** j - 1 + r: 2 ** j - 1 + r + self.Z] = np.array(encrypted_bucket)

        # evict paths
        v = {j: ([None] * 2 ** j) for j in range(0, self.h + 1)}
        for j in range(self.h, -1, -1):
            start = cnt % 2 ** j
            end = (cnt + k) % 2 ** j
            if k >= 2 ** j:
                r_range = range(0, 2 ** j)
            elif start <= end:
                r_range = range(start, end)
            else:
                r_range = [*range(start, 2 ** j), *range(0, end)]
            for r in r_range:
                S_prime = {}
                for B in self.S.items():
                    if B[1][self.i + 1] % 2 ** j == r:
                        S_prime.update([B])
                        if len(S_prime) == self.Z:
                            break
                for a in S_prime.keys():
                    del self.S[a]
                v[j][r] = S_prime

        # write back buckets to server
        for j in range(self.h + 1):
            self._write_buckets(j, cnt, k, v[j])
