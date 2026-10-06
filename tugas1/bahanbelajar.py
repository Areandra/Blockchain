# ==========================================
# 1. IMPORT LIBRARY (MEMUAT MODUL TEKNIS)
# ==========================================
import hashlib  # Modul bawaan Python untuk fungsi hash kriptografik (implementasi fungsi searah/one-way function).
import json     # Modul bawaan untuk serialisasi (mengubah objek Python di memori menjadi teks terstruktur).
# Modul dari pustaka 'cryptography' (Sesuai dengan praktik di file sign-verifyl.py):
from cryptography.hazmat.primitives.asymmetric import rsa, padding  # rsa: pembuat kunci asimetris. padding: teknik pengamanan data sebelum dienkripsi.
from cryptography.hazmat.primitives import hashes  # Menentukan algoritma hash pendukung (SHA256) untuk tanda tangan.
from cryptography.hazmat.backends import default_backend  # Mesin (engine) kriptografi default yang mengeksekusi operasi C di belakang layar.

# ==========================================
# 2. INISIALISASI KUNCI RSA (PUBLIC KEY INFRASTRUCTURE)
# ==========================================
# Membuat objek private_key RSA di memori.
# - public_exponent=65537: Angka prima Fermat keempat (2^16 + 1). Standar industri karena sangat efisien (cepat) untuk komputasi matematis komputer tanpa mengorbankan keamanan.
# - key_size=2048: Panjang kunci dalam bit. Semakin panjang semakin aman, 2048 adalah standar minimal modern yang mustahil dibobol brute-force saat ini.
produsen_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
distributor_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
apotek_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# Mengekstrak Public Key dari Private Key (sifat matematis RSA memungkinkan public key diturunkan dari private key, tapi tidak sebaliknya).
# Disimpan dalam tipe data Dictionary Python sebagai "Whitelist" / Registry identitas.
public_keys = {
    "Produsen": produsen_key.public_key(),
    "Distributor": distributor_key.public_key(),
    "Apotek": apotek_key.public_key()
}

# ==========================================
# 3. KELAS CETAK BIRU (BLUEPRINT) BLOCK
# ==========================================
class Block:
    # Metode __init__ (Constructor) dipanggil secara otomatis saat kita membuat objek block_0, block_1, dst.
    # parent_hash=None: Parameter opsional. Block pertama (Genesis) tidak punya parent, jadi default-nya None (kosong).
    def __init__(self, index, author, batch_id, status, payload, timestamp, parent_hash=None):
        # Variabel instansiasi (self.xxx) menyimpan data spesifik untuk satu block di RAM.
        self.index = index              # (Integer) Index array secara logis.
        self.author = author            # (String) Kunci pencarian untuk mencocokkan di dictionary public_keys.
        self.batch_id = batch_id        # (String) Kunci primer (Primary Key) untuk pelacakan obat.
        self.status = status            # (String) State/kondisi terkini dari state machine logistik.
        self.payload = payload          # (Dictionary) Data bebas tambahan (sensor suhu, dll).
        self.timestamp = timestamp      # (Float) Epoch time (detik sejak 1 Jan 1970).
        
        self.parent_hash = parent_hash  # (String/None) Kunci asing (Foreign Key) yang menunjuk ke block.hash sebelumnya.
        self.nonce = None               # (Integer) Counter iterasi dari algoritma penambangan.
        self.hash = None                # (String) String Hexadesimal 64-karakter (Output dari SHA-256).
        self.signature = None           # (String) Tanda tangan terenkripsi yang di-encode ke bentuk Hexadesimal.

