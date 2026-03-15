import random
import time
import numpy as np
from naive_roram import Client as NaiveRangeClient
from roram import Client as RORAMClient

def test_large_dataset(client_class, label, num_writes, num_reads, N, Z, B):
    print(f"=== Stress test range large dataset ({label}) ===")

    client = client_class(N, Z=Z, B=B)
    print(f"Initialized with N={N}, Z={Z}, B={B} bits")

    truth = np.zeros(N, dtype=int).astype(str)

    # initialize with '0's
    print('writing all zeros')
    client.nice_write(0, N, truth)

    # make num_writes random range writes
    print(f'starting {num_writes} write queries')
    start_time = time.time()
    for i in range(num_writes):
        a = random.randint(0, N - 1)
        end = random.randint(a, N - 1) # inclusive
        r = end - a + 1
        slice = np.random.randint(0, 10, r).astype(str) # r-size array of chars 0-9
        client.nice_write(a, r, slice)
        truth[a:end+1] = slice

        if (i + 1) % 5 == 0:
            print(f"Performed {i+1}/{num_writes} write queries")

    write_time = time.time() - start_time
    print(f"Completed {num_writes} writes in {write_time:.2f} seconds")

    # make num_reads random range reads
    print(f'starting {num_reads} read queries')
    start_time = time.time()
    for i in range(num_reads):
        a = random.randint(0, N - 1)
        end = random.randint(a, N - 1) # inclusive
        r = end - a + 1
        result = client.nice_read(a, r)

        assert np.array_equal(result, truth[a:end+1])

        if (i + 1) % 5 == 0:
            print(f"Performed {i+1}/{num_reads} read queries")

    read_time = time.time() - start_time
    print(f"Completed {num_reads} writes in {read_time:.2f} seconds")

    print(f"Stress test for range completed ({label})\n")


def test_large_both():
    N, Z, B = 1000, 4, 8192
    test_large_dataset(NaiveRangeClient, "Naive Range ORAM", num_writes=100, num_reads=100, N=N, Z=Z, B=B)
    test_large_dataset(RORAMClient, "RORAM", num_writes=100, num_reads=100, N=N, Z=Z, B=B)
    print("All large-data tests passed.")


if __name__ == "__main__":
    test_large_both()
