"""CLI Minimarket - versi prosedural. Jalankan: python main.py"""

import fungsi_minimarket as fm

MENU_BELANJA = """
--- Menu Belanja ---
1. Lihat produk
2. Tambah ke keranjang
3. Lihat keranjang
4. Hapus dari keranjang
5. Pakai voucher
6. Bayar
0. Kembali"""


def input_angka(pesan):
    """Minta input sampai pengguna mengisi angka bulat >= 0."""
    while True:
        try:
            nilai = int(input(pesan))
            if nilai >= 0:
                return nilai
            print("Angka tidak boleh negatif.")
        except ValueError:
            print("Masukkan angka yang valid.")


def tampilkan_produk():
    daftar = fm.baca_json(fm.FILE_PRODUK)
    if not daftar:
        print("Belum ada produk.")
    for i, p in enumerate(daftar, start=1):
        print(f"{i}. {p['kategori']}: {p['nama']} - Rp{p['harga']} "
              f"(Stok: {p['stok']}) | Setelah diskon: Rp{fm.hitung_harga_akhir(p)}")


def format_struk(s):
    baris = [f"[{s['waktu']}] Pembeli: {s['pembeli']}"]
    for it in s["items"]:
        baris.append(f"  {it['nama']} x{it['qty']} @ Rp{it['harga_satuan']} = Rp{it['subtotal']}")
    baris.append(f"  Subtotal    : Rp{s['subtotal']}")
    if s["potongan"] > 0:
        baris.append(f"  Potongan    : -Rp{s['potongan']}")
    baris.append(f"  TOTAL BAYAR : Rp{s['total_bayar']}")
    return "\n".join(baris)


def tambah_produk_interaktif():
    kategori = input("Kategori (makanan/mainan/minuman): ").strip().lower()
    if kategori not in ("makanan", "mainan", "minuman"):
        print("Kategori tidak dikenal.")
        return
    nama = input("Nama produk: ").strip()
    harga = input("Harga: ")
    stok = input("Stok: ")
    if kategori == "makanan":
        extra = input("Tanggal kadaluarsa: ")
    elif kategori == "mainan":
        extra = input("Rekomendasi umur: ")
    else:
        extra = input("Ukuran (ml): ")
    print(fm.tambah_produk(kategori, nama, harga, stok, extra)["pesan"])


def mulai_belanja(pembeli):
    keranjang = []   # list of {"kode": str, "qty": int}
    voucher = ""
    while True:
        print(MENU_BELANJA)
        pilih = input("Pilih: ").strip()

        if pilih == "1":
            tampilkan_produk()

        elif pilih == "2":
            produk = fm.cari_produk_nama(fm.baca_json(fm.FILE_PRODUK), input("Nama produk: "))
            if produk is None:
                print("Produk tidak ditemukan.")
                continue
            try:
                n = int(input("Jumlah: "))
            except ValueError:
                n = 0
            if n <= 0:
                print("Jumlah harus angka lebih dari 0.")
                continue
            sudah = 0
            for k in keranjang:
                if k["kode"] == produk["nama"]:
                    sudah = k["qty"]
            if produk["stok"] < sudah + n:
                print(f"Gagal: stok {produk['nama']} tidak mencukupi. (Sisa stok: {produk['stok']})")
                continue
            if sudah > 0:
                for k in keranjang:
                    if k["kode"] == produk["nama"]:
                        k["qty"] += n
            else:
                keranjang.append({"kode": produk["nama"], "qty": n})
            print(f"{produk['nama']} sebanyak {n} dimasukkan ke keranjang.")

        elif pilih == "3":
            if not keranjang:
                print("Keranjang kosong.")
            for k in keranjang:
                print(f"- {k['kode']} x{k['qty']}")

        elif pilih == "4":
            nama = input("Nama produk: ").strip().lower()
            ditemukan = False
            for k in keranjang:
                if k["kode"].lower() == nama:
                    keranjang.remove(k)
                    ditemukan = True
                    print(f"{k['kode']} berhasil dihapus dari keranjang.")
                    break
            if not ditemukan:
                print("Produk tidak ada di keranjang.")

        elif pilih == "5":
            kode = input("Kode voucher: ").strip().upper()
            if kode in fm.DAFTAR_VOUCHER:
                voucher = kode
                print("Voucher dipasang.")
            else:
                print("Voucher tidak ditemukan.")

        elif pilih == "6":
            hasil = fm.proses_transaksi(pembeli["nama"], keranjang, voucher, pembeli["saldo"])
            if hasil["status"] == "sukses":
                pembeli["saldo"] = hasil["sisa_saldo"]
                print("\nPembayaran berhasil!")
                print(format_struk(hasil["struk"]))
                print(f"Sisa saldo: Rp{pembeli['saldo']}")
                break
            print(hasil["pesan"])

        elif pilih == "0":
            break
        else:
            print("Pilihan tidak valid.")


def tampilkan_riwayat():
    riwayat = fm.ambil_riwayat()
    if not riwayat:
        print("Belum ada riwayat transaksi.")
    for i, s in enumerate(riwayat, start=1):
        print(f"--- Transaksi #{i} ---")
        print(format_struk(s))


if __name__ == "__main__":
    print("Sistem Minimarket Kita (prosedural) siap dijalankan.")
    nama = input("Nama pembeli: ").strip()
    saldo = input_angka("Saldo awal: ")
    pembeli = {"nama": nama, "saldo": saldo}

    while True:
        print("\n=== MENU UTAMA ===")
        print("1. Tambah produk")
        print("2. Lihat produk")
        print("3. Cari produk")
        print("4. Mulai belanja")
        print("5. Riwayat transaksi")
        print("0. Keluar")
        pilihan = input("Pilih opsi: ").strip()

        if pilihan == "1":
            tambah_produk_interaktif()
        elif pilihan == "2":
            tampilkan_produk()
        elif pilihan == "3":
            p = fm.cari_produk_nama(fm.baca_json(fm.FILE_PRODUK), input("Cari produk: "))
            if p:
                print(f"{p['kategori']}: {p['nama']} - Rp{p['harga']} (Stok: {p['stok']})")
            else:
                print("Produk tidak ditemukan.")
        elif pilihan == "4":
            mulai_belanja(pembeli)
        elif pilihan == "5":
            tampilkan_riwayat()
        elif pilihan == "0":
            print("Terima kasih!")
            break
        else:
            print("Pilihan tidak valid.")