# ==========================================
# 4. FUNGSI HASH (DETERMINISTIK & COLLISION RESISTANCE)
# ==========================================
def compute_hash(block):
    # Membungkus variabel-variabel instansiasi ke dalam satu struktur Dictionary Python.
    # Ingat: Kita TIDAK memasukkan 'hash' dan 'signature' karena keduanya bergantung pada komputasi hash itu sendiri (menghindari rekursi).
    data = {
        "index": block.index, "author": block.author, "batch_id": block.batch_id,
        "status": block.status, "payload": block.payload, "timestamp": block.timestamp,
        "parent_hash": block.parent_hash, "nonce": block.nonce
    }
    
    # TEKNIS SERIALISASI:
    # 1. json.dumps(data, sort_keys=True): Mengubah Dictionary Python acak menjadi String panjang yang terurut secara alfabet (A-Z) berdasarkan key.
    #    Ini SANGAT KRUSIAL. Fungsi hash harus deterministik. Jika urutan key JSON berubah-ubah (misal kadang 'index' di depan, kadang 'author'), nilai hash akan totally berbeda!
    # 2. .encode('utf-8'): Algoritma hashlib.sha256() HANYA menerima format biner (Bytes), BUKAN String. utf-8 mengubah teks ke bentuk Bytes (0101010).
    payload = json.dumps(data, sort_keys=True).encode('utf-8')
    
    # hashlib.sha256(payload): Melakukan komputasi searah matematika kriptografi pada data biner.
    # .hexdigest(): Menerjemahkan output biner biner/byte mentah menjadi teks string berformat Hexadesimal (angka 0-9 dan huruf a-f).
    return hashlib.sha256(payload).hexdigest()

# ==========================================
# 5. ALGORITMA KONSENSUS (PROOF OF WORK)
# ==========================================
def mine_block(block, difficulty_prefix='000', max_try=1000000):
    # Loop iterasi dari 0 hingga 999.999 (Brute-force attack terkontrol)
    for i in range(max_try):
        block.nonce = i               # Mutasi/Ubah data di dalam block.
        h = compute_hash(block)       # Karena nonce berubah (walau cuma 1 angka), efek avalanche SHA-256 akan menghasilkan hash yang berubah total.
        
        # Evaluasi teknis: h adalah string hex (misal "000a1b2..."). startswith membandingkan karakter awal string tersebut.
        if h.startswith(difficulty_prefix): 
            block.hash = h            # Jika memenuhi syarat (awalan "000"), simpan permanen hash tersebut ke memori objek block.
            return i, h               # Hentikan fungsi (Break), kembalikan tuple (nonce, hash).
    
    block.nonce = None # Kembalikan ke asal (None) jika gagal menambang, mencegah terjadinya invalid state.
    return None, None

# ==========================================
# 6. DIGITAL SIGNATURE (PEMBUKTIAN OTENTIKASI & INTEGRITAS)
# ==========================================
def sign_block(block, private_key):
    # Hash SHA-256 yang sudah di-generate sebelumnya bertipe String. Diubah ke Bytes menggunakan encode() untuk diproses oleh RSA.
    message = block.hash.encode('utf-8')
    
    # Proses matematis penandatanganan:
    signature = private_key.sign(
        message, # Data biner yang akan ditandatangani.
        # TEKNIS PADDING (RSASSA-PSS): Probabilistic Signature Scheme.
        # Jika kita mengenkripsi data yang persis sama dua kali, PSS menyuntikkan 'salt' (acak) sehingga hasil signature akan BERBEDA setiap kali dipanggil, 
        # namun Public Key TETAP BISA memvalidasinya. Ini mencegah serangan analisis pola (Chosen Ciphertext Attack).
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), # Mask Generation Function menggunakan SHA-256 untuk memoles struktur padding.
            salt_length=padding.PSS.MAX_LENGTH # Menggunakan maksimal memori yang tersisa di blok data untuk menambah pengacakan.
        ),
        hashes.SHA256() # Proses hash di internal fungsi signing.
    )
    # Variabel signature berupa Bytes mentah yang sulit dibaca/dikirim via JSON. 
    # .hex() mengubah byte mentah (misal: \x1b\x02) menjadi string hex (misal: "1b02") agar mudah disimpan.
    block.signature = signature.hex()

