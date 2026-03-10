import random
import time
import numpy as np
from basic_path_oram import Client as BasicClient
from re_recursive_path_oram import Client as RecursiveClient

def test_large_dataset(client_class, label, N, Z, B):
    print(f"=== Stress test large dataset ({label}) ===")

    client = client_class(N, Z=Z, B=B)
    print(f"Initialized with N={N}, Z={Z}, B={B} bits")

    truth = []
    # Write random data to all blocks
    start_time = time.time()
    for i in range(N):
        data = str(random.randint(0, 10))
        truth.append(data)
        # data = "X" * (B // 8 - 50)  # large payload string to fit in B bits
        client.access("write", i, data)
        if (i + 1) % 1000 == 0:
            print(f"Written {i+1}/{N} blocks")

    write_time = time.time() - start_time
    print(f"Completed writing {N} blocks in {write_time:.2f} seconds")

    # Randomized read order
    indices = list(range(N))
    random.shuffle(indices)
    start_time = time.time()

    for i, idx in enumerate(indices):
        val = client.access("read", idx)
        assert val == truth[idx]

        if (i + 1) % 1000 == 0:
            print(f"Read {i+1}/{N} blocks")

    read_time = time.time() - start_time
    print(f"Completed reading {N} blocks in {read_time:.2f} seconds")
    print(f"Stress test completed ({label})\n")


def test_large_both():
    N, Z, B = 10000, 4, 8192
    test_large_dataset(BasicClient, "Basic Path ORAM", N=N, Z=Z, B=B)
    test_large_dataset(RecursiveClient, "Recursive Path ORAM", N=N, Z=Z, B=B)
    print("All large-data tests passed.")


if __name__ == "__main__":
    test_large_both()
