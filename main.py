# from recursive_path_oram_client import Client

# if __name__ == "__main__":
#     Client = Client(10)
#     print("L= ", Client.L)

#     print("\nWrite (0, 'block 0 v1)")
#     Client.access("write", 0, "block 0 v1")

#     print("\nWrite (8, 'block 8 v1)")
#     Client.access("write", 8, "block 8 v1")

#     print("\nWrite (0, 'block 0 v2)")
#     Client.access("write", 0, "block 0 v2")

#     print("\nRead 0")
#     print(Client.access("read", 0))

#     print("\nRead 8")
#     print(Client.access("read", 8))


from roram.roram_client import RORAMClient
if __name__ == "__main__":
    client = RORAMClient(32)
    client.access(5, 3, "write", {5: 'a', 6: 'b', 7: 'c'})
