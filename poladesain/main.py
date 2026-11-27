"""Antarmuka CLI LokaMart-DPF yang terintegrasi dengan MinimarketFacade."""

from __future__ import annotations

from typing import Any

try:
    from .minimarket_facade import MinimarketFacade, simulasi_batch_checkout
    from .pembeli import Pembeli
    from .toko import MENU_BELANJA, Transaksi, format_struk
except ImportError:
    from minimarket_facade import MinimarketFacade
    from pembeli import Pembeli
    from toko import MENU_BELANJA, Transaksi, format_struk


def input_angka(pesan: str) -> int:
    """Meminta input angka bulat >= 0 hingga valid."""
    while True:
        try:
            nilai = int(input(pesan))
            if nilai >= 0:
                return nilai
            print("Angka tidak boleh negatif.")
        except ValueError:
            print("Masukkan angka yang valid.")


def tambah_produk_cli(facade: MinimarketFacade) -> None:
    """Alur interaktif penambahan produk melalui MinimarketFacade."""
    kategori = input("Kategori (makanan/mainan/minuman): ").strip().lower()
    if kategori not in ("makanan", "mainan", "minuman"):
        print("Kategori tidak dikenal.")
        return

    nama = input("Nama produk: ").strip()
    harga = input_angka("Harga: ")
    stok = input_angka("Stok: ")

    prompt_extra = {
        "makanan": "Tanggal kadaluarsa: ",
        "mainan": "Rekomendasi umur: ",
        "minuman": "Ukuran (ml): ",
    }
    extra: Any = input(prompt_extra[kategori]).strip()

    hasil = facade.tambah_produk(kategori, nama, harga, stok, extra)
    print(hasil["pesan"])


def mulai_transaksi_cli(facade: MinimarketFacade, pembeli: Pembeli) -> None:
    """Menjalankan sesi belanja CLI dan checkout atomik via Facade."""
    kode_voucher: str | None = None
    pembeli.keranjang.kosongkan()

    while True:
        print(MENU_BELANJA)
        pilih = input("Pilih: ").strip()

        if pilih == "1":
            facade.toko.tampilkan_produk()

        elif pilih == "2":
            produk = facade.cari_produk(input("Nama produk: "))
            if produk is None:
                print("Produk tidak ditemukan.")
            else:
                jumlah = input_angka("Jumlah: ")
                pembeli.tambah_ke_keranjang(produk, jumlah, verbose=True)

        elif pilih == "3":
            items = pembeli.keranjang.get_items()
            if not items:
                print("Keranjang kosong.")
            else:
                for barang in items:
                    print(f"- {barang['produk'].nama} x{barang['jumlah']}")
                voucher_obj = facade.toko.ambil_voucher(kode_voucher)
                pratinjau = Transaksi(pembeli, voucher_obj).hitung_total()
                print(f"Total saat ini: Rp{pratinjau}")

        elif pilih == "4":
            produk = facade.cari_produk(input("Nama produk: "))
            if produk is None:
                print("Produk tidak ditemukan.")
            else:
                pembeli.keranjang.hapus(produk, verbose=True)

        elif pilih == "5":
            kode_input = input("Kode voucher: ").strip().upper()
            if facade.toko.ambil_voucher(kode_input) is not None:
                kode_voucher = kode_input
                print("Voucher dipasang.")
            else:
                print("Voucher tidak ditemukan.")

        elif pilih == "6":
            items_payload = [
                {
                    "kode": barang["produk"].nama,
                    "qty": barang["jumlah"],
                }
                for barang in pembeli.keranjang.get_items()
            ]
            hasil = facade.proses_checkout(
                nama_pembeli=pembeli.nama,
                items=items_payload,
                kode_voucher=kode_voucher,
                pembeli=pembeli,
                simpan_ke_disk=True,
                verbose=True,
            )
            if hasil["status"] == "sukses":
                print("\nPembayaran berhasil!")
                print(format_struk(hasil["struk"]))
                break
            print(hasil["pesan"])

        elif pilih == "0":
            break

        else:
            print("Pilihan tidak valid.")


if __name__ == "__main__":
    facade_utama = MinimarketFacade("LokaMart")
    print(f"Sistem {facade_utama.toko.nama} siap dijalankan.")

    nama_pembeli = input("Nama pembeli: ").strip()
    saldo_awal = input_angka("Saldo awal: ")
    pembeli_aktif = Pembeli(nama_pembeli, saldo_awal)

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
            tambah_produk_cli(facade_utama)
        elif pilihan == "2":
            facade_utama.toko.tampilkan_produk()
        elif pilihan == "3":
            hasil_cari = facade_utama.cari_produk(input("Cari produk: "))
            print(hasil_cari.info() if hasil_cari else "Produk tidak ditemukan.")
        elif pilihan == "4":
            mulai_transaksi_cli(facade_utama, pembeli_aktif)
        elif pilihan == "5":
            facade_utama.toko.tampilkan_riwayat()
        elif pilihan == "0":
            print("Terima kasih!")
            break
        else:
            print("Pilihan tidak valid.")
