# nodde.py- Node blockchain yang dapat berkomunikasi lewat jaringan
import hashlib
import json
import sys
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DIFFICULTY = "0000" #tingkat kesuliatan proof of work
PORT = 0 #diisi saat program dijalankan
PEERS = [] #daftar alamat node tetangga
CHAIN = [] #daftar block milik node ini

#--- Logika blockchain (lanjutan dari pratikum 1) ---
def new_block(id, history, parent_id=None, parent_hash=None):
    return {
        "id": id,
        "history": history,
        "parent_id": parent_id,
        "parent_hash": parent_hash,
        "nonce": None,
    }

def compute_hash(block):
    payload = json.dumps(block, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def mine_block(block, difficulty=DIFFICULTY, max_try=500000):
    for i in range(max_try):
        block["nonce"] = i
        hasil = compute_hash(block)
        if hasil.startswith(difficulty):
            return i, hasil
    block["nonce"] = None
    return None, None

def genesis_block():
    block = new_block(1, "Genesis Block")
    block["nonce"] = 0  #genesis disamakan di semua node
    return block

def is_chain_valid(chain, difficulty=DIFFICULTY):
    if not chain or chain[0]["parent_hash"] is not None:
        return False
    for i in range(1, len(chain)):
        induk = chain[i - 1]
        block = chain[i]
        if block["parent_id"] != induk["id"]:
            return False
        if block["parent_hash"] != compute_hash(induk):
            return False
        if block["nonce"] is None:
            return False
        if not compute_hash(block).startswith(difficulty):
            return False
    return True

#--- Komunikasi antar node ---
def kirim_json(url, isi):
    data = json.dumps(isi).encode("utf-8")
    permintaan = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(permintaan, timeout=5) as balasan:
        return json.loads(balasan.read().decode("utf-8"))

def ambil_json(url):
    with urllib.request.urlopen(url, timeout=5) as balasan:
        return json.loads(balasan.read().decode("utf-8"))

def broadcast_block(block):
    for peer in PEERS:
        try:
            kirim_json(f"http://{peer}/block", block)
            print(f"  -> block {block['id']} dikirim ke {peer}")
        except Exception as e:
            print(f"  !! gagal menririm ke {peer} ({e})")

def resolve_conflicts():
    terpanjang = CHAIN
    for peer in PEERS:
        try:
            kandidat = ambil_json(f"http://{peer}/chain")["chain"]
            if len(kandidat) > len(terpanjang) and is_chain_valid(kandidat):
                terpanjang = kandidat
                print(f"  -> rantai lebih panjang di {peer}"
                      f" ({len(kandidat)} block)")
        except Exception as e:
            print(f"  !! gagal menghubungi {peer} ({e})")
    if terpanjang is not CHAIN:
        CHAIN[:] = terpanjang
        return True
    return False


#--- Antarmuka HTTP node---
class NodeHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass     # mematikan log bawaan agar keluaran mudah dibaca

    def _balas(self, kode, isi):
        badan = json.dumps(isi, indent=2).encode("utf-8")
        self.send_response(kode)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(badan)))
        self.end_headers()
        self.wfile.write(badan)

    def do_GET(self):
        if self.path == "/chain":
            self._balas(200, {"panjang": len(CHAIN), "chain": CHAIN})
        elif self.path == "/resolve":
            print(f"[{PORT}] menjalankan longest-chain rule")
            berubah = resolve_conflicts()
            self._balas(200, {"rantai_diganti": berubah,
                              "panjang": len(CHAIN)})
        else:
            self._balas(404, {"error": "endpoint tidak dikenal"})

    def do_POST(self):
        panjang = int(self.headers.get("Content-Length", 0))
        isi = json.loads(self.rfile.read(panjang) or b"{}")
        if self.path == "/mine":
            induk = CHAIN[-1]
            block = new_block(induk["id"] + 1,
                    isi.get("history", "(tanpa data)"),
                    parent_id=induk["id"],
                    parent_hash=compute_hash(induk))
            nonce, hasil = mine_block(block)
            if nonce is None:
                self._balas(500, {"error": "gagal menambang block"})
                return
            CHAIN.append(block)
            print(f"[{PORT}] block {block['id']} ditambang,"
                f" nonce={nonce}, hash={hasil[:20]}...")
            broadcast_block(block)
            self._balas(201, {"pesan": "block ditambang", "block": block})
        elif self.path == "/block":
            block = isi
            induk = CHAIN[-1]
            sah = (block.get("parent_id") == induk["id"]
                and block.get("parent_hash") == compute_hash(induk)
                and block.get("nonce") is not None
                and compute_hash(block).startswith(DIFFICULTY))
            if sah:
                CHAIN.append(block)
                print(f"[{PORT}] block {block['id']} diterima dari peer")
                self._balas(200, {"pesan": "block diterima"})
            else:
                print(f"[{PORT}] block {block.get('id')} DITOLAK")
                self._balas(409, {"pesan": "block ditolak"})
        else:
            self._balas(404, {"error": "endpoint tidak dikenal"})


#--- Menjalankan node---
if __name__=="__main__":
    PORT = int(sys.argv[1])
    if len(sys.argv) > 2 and sys.argv[2]:
        PEERS = sys.argv[2].split(",")
    CHAIN.append(genesis_block())

    print(f"Node aktif di port {PORT}")
    print("peers  : " + (",".join(PEERS) if PEERS else "(belum ada)"))
    print(f"Genesis : {compute_hash(CHAIN[0])[:20]}...")
    ThreadingHTTPServer(("0.0.0.0", PORT), NodeHandler).serve_forever()