"""Sistem Informasi Minimarket - versi PROSEDURAL MURNI.

Tanpa class, tanpa inheritance, tanpa design pattern.
Hanya fungsi, dictionary, list, if-elif, dan looping.

Struktur data:
  produk  = {"kategori": "Makanan", "nama": str, "harga": int, "stok": int,
             "kadaluarsa" | "rekomendasi_umur" | "ukuran_ml": ...}
  struk   = {"waktu", "pembeli", "items", "subtotal", "potongan", "total_bayar"}
"""

import json
import os
import sys
from datetime import datetime

FOLDER = os.path.dirname(os.path.abspath(__file__))
FILE_PRODUK = os.path.join(FOLDER, "database_toko.json")
FILE_RIWAYAT = os.path.join(FOLDER, "riwayat.json")

# Voucher yang tersedia: kode -> potongan nominal (Rp)
DAFTAR_VOUCHER = {"HEMAT5K": 5000}


# ----------------------------------------------------------------------
# Baca / tulis JSON
# ----------------------------------------------------------------------
def baca_json(path):
    """Baca file JSON berisi list. File belum ada/kosong -> list kosong."""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        isi = f.read().strip()
    if isi == "":
        return []
    data = json.loads(isi)
    if isinstance(data, list):
        return data
    return []


