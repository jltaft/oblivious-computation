
class Server:
    def __init__(self, data):
        self.data = data
    
    def read_bucket(self, bucket):
        return self.data[bucket]
    
    def write_bucket(self, bucket, blocks):
        self.data[bucket] = blocks
