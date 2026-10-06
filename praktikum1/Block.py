class Block:
    id = None
    history = None
    parent_id = None

block_A = Block()
block_A.id = 1
block_A.history = 'Abu Menyukai Kucing'

block_B = Block()
block_B.id = 2
block_B.history = 'Angel Menyukai Anjing'
block_B.parent_id = block_A.id

block_C = Block()
block_C.id = 2
block_C.history = 'Tito Menyukai Anjing'
block_C.parent_id = block_B.id

print("block_A : ",block_A.history)
print("block_B : ",block_A.history)
print("block_C : ",block_A.history)

block_A.history = 'Abu Membenci Kucing'

print("block_A : ",block_A.history)