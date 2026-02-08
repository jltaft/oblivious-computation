from client import Client

def test_basic_write_read():
    print("\n=== Test: Overwriting blocks with trace ===")
    N = 3
    client = Client(N)

    # Initial writes
    for i in range(N):
        print(f"Initial write block {i}: first_{i}")
        client.access("write", i, f"first_{i}")

    # Overwrites
    for i in range(N):
        print(f"Overwrite block {i}: second_{i}")
        client.access("write", i, f"second_{i}")

    # Read back
    for i in range(N):
        val = client.access("read", i)
        print(f"Read block {i}: {val}")
        assert val == f"second_{i}", f"Expected second_{i}, got {val}"

    print("Passed overwrite test with trace\n")

if __name__ == "__main__":
    test_basic_write_read()
