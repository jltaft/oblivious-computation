import math
import copy
from cryptography.fernet import Fernet
from utils import uniform_random, encrypt_block, decrypt_block

class Client:
    def __init__(self, N, L=None, B=32768, Z=4, initial_data=None):
        if N <= 0:
            raise ValueError(f"N={N} is not positive")
        self.h = math.ceil(math.log2(N))
        self.L = L if L is not None else N # L <= N is the maximum range size supported
        N = 1 << self.h # move N up to be a power of 2
        self.N = N # number of logical blocks, also number of leaf nodes
        self.l = math.ceil(math.log2(self.L)) # we have l + 1 PATH ORAMS labeled R_0, ..., R_l
        self.B = B # block size (in bits)
        self.Z = Z # capacity of each bucket (in blocks)
        self.cnt = [0] # global counter
        self.R = self._initialize_sub_orams(initial_data)

    def get_seeks(self):
        return sum([oram.get_seeks() for oram in self.R])
    
    def reset_seeks(self):
        for oram in self.R:
            oram.reset_seeks()

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
        a_0 = (a // (1 << i)) * (1 << i)
        D = {}
        for a_prime in [a_0, a_0 + (1 << i)]:
            if a_prime >= self.N:
                break
            Bs, p_prime = self.R[i].read_range(a_prime)
            for j in range(1 << i):
                try:
                    Bs[a_prime + j][1 + i] = (p_prime + j) % self.N
                except:
                    raise

            D = D | Bs
        # try:
        #     assert len(D) == 1 << (i + 1)
        # except:
        #     assert a_prime == self.N
        # update if write
        if op == "write":
            for j in range(r):
                D[a + j][0] = D_star[j]
        # Update stashes and evict in each tree
        for j in range(self.l + 1):                
            Rj = self.R[j]
            as_to_remove = {Ba for Ba in Rj.S.keys() if a_0 <= Ba < a_0 + len(D)}
            for a_to_remove in as_to_remove:
                del Rj.S[a_to_remove]
            Rj.S = Rj.S | D 
            Rj.batch_evict(len(D))

        self.cnt[0] += len(D)
        if op == "read":
            return D

    def _initialize_sub_orams(self, initial_data):
        # initialize positions
        positions = []
        for i in range(self.l + 1):
            position = []
            for j in range(0, self.N, 1 << i):
                position.append(uniform_random(self.N - 1))
                for k in range(1, 1 << i):
                    position.append((position[j] + k) % self.N)
            positions.append(position)
        
        data = {}
        from tqdm import tqdm
        for a in tqdm(range(self.N)):
            data[a] = [initial_data[a] if initial_data is not None else "", *[positions[i][a] for i in range(self.l + 1)]]
        # R = []
        # for i in tqdm(range(self.l + 1)):
        #     R.append(SubORAMClient(i, self.cnt, positions[i], data, self.N, self.h, B=self.B, Z=self.Z))
        # return R
        return [SubORAMClient(i, self.cnt, positions[i], copy.deepcopy(data), self.N, self.h, B=self.B, Z=self.Z) for i in tqdm(range(self.l + 1))]
        # need to move stash to server so that post-initialization there is not too much in stash


class SubORAMServer:
    def __init__(self, data, Z):
        self.data = data
        self.Z = Z
        self.ops = 0

    # i, j are bucket indices not blocks!
    def read_slice(self, i, j): # [i,j)
        self.ops += 1
        return self.data[i*self.Z:j*self.Z]
    
    # i, j are bucket indices not blocks!
    def write_slice(self, i, j, data): # [i,j)
        self.ops += 1
        self.data[i*self.Z:j*self.Z] = data

    def get_ops(self):
        return self.ops
    
    def reset_ops(self):
        self.ops = 0


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
        self.server = SubORAMServer([self._create_dummy_block() for _ in range(self.Z * ((1 << (self.h + 1)) - 1))], self.Z)
    
    def get_seeks(self):
        return self.server.get_ops()
    
    def reset_seeks(self):
        self.server.reset_ops()

    def _is_valid(self, block):
        a, data = block
        if a < 0 or a >= self.N:
            return False
        # for i in range(1, len(data)):
        #     if data[i] < 0 or data[i] >= self.N:
        #         return False
        return True

    def _create_dummy_block(self):
        return encrypt_block((-1, "dummy!"), self.B, self.f)

    def _read_buckets(self, j, start, length):
        start = start % (1 << j)
        end = (start + length) % (1 << j)
        # assert (start != end or length >= (1 << j))

        if start == end:
            end += (1 << j)
        if length >= (1 << j):
            encrypted_blocks = self.server.read_slice((1 << j) - 1 + 0, (1 << j) - 1 + (1 << j))
        elif start <= end:
            encrypted_blocks = self.server.read_slice((1 << j) - 1 + start, (1 << j) - 1 + end)
        else:
            encrypted_blocks = self.server.read_slice((1 << j) - 1 + start, (1 << j) - 1 + (1 << j)) + self.server.read_slice((1 << j) - 1 + 0, (1 << j) - 1 + end)
        decrypted_blocks = []
        for encrypted_block in encrypted_blocks:
            block = decrypt_block(encrypted_block, self.f)
            if self._is_valid(block):
                decrypted_blocks.append(block)
        return decrypted_blocks

    # pads with dummy blocks if needed
    def _write_buckets(self, j, start, length, buckets):
        start = start % (1 << j)
        end = (start + length) % (1 << j)
        if length >= (1 << j):
            encrypted_blocks = []
            for r in range(0, (1 << j)):
                bucket = buckets[r]
                encrypted_blocks += [encrypt_block(block, self.B, self.f) for block in bucket.items()]
                for _ in range(self.Z - len(bucket)):
                    encrypted_blocks.append(self._create_dummy_block())
            self.server.write_slice((1 << j) - 1 + 0, (1 << j) - 1 + (1 << j), encrypted_blocks)
        elif start <= end:
            encrypted_blocks = []
            for r in range(start, end):
                bucket = buckets[r]
                encrypted_blocks += [encrypt_block(block, self.B, self.f) for block in bucket.items()]
                for _ in range(self.Z - len(bucket)):
                    encrypted_blocks.append(self._create_dummy_block())
            self.server.write_slice((1 << j) - 1 + start, (1 << j) - 1 + end, encrypted_blocks)
        else:
            encrypted_blocks_1 = []
            encrypted_blocks_2 = []
            for r in range(start, (1 << j)):
                bucket = buckets[r]
                encrypted_blocks_1 += [encrypt_block(block, self.B, self.f) for block in bucket.items()]
                for _ in range(self.Z - len(bucket)):
                    encrypted_blocks_1.append(self._create_dummy_block())

            for r in range(0, end):
                bucket = buckets[r]
                encrypted_blocks_2 += [encrypt_block(block, self.B, self.f) for block in bucket.items()]
                for _ in range(self.Z - len(bucket)):
                    encrypted_blocks_2.append(self._create_dummy_block())
                
            self.server.write_slice((1 << j) - 1 + start, (1 << j) - 1 + (1 << j), encrypted_blocks_1)
            self.server.write_slice((1 << j) - 1 + 0, (1 << j) - 1 + end, encrypted_blocks_2)

    # block is now (a, (d, p_0, ..., p_l))
    # a must be a multiple of 2^i
    def read_range(self, a):
        result = {B[0]:B[1] for B in self.S.items() if a <= B[0] < a + (1 << self.i)}
        p = self.position[a]
        p_prime = uniform_random(self.N - 1)
        self.position[a] = p_prime
        for j in range(self.h + 1):
            V = self._read_buckets(j, p, (1 << self.i))
            for B in V:
                if a <= B[0] < a + (1 << self.i) and B[0] not in result and B[1][self.i + 1] == (p + B[0] - a) % self.N:
                    result.update([B])
        # return (copy.deepcopy(result), p_prime)
        return (result, p_prime)

    # def batch_evict(self, k):
    #     cnt = self.cnt[0]
    #     for j in range(self.h + 1):
    #         V = self._read_buckets(j, cnt, k)
    #         for B in V:
    #             a0 = (B[0] // ((1 << self.i))) * ((1 << self.i))
    #             if B[0] not in self.S.keys() and B[1][self.i + 1] == (self.position[a0] + B[0] - a0) % self.N:
    #                 self.S.update([B])

    #     # evict paths
    #     v = {j: ([None] * (1 << j)) for j in range(0, self.h + 1)}
    #     for j in range(self.h, -1, -1):
    #         start = cnt % (1 << j)
    #         end = (cnt + k) % (1 << j)
    #         if k >= (1 << j):
    #             r_range = range(0, (1 << j))
    #         elif start <= end:
    #             r_range = range(start, end)
    #         else:
    #             r_range = [*range(start, (1 << j)), *range(0, end)]
    #         for r in r_range:
    #             S_prime = {}
    #             for B in self.S.items():
    #                 if B[1][self.i + 1] % (1 << j) == r:
    #                     S_prime.update([B])
    #                     if len(S_prime) == self.Z:
    #                         break
    #             for a in S_prime.keys():
    #                 del self.S[a]
    #             v[j][r] = S_prime

    #     # write back buckets to server
    #     for j in range(self.h + 1):
    #         self._write_buckets(j, cnt, k, v[j])


    def batch_evict(self, k):
        cnt = self.cnt[0]

        # Fetch buckets from server into stash
        for j in range(self.h + 1):
            V = self._read_buckets(j, cnt, k)
            for a, data in V:
                a0 = (a // (1 << self.i)) * (1 << self.i)
                if a not in self.S and data[self.i + 1] == (self.position[a0] + a - a0) % self.N:
                    self.S[a] = data

        # Evict paths: bottom-up, grouping stash blocks once per level
        v = {j: ([None] * (1 << j)) for j in range(self.h + 1)}

        for j in range(self.h, -1, -1):
            m = 1 << j

            start = cnt % m
            end = (cnt + k) % m

            if k >= m:
                r_list = list(range(m))
            elif start < end:
                r_list = list(range(start, end))
            else:
                r_list = list(range(start, m)) + list(range(0, end))

            wanted = set(r_list)
            groups = {r: {} for r in r_list}

            mask = m - 1
            to_remove = set()

            # Scan stash once for this level
            for a, data in self.S.items():
                r = data[self.i + 1] & mask  # same as % (1 << j), but faster
                if r in wanted and len(groups[r]) < self.Z:
                    groups[r][a] = data
                    to_remove.add(a)

            # Remove selected blocks from stash
            for a in to_remove:
                del self.S[a]

            # Store buckets for writeback
            for r in r_list:
                v[j][r] = groups[r]

        # Write back buckets to server
        for j in range(self.h + 1):
            self._write_buckets(j, cnt, k, v[j])