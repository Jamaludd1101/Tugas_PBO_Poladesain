"""Modul domain Transaksi, RiwayatTransaksi, dan Toko."""

from __future__ import annotations

from datetime import datetime
from typing import Any

try:
    from .database_manager import DatabaseManager
    from .factory import ProdukCreator
    from .pembeli import Pembeli, Voucher
    from .produk import Produk
    from .strategy import DiskonStrategy
except ImportError:
    from database_manager import DatabaseManager
    from factory import ProdukCreator
    from pembeli import Pembeli, Voucher
    from produk import Produk
    from strategy import DiskonStrategy

MENU_BELANJA = """
--- Menu Belanja ---
1. Lihat produk
2. Tambah ke keranjang
3. Lihat keranjang
4. Hapus dari keranjang
5. Pakai voucher
6. Bayar
0. Kembali"""


def format_struk(struk: dict[str, Any]) -> str:
    """Mengubah dictionary struk menjadi teks yang rapi."""
    baris = [f"[{struk['waktu']}] Pembeli: {struk['pembeli']}"]
    for item in struk["items"]:
        baris.append(
            f"  {item['nama']} x{item['qty']} @ "
            f"Rp{item['harga_satuan']} = Rp{item['subtotal']}"
        )
    baris.append(f"  Subtotal    : Rp{struk['subtotal']}")
    if struk["potongan"] > 0:
        baris.append(f"  Potongan    : -Rp{struk['potongan']}")
    baris.append(f"  TOTAL BAYAR : Rp{struk['total_bayar']}")
    return "\n".join(baris)


class Transaksi:
    """Menangani validasi pembayaran atomik dan pembuatan struk."""

    def __init__(
        self,
        pembeli: Pembeli,
        voucher: Voucher | None = None,
        diskon_tambahan: DiskonStrategy | None = None,
    ) -> None:
        self.__pembeli = pembeli
        self.__keranjang = pembeli.keranjang
        self.__voucher = voucher
        self.__diskon_tambahan = diskon_tambahan
        self.__struk: dict[str, Any] | None = None

    def set_diskon_tambahan(self, strategy: DiskonStrategy | None) -> None:
        """Mengatur atau mengganti strategi diskon transaksi saat runtime."""
        self.__diskon_tambahan = strategy

    def hitung_total(self) -> int:
        """Menghitung total bayar setelah diskon produk, voucher, & strategi."""
        total = self.__keranjang.total_harga()
        if self.__voucher:
            total = self.__voucher.terapkan(total)
        if self.__diskon_tambahan:
            total = max(0, total - self.__diskon_tambahan.hitung_diskon(total))
        return total

    def cek_saldo(self) -> bool:
        """Memeriksa kecukupan saldo pembeli."""
        return self.__pembeli.saldo >= self.hitung_total()

    def bayar(self, verbose: bool = True) -> bool:
        """Mengeksekusi pembayaran secara atomik (validasi penuh sebelum mutasi)."""
        items = self.__keranjang.get_items()

        if not items:
            if verbose:
                print("Keranjang masih kosong.")
            return False

        # Agregasi kuantitas per produk untuk mencegah bypass stok item duplikat
        kebutuhan_stok: dict[str, tuple[Produk, int]] = {}
        for barang in items:
            produk: Produk = barang["produk"]
            qty: int = barang["jumlah"]
            if produk.nama in kebutuhan_stok:
                _, total_lama = kebutuhan_stok[produk.nama]
                kebutuhan_stok[produk.nama] = (produk, total_lama + qty)
            else:
                kebutuhan_stok[produk.nama] = (produk, qty)

        for produk, total_qty in kebutuhan_stok.values():
            if not produk.cek_stok(total_qty):
                if verbose:
                    print(f"Stok {produk.nama} tidak cukup.")
                return False

        if not self.cek_saldo():
            if verbose:
                print("Saldo tidak cukup.")
            return False

        # Semua validasi lolos -> mutasi state secara atomik
        total_bayar = self.hitung_total()
        self.__struk = self.cetak_struk()
        self.__pembeli.kurangi_saldo(total_bayar, verbose=verbose)
        for barang in items:
            barang["produk"].kurangi_stok(barang["jumlah"])
        self.__keranjang.kosongkan()
        return True

    def cetak_struk(self) -> dict[str, Any]:
        """Menghasilkan dictionary struk sesuai skema riwayat.json."""
        if self.__struk is not None:
            return self.__struk

        daftar_item: list[dict[str, Any]] = []
        for barang in self.__keranjang.get_items():
            produk: Produk = barang["produk"]
            qty: int = barang["jumlah"]
            harga_satuan = produk.harga_akhir()
            daftar_item.append(
                {
                    "nama": produk.nama,
                    "qty": qty,
                    "harga_satuan": harga_satuan,
                    "subtotal": harga_satuan * qty,
                }
            )

        subtotal = self.__keranjang.total_harga()
        total = self.hitung_total()
        return {
            "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pembeli": self.__pembeli.nama,
            "items": daftar_item,
            "subtotal": subtotal,
            "potongan": subtotal - total,
            "total_bayar": total,
        }


