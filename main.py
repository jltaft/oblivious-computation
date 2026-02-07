from client import Client

if __name__ == "__main__":
    Client = Client(10)
    Client.access("write", 0, "block 0 v1")
    Client.access("write", 8, "block 8 v1")
    Client.access("write", 0, "block 0 v2")

    print(Client.access("read", 0))
    print(Client.access("read", 8))
