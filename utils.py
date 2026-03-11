import random
import json

def uniform_random(n):
    # return a uniform random int from 0 to n inclusive
    return random.randint(0, n)

def pad_block(block, B):
    B_bytes = B // 8
    if len(block) > B_bytes:
        raise ValueError(f"Block size {8 * len(block)} is larger than B={B}")
    if len(block) == B_bytes:
        return block
    return block + b"\x01" + b"\x00" * (B_bytes - len(block) - 1)

def depad_block(block):
    return block.rstrip(b"\x00").removesuffix(b"\x01")

def _encrypt(data, f, identity=True):
    return f.encrypt(data) if not identity else data

def _decrypt(data, f, identity=True):
    return f.decrypt(data) if not identity else data

def encrypt_block(block, B, f):
    byte_block = json.dumps(block).encode("utf-8")
    padded_block = pad_block(byte_block, B)
    encrypted_block = _encrypt(padded_block, f)
    return encrypted_block

def decrypt_block(block, f):
    padded_decrypted_byte_block = _decrypt(block, f)
    decrypted_byte_block = depad_block(padded_decrypted_byte_block)
    decrypted_block = decrypted_byte_block.decode("utf-8")
    return json.loads(decrypted_block)
