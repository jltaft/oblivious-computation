from client import Client, recursiveClient

def test_basic_write_read(client_class, label="Path ORAM"):
    print(f"\n=== Overwriting blocks with trace ({label}) ===")
    N = 3
    client = client_class(N)

    # writes
    for i in range(N):
        print(f"Initial write block {i}: first_{i}")
        client.access("write", i, f"first_{i}")

    # overwrites
    for i in range(N):
        print(f"Overwrite block {i}: second_{i}")
        client.access("write", i, f"second_{i}")

    # reads
    for i in range(N):
        val = client.access("read", i)
        print(f"Read block {i}: {val}")
        assert val == f"second_{i}", f"Expected second_{i}, got {val}"

    print(f"Passed overwrite test ({label})\n")


def test_basic_both():
    test_basic_write_read(Client, "single-level Path ORAM")
    test_basic_write_read(recursiveClient, "recursive Path ORAM")
    print("All basic tests passed (single-level + recursive).\n")


if __name__ == "__main__":
    test_basic_both()
