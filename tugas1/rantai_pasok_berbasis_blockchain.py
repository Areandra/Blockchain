import hashlib
import json
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

produsen_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
distributor_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
apotek_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

public_keys = {
    "Produsen": produsen_key.public_key(),
    "Distributor": distributor_key.public_key(),
    "Apotek": apotek_key.public_key()
}

class Block:
    def __init__(self, index, author, batch_id, status, payload, timestamp, parent_hash=None):
        self.index = index
        self.author = author
        self.batch_id = batch_id
        self.status = status
        self.payload = payload
        self.timestamp = timestamp
        self.parent_hash = parent_hash
        self.nonce = None
        self.hash = None
        self.signature = None

def compute_hash(block):
    data = {
        "index": block.index,
        "author": block.author,
        "batch_id": block.batch_id,
        "status": block.status,
        "payload": block.payload,
        "timestamp": block.timestamp,
        "parent_hash": block.parent_hash,
        "nonce": block.nonce
    }
    payload = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()

def mine_block(block, difficulty_prefix='000', max_try=1000000):
    for i in range(max_try):
        block.nonce = i
        h = compute_hash(block)
        if h.startswith(difficulty_prefix):
            block.hash = h
            return i, h
    block.nonce = None
    return None, None

def sign_block(block, private_key):
    message = block.hash.encode('utf-8')
    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    block.signature = signature.hex()

def is_chain_valid(latest_block, chain, difficulty_prefix='000'):
    index_map = {b.index: b for b in chain}
    cur = latest_block
    
    while cur and cur.index > 0:
        parent = index_map.get(cur.index - 1)
        
        if parent is None:
            print('! Block induk index=%s tidak ditemukan' % (cur.index - 1))
            return False
            
        if cur.parent_hash != parent.hash:
            print('! parent_hash block index=%s tidak cocok' % cur.index)
            return False
            
        if cur.hash != compute_hash(cur):
            print('! Hash block index=%s telah berubah/tidak sesuai isi' % cur.index)
            return False
            
        if cur.nonce is not None and not cur.hash.startswith(difficulty_prefix):
            print('! proof-of-Work block index=%s tidak sah' % cur.index)
            return False
            
        if cur.author not in public_keys:
            print('! Aktor "%s" tidak terdaftar di whitelist' % cur.author)
            return False
            
        try:
            public_key = public_keys.get(cur.author)
            public_key.verify(
                bytes.fromhex(cur.signature),
                cur.hash.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        except Exception:
            print('! Signature block index=%s tidak valid atau dipalsukan' % cur.index)
            return False
            
        if cur.batch_id != parent.batch_id:
             print('! Batch ID berubah secara ilegal dari %s ke %s pada index %s' % (parent.batch_id, cur.batch_id, cur.index))
             return False
             
        valid_transitions = {
            "MANUFACTURED": ["IN TRANSIT"],
            "IN TRANSIT": ["RECEIVED", "IN TRANSIT"], # Bisa transit antar gudang
            "RECEIVED": [] # Tidak bisa diubah lagi setelah diterima
        }
        if cur.status not in valid_transitions.get(parent.status, []):
            print('! Transisi status ilegal dari %s ke %s pada index %s' % (parent.status, cur.status, cur.index))
            return False

        cur = parent
        
    if cur and cur.index == 0:
        if cur.hash != compute_hash(cur):
            print('! Isi Genesis block telah dimanipulasi')
            return False
        if cur.status != "MANUFACTURED":
            print('! Status Genesis block harus MANUFACTURED')
            return False
            
    return True

chain = []
DIFFICULTY = '000'

block_0 = Block(0, "Produsen", "BATCH-001", "MANUFACTURED", {"suhu": "20C"}, 1696000000.0)
mine_block(block_0, DIFFICULTY)
sign_block(block_0, produsen_key)
chain.append(block_0)

block_1 = Block(1, "Distributor", "BATCH-001", "IN TRANSIT", {"suhu": "22C", "lokasi": "Gudang A"}, 1696005000.0, block_0.hash)
mine_block(block_1, DIFFICULTY)
sign_block(block_1, distributor_key)
chain.append(block_1)

block_2 = Block(2, "Apotek", "BATCH-001", "RECEIVED", {"kondisi": "Baik"}, 1696010000.0, block_1.hash)
mine_block(block_2, DIFFICULTY)
sign_block(block_2, apotek_key)
chain.append(block_2)

print('== Sebelum manipulasi ==')
print('Block 2 valid chain? ->', is_chain_valid(block_2, chain, DIFFICULTY))

block_0.status = "EXPIRED"
block_0.hash = compute_hash(block_0)
print('\n== Setelah manipulasi data pada Block 0 ==')
print('Block 2 valid chain? ->', is_chain_valid(block_2, chain, DIFFICULTY))

block_0.status = "MANUFACTURED"
mine_block(block_0, DIFFICULTY)
sign_block(block_0, produsen_key)
block_2.nonce = 999999
print('\n== Setelah nonce block 2 dipalsukan ==')
print('Block 2 valid chain? ->', is_chain_valid(block_2, chain, DIFFICULTY))
