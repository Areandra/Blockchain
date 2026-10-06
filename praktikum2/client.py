import json 
import sys
import urllib.error
import urllib.request

def panggil(url, data = None):
    if data is None:
        permintaan = urllib.request.Request(url)
    else: 
        permintaan = urllib.request.Request(
            url, data = json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(permintaan, timeout=30) as balasan:
        return json.loads(balasan.read().decode("utf-8"))
def ringkas(chain):
    for block in chain:
        induk = block["parent_hash"]
        induk = induk[:12] + "..." if induk else "None"
        print(f" Block {block['id']}"
              f" | nonce: {str(block['nonce']).ljust(8)}"
              f" | parent_hash: {induk}"
              f" | history: {block['history']}")

if __name__ == "__main__":
    perintah = sys.argv[1]
    alamat = sys.argv[2]
    if perintah == "mine":
        pesan = sys.argv[3] if len(sys.argv) > 3 else "(tanpa data)"
        hasil = panggil(f"http://{alamat}/mine", {"history": pesan})
        print(f"{hasil['pesan']}: block {hasil['block']['id']}")
    elif perintah == "chain":
        hasil = panggil(f"http://{alamat}/chain")
        print(f"Panjang rantai di {alamat} : {hasil['panjang']} block")
        ringkas(hasil["chain"])
    elif perintah == "resolve":
        hasil = panggil(f"http://{alamat}/resolve")
        if hasil["rantai_diganti"]:
            print(f"Rantai diganti. Panjang sekarang: {hasil['panjang']} block")
        else:
            print(f"Rantai tidak berubah. Panjang: {hasil['panjang']} block")
    elif perintah == "palsu":
        terakhir = panggil(f"http://{alamat}/chain")["chain"][-1]
        block_palsu = {
            "id": terakhir["id"] + 1,
            "history": "Block palsu tanpa proof of work",
            "parent_id": terakhir["id"],
            "parent_hash": "0" * 64,
            "nonce": 1,
        }
        try:
            panggil(f"http://{alamat}/block", block_palsu)
            print("Block palsu DITERIMA -- validasi node bermasalah.")
        except urllib.error.HTTPError as e:
            print(f"Block palsu DITOLAK oleh node. Status HTTP: {e.code}")
    else:
        print("Perintah: mine | chain | resolve | palsu")
