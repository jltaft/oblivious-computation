"""
Throughput comparison: Path ORAM (naive range = r single-block accesses) vs rORAM.

Runs the same random sequence of range read/write operations on both and 
reports total time and throughput (ops/sec and logical blocks/sec).
"""

import random
import time
from basic_path_oram import Client as PathORAMClient
from naive_roram import Client as NaiveRangeClient
from roram import Client as RORAMClient


def generate_operations(N, num_ops, max_range, read_frac=0.5, seed=None):
    """Generate (a, r, op) with op in {'read', 'write'}, a + r <= N, 1 <= r <= max_range."""
    if seed is not None:
        random.seed(seed)
    max_range = min(max_range, N)
    ops = []
    for _ in range(num_ops):
        op = "read" if random.random() < read_frac else "write"
        r = random.randint(1, max_range)
        a = random.randint(0, N - r) if N > r else 0
        ops.append((a, r, op))
    return ops

#Each range of size r is r single-block access 
def run_path_oram(N, ops, truth, B, Z):
    """Run workload on Path ORAM (naive: each range op = r single-block accesses)."""
    client = PathORAMClient(N, B=B, Z=Z)
    # Initialize: write all blocks
    for i in range(N):
        client.access("write", i, truth[i])

    start = time.perf_counter()
    for a, r, op in ops:
        if op == "read":
            for i in range(r):
                client.access("read", a + i)
        else:
            for i in range(r):
                client.access("write", a + i, truth[a + i])
    elapsed = time.perf_counter() - start
    return elapsed

#
def run_naive_roram(N, ops, truth, B, Z, L):
    """Run workload on Naive rORAM (path ORAM under the hood, same r single-block accesses)."""
    client = NaiveRangeClient(N, L=L, B=B, Z=Z)
    client.nice_write(0, N, list(truth))

    start = time.perf_counter()
    for a, r, op in ops:
        if op == "read":
            client.nice_read(a, r)
        else:
            client.nice_write(a, r, truth[a : a + r])
    elapsed = time.perf_counter() - start
    return elapsed


def run_roram(N, ops, truth, B, Z, L):
    """Run workload on rORAM (one range access per op)."""
    client = RORAMClient(N, L=L, B=B, Z=Z)
    truth_list = list(truth)
    client.nice_write(0, N, truth_list)

    start = time.perf_counter()
    for a, r, op in ops:
        if op == "read":
            client.nice_read(a, r)
        else:
            client.nice_write(a, r, truth_list[a : a + r])
    elapsed = time.perf_counter() - start
    return elapsed


def benchmark(N, num_ops, max_range=None, read_frac=0.5, B=8192, Z=4, seed=42):
    """
    Compare throughput of Path ORAM vs Naive rORAM vs rORAM.

    N: number of blocks (use power of 2; rORAM rounds up).
    num_ops: number of range read/write operations.
    max_range: maximum range size per op (default N).
    read_frac: fraction of operations that are reads.
    """
    if max_range is None:
        max_range = N
    max_range = min(max_range, N)

    # Shared initial truth (list of strings)
    random.seed(seed)
    truth = [str(random.randint(0, 9)) for _ in range(N)]

    ops = generate_operations(N, num_ops, max_range, read_frac, seed)

    total_blocks = sum(r for (_, r, _) in ops)

    print("Throughput comparison (same workload)")
    print("=" * 60)
    print(f"N = {N}, num_ops = {num_ops}, max_range = {max_range}, read_frac = {read_frac}")
    print(f"Total logical blocks in workload: {total_blocks}")
    print()

    results = []

    # Path ORAM (naive)
    print("Running Path ORAM (naive range = r single-block accesses)...")
    t_path = run_path_oram(N, ops, truth, B, Z)
    results.append(("Path ORAM (naive)", t_path))

    # Naive rORAM
    print("Running Naive rORAM...")
    t_naive = run_naive_roram(N, ops, truth, B, Z, L=N)
    results.append(("Naive rORAM", t_naive))

    # rORAM
    print("Running rORAM...")
    t_roram = run_roram(N, ops, truth, B, Z, L=N)
    results.append(("rORAM", t_roram))

    # Report
    print()
    print(f"{'Implementation':<28} {'Time (s)':>10} {'Ops/sec':>10} {'Blocks/sec':>12}")
    print("-" * 62)
    for name, t in results:
        ops_sec = num_ops / t if t > 0 else 0
        blocks_sec = total_blocks / t if t > 0 else 0
        print(f"{name:<28} {t:>10.3f} {ops_sec:>10.1f} {blocks_sec:>12.1f}")

    print()
    best_t = min(t for _, t in results)
    print("Relative time (1.0 = fastest):")
    for name, t in results:
        print(f"  {name}: {t / best_t:.2f}x")
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Throughput: Path ORAM vs rORAM")
    parser.add_argument("-N", type=int, default=256, help="Number of blocks (power of 2 for fair comparison)")
    parser.add_argument("--ops", type=int, default=30, help="Number of range read/write operations")
    parser.add_argument("--max-range", type=int, default=None, help="Max range size per op (default N)")
    parser.add_argument("--read-frac", type=float, default=0.5, help="Fraction of operations that are reads")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    benchmark(
        N=args.N,
        num_ops=args.ops,
        max_range=args.max_range,
        read_frac=args.read_frac,
        B=8192,
        Z=4,
        seed=args.seed,
    )

#CLI options: 
# - N: number of blocks (power of 2; rORAM rounds up)
# - ops: number of range read/write operations
# - max-range: max range size per op (default N)
# - read-frac: fraction of operations that are reads
# - seed: random seed   