def tulis_json(path, data):
    """Tulis list ke file JSON (indent 4, sama dengan versi lain)."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ----------------------------------------------------------------------
# Produk
# ----------------------------------------------------------------------
def hitung_harga_akhir(produk):
    """Harga satuan setelah diskon kategori (Makanan 10%, Mainan 5%, Minuman 20%)."""
    kategori = produk["kategori"]
    if kategori == "Makanan":
        persen = 10
    elif kategori == "Mainan":
        persen = 5
    elif kategori == "Minuman":
        persen = 20
    else:
        persen = 0
    return produk["harga"] - int((produk["harga"] * persen) / 100)


def cari_produk(daftar_produk, kode_atau_nama):
    """Cari berdasarkan nama (tidak peka huruf besar/kecil), fallback 'PRD-001' / '1'."""
    if not kode_atau_nama:
        return None
    target = kode_atau_nama.strip().lower()
    for p in daftar_produk:
        if p["nama"].lower() == target:
            return p
    bersih = kode_atau_nama.strip().upper()
    if bersih.startswith("PRD-"):
        bersih = bersih[4:]
    if bersih.isdigit():
        indeks = int(bersih) - 1
        if 0 <= indeks < len(daftar_produk):
            return daftar_produk[indeks]
    return None


def ambil_semua_produk():
    """Daftar produk untuk frontend (+ id_produk dan harga_akhir)."""
    hasil = []
    for p in baca_json(FILE_PRODUK):
        item = dict(p)
        item["id_produk"] = p["nama"]
        item["harga_akhir"] = hitung_harga_akhir(p)
        hasil.append(item)
    return hasil


def tambah_produk(kategori, nama, harga, stok, extra):
    """Tambah produk baru ke database_toko.json."""
    nama_bersih = str(nama).strip()
    try:
        harga_int = int(harga)
        stok_int = int(stok)
    except (TypeError, ValueError):
        return {"status": "gagal", "pesan": "Harga dan Stok harus angka."}

    if not nama_bersih or harga_int <= 0 or stok_int < 0:
        return {"status": "gagal", "pesan": "Data tidak lengkap/valid."}

    daftar = baca_json(FILE_PRODUK)
    if cari_produk_nama(daftar, nama_bersih) is not None:
        return {"status": "gagal", "pesan": "Produk dengan nama tersebut sudah ada."}

    kat = str(kategori).strip().lower()
    produk = {"nama": nama_bersih, "harga": harga_int, "stok": stok_int}
    try:
        if kat == "makanan":
            produk = {"kategori": "Makanan", "nama": nama_bersih, "harga": harga_int,
                      "stok": stok_int, "kadaluarsa": str(extra)}
        elif kat == "mainan":
            produk = {"kategori": "Mainan", "nama": nama_bersih, "harga": harga_int,
                      "stok": stok_int, "rekomendasi_umur": int(extra)}
        elif kat == "minuman":
            produk = {"kategori": "Minuman", "nama": nama_bersih, "harga": harga_int,
                      "stok": stok_int, "ukuran_ml": int(extra)}
        else:
            return {"status": "gagal", "pesan": "Kategori tidak dikenal."}
    except (TypeError, ValueError):
        return {"status": "gagal", "pesan": "Data tambahan produk tidak valid."}

    daftar.append(produk)
    tulis_json(FILE_PRODUK, daftar)
    return {"status": "sukses",
            "pesan": f"Produk {nama_bersih} berhasil ditambahkan!",
            "produk": produk}


def cari_produk_nama(daftar_produk, nama):
    """Cari persis berdasarkan nama (tanpa fallback indeks)."""
    target = nama.strip().lower()
    for p in daftar_produk:
        if p["nama"].lower() == target:
            return p
    return None


# ----------------------------------------------------------------------
# Transaksi (semua logika ada DI DALAM satu fungsi, tanpa objek)
# ----------------------------------------------------------------------
def proses_transaksi(nama_pembeli, items, kode_voucher=None, saldo_awal=None):
    """Proses SATU transaksi.

    Setiap pemanggilan: baca database_toko.json -> validasi -> hitung diskon
    -> kurangi stok -> tulis ulang database_toko.json -> baca & tulis ulang
    riwayat.json.
    """
    if not items:
        return {"status": "gagal", "pesan": "Keranjang belanja tidak boleh kosong."}

    # 1) BACA ulang database dari disk
    daftar_produk = baca_json(FILE_PRODUK)

    # 2) Validasi tiap item + agregasi qty per produk
    keranjang = []          # list of {"produk": dict, "jumlah": int}
    total_diminta = {}      # nama produk -> total qty diminta
    for entry in items:
        kode_item = str(entry.get("kode") or entry.get("id_produk") or "").strip()
        try:
            qty = int(entry.get("qty", entry.get("jumlah", 0)))
        except (TypeError, ValueError):
            return {"status": "gagal",
                    "pesan": f"Kuantitas item '{kode_item}' tidak valid."}

        if qty <= 0:
            return {"status": "gagal",
                    "pesan": f"Kuantitas '{kode_item}' harus lebih dari 0."}

        produk = cari_produk(daftar_produk, kode_item)
        if produk is None:
            return {"status": "gagal",
                    "pesan": f"Produk '{kode_item}' tidak ditemukan."}

        akumulasi = total_diminta.get(produk["nama"], 0) + qty
        if produk["stok"] < akumulasi:
            return {"status": "gagal",
                    "pesan": (f"Stok {produk['nama']} tidak mencukupi "
                              f"(diminta: {akumulasi}, tersedia: {produk['stok']}).")}
        total_diminta[produk["nama"]] = akumulasi

        sudah_ada = False
        for barang in keranjang:
            if barang["produk"]["nama"] == produk["nama"]:
                barang["jumlah"] += qty
                sudah_ada = True
                break
        if not sudah_ada:
            keranjang.append({"produk": produk, "jumlah": qty})

    # 3) Hitung harga per item (diskon kategori) dan subtotal
    daftar_item = []
    subtotal = 0
    for barang in keranjang:
        produk = barang["produk"]
        kategori = produk["kategori"]
        if kategori == "Makanan":
            persen = 10
        elif kategori == "Mainan":
            persen = 5
        elif kategori == "Minuman":
            persen = 20
        else:
            persen = 0
        harga_satuan = produk["harga"] - int((produk["harga"] * persen) / 100)
        sub = harga_satuan * barang["jumlah"]
        subtotal += sub
        daftar_item.append({
            "nama": produk["nama"],
            "qty": barang["jumlah"],
            "harga_satuan": harga_satuan,
            "subtotal": sub,
        })

    # 4) Voucher (berlaku hanya jika subtotal >= nominal potongan)
    kode = (kode_voucher or "").strip().upper()
    potongan = 0
    if kode in DAFTAR_VOUCHER:
        nominal = DAFTAR_VOUCHER[kode]
        if subtotal >= nominal:
            potongan = nominal
    total_bayar = subtotal - potongan

    # 5) Cek saldo
    if saldo_awal is None:
        saldo = sys.maxsize
    else:
        saldo = saldo_awal
    if saldo < total_bayar:
        return {"status": "gagal",
                "pesan": "Transaksi gagal: saldo atau stok tidak mencukupi."}

    # 6) Semua syarat lolos -> kurangi stok, TULIS ulang database
    for barang in keranjang:
        barang["produk"]["stok"] -= barang["jumlah"]
    tulis_json(FILE_PRODUK, daftar_produk)

    # 7) Buat struk, BACA + TULIS ulang riwayat
    nama = str(nama_pembeli).strip()
    if nama == "":
        nama = "Pelanggan"
    struk = {
        "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pembeli": nama,
        "items": daftar_item,
        "subtotal": subtotal,
        "potongan": potongan,
        "total_bayar": total_bayar,
    }
    riwayat = baca_json(FILE_RIWAYAT)
    riwayat.append(struk)
    tulis_json(FILE_RIWAYAT, riwayat)

    return {
        "status": "sukses",
        "pesan": "Transaksi berhasil diproses.",
        "struk": struk,
        "sisa_saldo": saldo - total_bayar,
    }


def simulasi_batch_checkout(daftar_order):
    """Kontrak pengujian.

    Input : [{"nama_pembeli": str, "items": [{"kode": str, "qty": int}], "voucher": str}]
    Output: list hasil per order, mis.
            {"status": "sukses", "pesan": ..., "struk": {...}, "sisa_saldo": int}
            {"status": "gagal", "pesan": ...}
    """
    hasil_batch = []
    for order in daftar_order:
        nama_pembeli = str(order.get("nama_pembeli", "Pembeli Batch"))
        items = order.get("items", [])
        voucher = order.get("voucher")
        saldo_opsional = order.get("saldo")
        hasil = proses_transaksi(nama_pembeli, items, voucher, saldo_opsional)
        hasil_batch.append(hasil)
    return hasil_batch


def ambil_riwayat():
    """Seluruh riwayat transaksi dari riwayat.json."""
    return baca_json(FILE_RIWAYAT)
