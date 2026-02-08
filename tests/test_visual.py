import random
import pprint
from client import Client

pp = pprint.PrettyPrinter(indent=4)

def initialize_oram(client, N):
    """
    Initialize all logical blocks so that every read is valid.
    """
    expected = {}
    print("\n--- Initializing ORAM with default values ---")
    for i in range(N):
        val = f"init_{i}"
        print(f"WRITE init: block {i} -> {val}")
        client.access("write", i, val)
        expected[i] = val
    print("--- Initialization complete ---\n")
    return expected


def visualize_access(client, op, block, expected, new_val=None):
    """
    Perform an access and print detailed ORAM state information.
    """
    print("\n==============================")
    print(f"OPERATION: {op.upper()} block {block}")
    if new_val is not None:
        print(f"  New value: {new_val}")
    print("==============================")

    # Before access
    print("Position map BEFORE:")
    pp.pprint(client.position)

    # Perform access
    if op == "write":
        result = client.access("write", block, new_val)
    else:
        result = client.access("read", block)

    # After access
    print("\nPosition map AFTER:")
    pp.pprint(client.position)

    print("\nStash AFTER:")
    pp.pprint(client.S)

    if op == "read":
        print(f"\nREAD RESULT: {result}")
        print(f"EXPECTED:    {expected[block]}")
        assert result == expected[block], f"Mismatch on block {block}"

    print("============================================\n")


def test_visual_basic(client_class):
    print("\n=== VISUAL TEST: Basic Read/Write ===")
    N = 8
    client = client_class(N, Z=2)

    expected = initialize_oram(client, N)

    # Overwrite all blocks with visualization
    for i in range(N):
        new_val = f"new_{i}"
        expected[i] = new_val
        visualize_access(client, "write", i, expected, new_val)

    # Read back with visualization
    for i in range(N):
        visualize_access(client, "read", i, expected)

    print("Basic visual test passed.\n")


def test_visual_random(client_class):
    print("\n=== VISUAL TEST: Random Access ===")
    N = 8
    client = client_class(N, Z=2)

    expected = initialize_oram(client, N)

    for step in range(20):
        block = random.randint(0, N - 1)
        if random.random() < 0.5:
            new_val = f"rand_{step}_{block}"
            expected[block] = new_val
            visualize_access(client, "write", block, expected, new_val)
        else:
            visualize_access(client, "read", block, expected)

    print("Random visual test passed.\n")


def test_all_visual(client_class):
    test_visual_basic(client_class)
    test_visual_random(client_class)
    print("\nAll visual Path ORAM tests passed.\n")


if __name__ == "__main__":
    from client10 import Client10
    test_all_visual(Client10)
