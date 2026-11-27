"""Modul entitas Voucher, Keranjang, dan Pembeli."""

from __future__ import annotations

from typing import Any

try:
    from .produk import Produk
    from .strategy import DiskonStrategy, VoucherNominalStrategy
except ImportError:
    from produk import Produk
    from strategy import DiskonStrategy, VoucherNominalStrategy


class Voucher:
    """Konteks voucher yang mendelegasikan perhitungan ke DiskonStrategy."""

    def __init__(
        self,
        kode: str,
        potongan: int = 0,
        strategy: DiskonStrategy | None = None,
    ) -> None:
        self.__kode = kode.strip().upper()
        self.__potongan = potongan
        self.__strategy: DiskonStrategy = strategy or VoucherNominalStrategy(
            self.__kode, potongan
        )

    @property
    def kode(self) -> str:
        return self.__kode

    @property
    def strategy(self) -> DiskonStrategy:
        return self.__strategy

    def set_strategy(self, strategy: DiskonStrategy) -> None:
        """Mengganti strategi perhitungan voucher secara dinamis saat runtime."""
        self.__strategy = strategy

    def hitung_potongan(self, total: int) -> int:
        """Menghitung potongan voucher berdasarkan strategi aktif."""
        return self.__strategy.hitung_diskon(total)

    def berlaku(self, total: int) -> bool:
        """Mengecek apakah voucher menghasilkan potongan pada total tertentu."""
        return self.hitung_potongan(total) > 0

    def terapkan(self, total: int) -> int:
        """Mengembalikan total akhir setelah potongan voucher."""
        return total - self.hitung_potongan(total)


class Keranjang:
    """Komposisi keranjang belanja milik Pembeli."""

    def __init__(self) -> None:
        self.__item: list[dict[str, Any]] = []

    def tambah(self, produk: Produk, jumlah: int, verbose: bool = True) -> bool:
        """Menambahkan produk ke keranjang setelah memvalidasi stok."""
        if jumlah <= 0:
            if verbose:
                print("Jumlah barang harus lebih dari 0.")
            return False

        for barang in self.__item:
            if barang["produk"].nama == produk.nama:
                total_baru = barang["jumlah"] + jumlah
                if not produk.cek_stok(total_baru):
                    if verbose:
                        print(
                            f"Gagal: stok {produk.nama} tidak mencukupi. "
                            f"(Sisa stok: {produk.stok})"
                        )
                    return False
                barang["jumlah"] = total_baru
                if verbose:
                    print(
                        f"Jumlah {produk.nama} di keranjang diperbarui "
                        f"menjadi {barang['jumlah']}."
                    )
                return True

        if not produk.cek_stok(jumlah):
            if verbose:
                print(
                    f"Gagal: stok {produk.nama} tidak mencukupi. "
                    f"(Sisa stok: {produk.stok})"
                )
            return False

        self.__item.append({"produk": produk, "jumlah": jumlah})
        if verbose:
            print(f"{produk.nama} sebanyak {jumlah} dimasukkan ke keranjang.")
        return True

    def hapus(self, produk: Produk, verbose: bool = True) -> bool:
        """Menghapus item produk dari keranjang."""
        for barang in self.__item:
            if barang["produk"].nama == produk.nama:
                self.__item.remove(barang)
                if verbose:
                    print(f"{produk.nama} berhasil dihapus dari keranjang.")
                return True

        if verbose:
            print(f"Gagal: {produk.nama} tidak ditemukan di keranjang.")
        return False

    def total_harga(self) -> int:
        """Menghitung total harga seluruh item setelah diskon kategori."""
        return sum(
            barang["produk"].harga_akhir() * barang["jumlah"] for barang in self.__item
        )

    def get_items(self) -> list[dict[str, Any]]:
        """Mengembalikan daftar item di dalam keranjang."""
        return self.__item

    def kosongkan(self) -> None:
        """Mengosongkan isi keranjang."""
        self.__item.clear()


class Pembeli:
    """Entitas pembeli dengan saldo dan relasi komposisi ke Keranjang."""

    def __init__(self, nama: str, saldo: int) -> None:
        self.__nama = nama
        self.__saldo = saldo
        self.__keranjang = Keranjang()

    @property
    def keranjang(self) -> Keranjang:
        return self.__keranjang

    @property
    def nama(self) -> str:
        return self.__nama

    @property
    def saldo(self) -> int:
        return self.__saldo

    def tambah_ke_keranjang(
        self, produk: Produk, jumlah: int, verbose: bool = True
    ) -> bool:
        """Menambahkan produk ke keranjang milik pembeli."""
        return self.__keranjang.tambah(produk, jumlah, verbose=verbose)

    def kurangi_saldo(self, nominal: int, verbose: bool = True) -> bool:
        """Memotong saldo pembeli jika mencukupi."""
        if self.__saldo >= nominal:
            self.__saldo -= nominal
            if verbose:
                print(
                    f"Saldo berhasil dipotong. "
                    f"Sisa saldo {self.__nama}: Rp{self.__saldo}"
                )
            return True

        if verbose:
            print(
                f"Transaksi gagal: Saldo {self.__nama} tidak mencukupi! "
                f"(Saldo: Rp{self.__saldo}, Tagihan: Rp{nominal})"
            )
        return False
