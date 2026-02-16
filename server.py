
class Server:
    def __init__(self, data):
        self.data = data
    
    def read_block(self, i):
        return self.data[i]
    
    def write_block(self, i, block):
        self.data[i] = block