class RiwayatTransaksi:
    """Mengelola daftar struk transaksi melalui Singleton DatabaseManager."""

    def __init__(self, db_manager: DatabaseManager | None = None) -> None:
        self.__db = db_manager or DatabaseManager.get_instance()
        self.__daftar: list[dict[str, Any]] = []

    @property
    def daftar(self) -> list[dict[str, Any]]:
        return self.__daftar

    def tambah_riwayat(self, transaksi: Transaksi) -> None:
        """Menambahkan struk transaksi ke daftar riwayat."""
        self.__daftar.append(transaksi.cetak_struk())

    def tampilkan(self) -> None:
        """Menampilkan seluruh riwayat transaksi ke konsol."""
        if not self.__daftar:
            print("Belum ada riwayat transaksi.")
            return
        for idx, struk in enumerate(self.__daftar, start=1):
            print(f"--- Transaksi #{idx} ---")
            print(format_struk(struk))

    def simpan_ke_json(self, filename: str | None = None) -> None:
        """Menyimpan riwayat ke riwayat.json melalui DatabaseManager."""
        self.__db.simpan_riwayat(self.__daftar, filename=filename)

    def muat_dari_json(self, filename: str | None = None) -> None:
        """Memuat riwayat dari riwayat.json melalui DatabaseManager."""
        self.__daftar = list(self.__db.muat_riwayat(filename=filename))


class Toko:
    """Entitas utama pengelola katalog produk, voucher, dan riwayat."""

    def __init__(self, nama: str, db_manager: DatabaseManager | None = None) -> None:
        self.__nama = nama
        self.__db = db_manager or DatabaseManager.get_instance()
        self.__daftar_produk: list[Produk] = []
        self.__riwayat = RiwayatTransaksi(self.__db)
        self.__riwayat.muat_dari_json()
        self.__daftar_voucher: dict[str, Voucher] = {
            "HEMAT5K": Voucher("HEMAT5K", 5000)
        }

    @property
    def nama(self) -> str:
        return self.__nama

    @property
    def daftar_produk(self) -> list[Produk]:
        return self.__daftar_produk

    @property
    def riwayat(self) -> RiwayatTransaksi:
        return self.__riwayat

    @property
    def daftar_voucher(self) -> dict[str, Voucher]:
        return self.__daftar_voucher

    def tambah_voucher(self, voucher: Voucher) -> None:
        """Mendaftarkan voucher baru ke dalam sistem toko."""
        self.__daftar_voucher[voucher.kode] = voucher

    def ambil_voucher(self, kode: str | None) -> Voucher | None:
        """Mencari objek Voucher berdasarkan kode."""
        if not kode:
            return None
        return self.__daftar_voucher.get(kode.strip().upper())

    def tambah_produk(self, produk: Produk) -> None:
        """Menambahkan instance Produk ke katalog."""
        self.__daftar_produk.append(produk)

    def cari_produk(self, nama: str) -> Produk | None:
        """Mencari produk berdasarkan nama (case-insensitive)."""
        target = nama.strip().lower()
        for produk in self.__daftar_produk:
            if produk.nama.lower() == target:
                return produk
        return None

    def tampilkan_produk(self) -> None:
        """Menampilkan seluruh produk beserta harga setelah diskon."""
        if not self.__daftar_produk:
            print("Belum ada produk.")
            return
        for idx, produk in enumerate(self.__daftar_produk, start=1):
            print(
                f"{idx}. {produk.info()} | " f"Setelah diskon: Rp{produk.harga_akhir()}"
            )

    def tampilkan_riwayat(self) -> None:
        """Menampilkan seluruh riwayat transaksi."""
        self.__riwayat.tampilkan()

    def simpan_database_json(self, filename: str | None = None) -> None:
        """Menyimpan katalog produk ke database_toko.json via Singleton."""
        data = [produk.to_dict() for produk in self.__daftar_produk]
        self.__db.simpan_database_toko(data, filename=filename)

    def muat_database_json(
        self, filename: str | None = None, force_reload: bool = False
    ) -> None:
        """Memuat produk dari JSON menggunakan Factory Method ProdukCreator."""
        data = self.__db.muat_database_toko(
            filename=filename, force_reload=force_reload
        )
        self.__daftar_produk = []
        for item in data:
            try:
                produk = ProdukCreator.dari_dict(item)
                self.__daftar_produk.append(produk)
            except (ValueError, KeyError):
                continue
