
class Server:
    def __init__(self, data):
        self.data = data
    
    def read_bucket(self, i):
        return self.data[i]
    
    def write_bucket(self, i, block):
        self.data[i] = block
