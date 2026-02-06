class Block:
    def __init__(self, a=None, data=None):
        if a is None:
            pass
            # initialize dummy a
        if data is None:
            pass
            # initialize dummy data
        self.a = a
        self.data = data


class Bucket:
    def __init__(self, Z):
        self.data = [Block() for _ in range(Z)]
        self.left = None
        self.right = None

    def read_bucket(bucket):
        # client reads all Z blocks (including any dummy blocks) from the bucket stored on the server
        # return a set of tuples (id, data)
        tuples = {}
        for _ in range(Z):
            tuples.add(a, bucket.data)
            # will add decryption
        return tuples

    def write_bucket(bucket, blocks):
        # client writes the blocks "blocks" into the specified bucket on the server
        pass

class Tree:
    def __init__(self, N, L, Z):
        self.N = N
        self.L = L
        self.Z = Z

        level = [Bucket()] # starts at the root
        for _ in range(L):
            for b in level:
                next_level = []
                b.left = Bucket(Z)
                b.right = Bucket(Z)
                next_level.append(b.left)
                next_level.append(b.right)
            level = next_level
        self.leaves = level

    def P(x, l):
        pass