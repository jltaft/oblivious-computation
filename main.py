from basic_path_oram_client import PathORAMClient as Client

if __name__ == "__main__":
    Client = Client(10)
    print("L= ", Client.L)

    print("\nWrite (0, 'block 0 v1)")
    Client.access("write", 0, "block 0 v1")

    print("\nWrite (8, 'block 8 v1)")
    Client.access("write", 8, "block 8 v1")

    print("\nWrite (0, 'block 0 v2)")
    Client.access("write", 0, "block 0 v2")

    print("\nRead 0")
    print(Client.access("read", 0))

    print("\nRead 8")
    print(Client.access("read", 8))