# ==========================================
# 7. LOGIKA BISNIS DAN VALIDASI INTEGRITAS RANTAI
# ==========================================
def is_chain_valid(latest_block, chain, difficulty_prefix='000'):
    # Dictionary Comprehension Python. Mengubah struktur List/Array linear menjadi Hash Map (Dictionary).
    # Bertujuan agar pencarian parent block via index bersifat O(1) (instant), dibanding loop array biasa yang O(n) (lambat jika rantainya jutaan).
    index_map = {b.index: b for b in chain}
    
    # Kita melakukan verifikasi mundur (Reverse traversal) dari blok terbaru. 
    cur = latest_block 
    
    # Selama cur tidak None (belum lewat Genesis) dan index > 0.
    while cur and cur.index > 0:
        # Mengambil objek parent block dari Hash Map berdasarkan (index saat ini - 1)
        parent = index_map.get(cur.index - 1)
        
        # RULE 1: Keterhubungan Struktural. Parent harus ada di dalam memori/struktur data.
        if parent is None:
            print('! Block induk index=%s tidak ditemukan' % (cur.index - 1))
            return False
            
        # RULE 2: Validasi Linked List (Pointer Hash). Kunci penghubung (parent_hash block sekarang == hash parent).
        if cur.parent_hash != parent.hash:
            print('! parent_hash block index=%s tidak cocok' % cur.index)
            return False
            
        # RULE 3: Deteksi Mutasi Data. Jika ada hacker yang mengubah variabel payload atau status (secara langsung di RAM), 
        # maka compute_hash(cur) (hash real-time) akan berbeda dengan cur.hash (hash historis yang disimpan).
        if cur.hash != compute_hash(cur):
            print('! Hash block index=%s telah berubah/tidak sesuai isi' % cur.index)
            return False
            
        # RULE 4: Validasi PoW. Mencegah hacker membuat block instan. Mereka wajib membuktikan telah melakukan komputasi berat.
        if cur.nonce is not None and not cur.hash.startswith(difficulty_prefix):
            print('! proof-of-Work block index=%s tidak sah' % cur.index)
            return False
            
        # RULE 5: Permissioned Blockchain. Otorisasi penulis.
        if cur.author not in public_keys:
            print('! Aktor "%s" tidak terdaftar di whitelist' % cur.author)
            return False
            
        # RULE 6: Validasi Asimetris (Public Key Verifier).
        try:
            # Ambil public_key asli dari Whitelist berdasarkan author.
            public_key = public_keys.get(cur.author) 
            
            public_key.verify(
                bytes.fromhex(cur.signature), # Dekonversi dari string hex kembali menjadi format biner (Bytes).
                cur.hash.encode('utf-8'),     # Konversi hash ke biner (Bytes).
                # Parameter padding harus identik 100% dengan pengaturan pada fungsi sign_block() agar algoritma cocok.
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            # Jika verify sukses, ia tidak mereturn apapun (jalan terus). Jika gagal, akan men-trigger (raise) Exception!
        except Exception:
            # Masuk ke blok Exception jika hacker membajak transaksi atau mengubah data sehingga signature menjadi kadaluarsa.
            print('! Signature block index=%s tidak valid atau dipalsukan' % cur.index)
            return False
            
        # RULE 7: Integritas State Machine Bisnis (Primary Key tidak boleh diubah antar block).
        if cur.batch_id != parent.batch_id:
             print('! Batch ID berubah secara ilegal dari %s ke %s pada index %s' % (parent.batch_id, cur.batch_id, cur.index))
             return False
             
        # RULE 8: State Machine Logistik (Directed Acyclic Graph Logic).
        valid_transitions = {
            "MANUFACTURED": ["IN TRANSIT"],
            "IN TRANSIT": ["RECEIVED", "IN TRANSIT"], 
            "RECEIVED": [] 
        }
        # .get(parent.status, []) -> Jika status parent di luar nalar, return Array Kosong.
        # "not in" -> Jika status current (cur) tidak ada di dalam Array aturan yang berlaku, maka ia ditolak.
        if cur.status not in valid_transitions.get(parent.status, []):
            print('! Transisi status ilegal dari %s ke %s pada index %s' % (parent.status, cur.status, cur.index))
            return False

        # Geser pointer memori mundur satu langkah untuk iterasi Loop berikutnya.
        cur = parent
        
    # --- Validasi Khusus untuk Ujung Rantai (Genesis Block, index 0) ---
    if cur and cur.index == 0:
        if cur.hash != compute_hash(cur):
            print('! Isi Genesis block telah dimanipulasi')
            return False
        if cur.status != "MANUFACTURED": # Kondisi mutlak genesis. Obat tidak bisa tiba-tiba "RECEIVED" jika belum diproduksi.
            print('! Status Genesis block harus MANUFACTURED')
            return False
            
    return True # Seluruh stack validasi dilewati. Rantai 100% aman (Secure).

# ==========================================
# 8. EKSEKUSI PROGRAM & PEMBUATAN OBJEK (INSTANTIATION)
# ==========================================
chain = [] # Array List bertindak sebagai Ledger (Buku Besar) terdistribusi lokal.
DIFFICULTY = '000'

# A. Pembuatan Block-0 (Diinisiasi oleh memori komputer)
block_0 = Block(0, "Produsen", "BATCH-001", "MANUFACTURED", {"suhu": "20C"}, 1696000000.0)
mine_block(block_0, DIFFICULTY)      
sign_block(block_0, produsen_key)    
chain.append(block_0)

# B. Pembuatan Block-1 (Pointer parent_hash mengarah ke hash block-0 secara presisi di memori)
block_1 = Block(1, "Distributor", "BATCH-001", "IN TRANSIT", {"suhu": "22C", "lokasi": "Gudang A"}, 1696005000.0, block_0.hash)
mine_block(block_1, DIFFICULTY)
sign_block(block_1, distributor_key) 
chain.append(block_1)

# C. Pembuatan Block-2 (Ujung akhir/Tip dari chain)
block_2 = Block(2, "Apotek", "BATCH-001", "RECEIVED", {"kondisi": "Baik"}, 1696010000.0, block_1.hash)
mine_block(block_2, DIFFICULTY)
sign_block(block_2, apotek_key)      
chain.append(block_2)

print('== Sebelum manipulasi ==')
print('Block 2 valid chain? ->', is_chain_valid(block_2, chain, DIFFICULTY))

# ==========================================
# 9. UJI PENETRASI SISTEM (PENETRATION TESTING)
# ==========================================

# Skenario 1: Serangan Alterasi State (Mengganti Variabel Memori)
block_0.status = "EXPIRED" # Data diubah secara kasar dari sisi memori (RAM).
block_0.hash = compute_hash(block_0) # Hacker mencoba menghitung ulang hash baru agar lolos Validasi 3.
print('\n== Setelah manipulasi data pada Block 0 ==')
# GAGAL! Kenapa? 
# 1. Block-1 di memori sudah merekam hash block-0 yang ASLI ke dalam variabel block_1.parent_hash. Validasi 2 (Pointer) akan putus karena hash baru tidak cocok.
# 2. Meskipun hash baru dihitung, hacker TIDAK MEMILIKI produsen_key. Tanda tangan lama di memori sudah tidak relevan dengan string data (status) yang baru. Validasi 6 meledak (Exception).
print('Block 2 valid chain? ->', is_chain_valid(block_2, chain, DIFFICULTY))

# (Rollback / Pemulihan state sistem untuk uji coba selanjutnya)
block_0.status = "MANUFACTURED"
mine_block(block_0, DIFFICULTY)
sign_block(block_0, produsen_key)

# Skenario 2: Serangan Injeksi Nonce Tanpa Komputasi (Bypass PoW)
block_2.nonce = 999999
print('\n== Setelah nonce block 2 dipalsukan ==')
# GAGAL! Kenapa?
# Nonce diubah, artinya seluruh integritas isi JSON block-2 berubah (Avalanche effect hash SHA-256 terjadi). 
# Saat program memanggil compute_hash() untuk verifikasi Validasi 3, string hash-nya akan berubah drastis menjadi kombinasi huruf/angka acak. 
# Peluang hash acak tersebut diawali angka "000" (Validasi 4) secara tidak sengaja adalah 1 berbanding 4096. Serangan gagal terdeteksi!
print('Block 2 valid chain? ->', is_chain_valid(block_2, chain, DIFFICULTY))