import hashlib
import json

class Block:
    def __init__(self, id, history, parent_id=None, parent_hash=None) :
        self.id = id
        self.history = history
        self.parent_id = parent_id
        self.parent_hash = parent_hash
        self.nonce = None

block_A = Block(id=1, history='Abu suka kucing')
block_B = Block(id=2, history='Angel suka anjung', parent_id=block_A.id)
block_C = Block(id=3, history='Tito benci anjing', parent_id=block_B.id)
chain = [block_A, block_B, block_C]

def compute_hash(block):
    payload = json.dumps(block.__dict__, sort_keys=True).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()

block_B.parent_hash = compute_hash(block_A)
block_C.parent_hash = compute_hash(block_B)

def is_chain_valid(latest_block, chain, difficulty_prefix=''):
    index = {b.id: b for b in chain}
    cur = latest_block
    while cur and cur.parent_id is not None:
        parent = index.get(cur.parent_id)
        if parent is None:
            print (' ! Block induk id=%s tidak ditemukan' % cur.parent_id)
            return False
        if cur.parent_hash != compute_hash(parent):
            print(' ! parent_hash block id=%s tidak cocok' % cur.id)
            return False
        if cur.nonce is not None and not compute_hash(cur).startswith(difficulty_prefix):
            print(' ! proof-of-Work block id=%s tidak sah' % cur.id)
            return False
        cur = parent
    return True

print('== Sebelum manipulasi ==')
print('Block C valid chain? ->' , is_chain_valid(block_C, chain ))

# ... 4) proof of work cari nonce lalu simpan ke dalam block ...
def mine_block(block, difficulty_prefix='0000' , max_try=10-000-000):
    for i in range(max_try):
        block.nonce = i         #nonce ditulis ke dalam block
        h = compute_hash(block) #hash dihitun dari block utuh
        if h.startswith(difficulty_prefix):
            return i, h
    block.nonce = None
    return None, None

# ... 5) menambang block kandidat baru (D) lalu memasukkanya ke chain ...
DIFFICULITY = '0000' # naikkan ke '0000' untuk mersakan efek difficulity
block_D = Block(id=4, history='Sky loves turtle', parent_id=block_C.id)
block_D.parent_hash = compute_hash(block_C)
nonce, h = mine_block(block_D, DIFFICULITY)
chain.append(block_D)
print('== prooof of work (prefix %s) ==' % DIFFICULITY)
print('Nonce:', nonce, '| Hash:',h)
print('Block D valid chain? ->', is_chain_valid(block_D, chain, DIFFICULITY))

# --- 6) uji 1: manipulasi isi block_A ---
block_A.history = 'Abu benci Kucing'
print('== setelah manipulasi data pada Block A ==')
print('Block D valid chain? ->', is_chain_valid(block_D, chain, DIFFICULITY))

# --- 7) Uji pemalsuan nonce pada block yang sudah ditambang ---
block_A.history = 'Abu suka kucing'
block_D.nonce = 999
print('== Setelah nonce block D dipalsukan ==')
print('Block D valid chain? ->', is_chain_valid(block_D, chain, DIFFICULITY))
