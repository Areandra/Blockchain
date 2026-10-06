import hashlib
import json

print("=== PENGUJIAN AVALANCHE EFFECT (RANTAI PASOK OBAT) ===\n")

# 1. Data Obat Awal (Suhu 20C)
data_awal = {
    "batch_id": "BATCH-001", 
    "author": "Produsen",
    "status": "MANUFACTURED", 
    "suhu": "20C"
}
# Convert dictionary ke string JSON lalu ke byte
string_awal = json.dumps(data_awal, sort_keys=True).encode('utf-8')
hash_awal = hashlib.sha256(string_awal).hexdigest()

print("Data Awal   :", data_awal)
print("Hash Awal   :", hash_awal, "\n")

# 2. Data Obat Dimanipulasi (Suhu diubah hanya 1 angka menjadi 21C)
data_manipulasi = {
    "batch_id": "BATCH-001", 
    "author": "Produsen",
    "status": "MANUFACTURED", 
    "suhu": "21C"  # <-- Ini yang diubah
}
string_manipulasi = json.dumps(data_manipulasi, sort_keys=True).encode('utf-8')
hash_manipulasi = hashlib.sha256(string_manipulasi).hexdigest()

print("Data Ubah   :", data_manipulasi)
print("Hash Ubah   :", hash_manipulasi, "\n")

# 3. Kesimpulan
if hash_awal != hash_manipulasi:
    print("KESIMPULAN  : Avalanche effect TERBUKTI. Perubahan 1 karakter ('20C' ke '21C') mengubah seluruh struktur hash.")
