import random
import time
from client import Client

def test_large_dataset():
    print("\n=== Test: Stress test large dataset ===")
    
    N = 10000      # number of blocks
    Z = 4          # bucket capacity
    B = 8192       # block size in bits (~1 KB)
    client = Client(N, Z=Z, B=B)
    
    print(f"Initialized Path ORAM with N={N}, Z={Z}, B={B} bits")

    max_stash_size = 0

    # Write random data to all blocks
    start_time = time.time()
    for i in range(N):
        data = "X" * (B // 8 - 50)  # large payload string to fit in B bits
        client.access("write", i, data)
        if (i+1) % 1000 == 0:
            print(f"Written {i+1}/{N} blocks")
        max_stash_size = max(max_stash_size, len(client.S))
    
    write_time = time.time() - start_time
    print(f"Completed writing {N} blocks in {write_time:.2f} seconds")
    
    # Randomized read order
    indices = list(range(N))
    random.shuffle(indices)
    start_time = time.time()
    
    for i, idx in enumerate(indices):
        val = client.access("read", idx)
        if (i+1) % 1000 == 0:
            print(f"Read {i+1}/{N} blocks")
        max_stash_size = max(max_stash_size, len(client.S))
    
    read_time = time.time() - start_time
    print(f"Completed reading {N} blocks in {read_time:.2f} seconds")

    print(f"Maximum stash size observed: {max_stash_size}")
    print("Stress test completed successfully\n")

if __name__ == "__main__":
    test_large_dataset()
