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
        induk = induk[:8] + "..." if induk else "None"
        print(f" Block {block['id']} | {block['batch_id']} | {block['status']}"
              f" | Aktor: {block['author']}"
              f" | Hash Induk: {induk}"
              f" | Data: {block['payload']}")

if __name__ == "__main__":
    perintah = sys.argv[1]
    alamat = sys.argv[2]
    if perintah == "mine":
        # Format eksekusi: python client.py mine localhost:5001 "Produsen" "BATCH-001" "MANUFACTURED" '{"suhu":"20C"}'
        author = sys.argv[3] if len(sys.argv) > 3 else "Unknown"
        batch_id = sys.argv[4] if len(sys.argv) > 4 else "Unknown"
        status = sys.argv[5] if len(sys.argv) > 5 else "Unknown"
        payload_str = sys.argv[6] if len(sys.argv) > 6 else "{}"
        data_kirim = {
            "author": author,
            "batch_id": batch_id,
            "status": status,
            "payload": json.loads(payload_str)
        }
        hasil = panggil(f"http://{alamat}/mine", data_kirim)
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
