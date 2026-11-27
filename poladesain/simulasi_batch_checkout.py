import time
import tracemalloc

from poladesain.minimarket_facade import simulasi_batch_checkout

daftar_order = [
    {
        "nama_pembeli": "Andi",
        "items": [
            {"kode": "Oreo 133g", "qty": 2},
            {"kode": "Aqua Air Mineral", "qty": 3},
        ],
        "voucher": "HEMAT5K",
    },
    {
        "nama_pembeli": "Siti",
        "items": [
            {"kode": "Hot Wheels Reguler", "qty": 1},
            {"kode": "Pocari Sweat", "qty": 2},
        ],
        "voucher": "",
    },
]

tracemalloc.start()
mulai = time.perf_counter()

hasil = simulasi_batch_checkout(daftar_order)

durasi_ms = (time.perf_counter() - mulai) * 1000
mem_sekarang, mem_puncak = tracemalloc.get_traced_memory()
tracemalloc.stop()

print(f"Waktu eksekusi: {durasi_ms:.3f} ms")
print(f"Puncak memori : {mem_puncak / 1024:.2f} KB")
for idx, res in enumerate(hasil, start=1):
    print(f"Order #{idx}: {res['status']} -> {res.get('struk', res.get('pesan'))}")
