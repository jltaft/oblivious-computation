from basic_path_oram_client import PathORAMClient
from recursive_path_oram_client import recursiveClient

# print("\n********Basic Path ORAM******** \n")
# if __name__ == "__main__":
#     Client = PathORAMClient(10)
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

print("\n********Recursive Path ORAM******** \n")
if __name__ == "__main__":
    rClient = recursiveClient(20)
    print("L= ", rClient.L)

    print("\nWrite (0, 'block 0 v1)")
    rClient.access("write", 0, "block 0 v1")

    print("\nWrite (8, 'block 8 v1)")
    rClient.access("write", 8, "block 8 v1")

    print("\nWrite (0, 'block 0 v2)")
    rClient.access("write", 0, "block 0 v2")
    
    print("\nWrite (0, 'block 0 v2)")
    rClient.access("write", 0, "block 0 v2")

    print("\nRead 0")
    print(rClient.access("read", 0))

    print("\nRead 8")
    print(rClient.access("read", 8))


# from roram.roram_client import RORAMClient
# if __name__ == "__main__":
#     for i in range(1000):
#         print(f'test {i}')
#         client = RORAMClient(32)

#         client.access(5, 3, "write", ['a', 'b', 'c'])
#         d = client.access(5, 3, "read")
#         if d[5][0] != 'a' or d[6][0] != 'b' or d[7][0] != 'c':
#             print('failed')
#             break

#         client.access(6, 5, "write", ['e', 'f', 'g', 'h', 'i'])
#         d = client.access(5, 3, "read")
#         if d[6][0] != 'e' or d[7][0] != 'f' or d[8][0] != 'g' or d[9][0] != 'h' or d[10][0] != 'i':
#             print('failed')
#             break
#     else:
#         print('tests passed!')
