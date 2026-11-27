"""Modul entitas Produk yang terintegrasi dengan DiskonStrategy."""

from __future__ import annotations

from abc import ABC
from typing import Any

try:
    from .strategy import (
        DiskonMainanStrategy,
        DiskonMakananStrategy,
        DiskonMinumanStrategy,
        DiskonStrategy,
        TanpaDiskonStrategy,
    )
except ImportError:
    from strategy import (
        DiskonMainanStrategy,
        DiskonMakananStrategy,
        DiskonMinumanStrategy,
        DiskonStrategy,
        TanpaDiskonStrategy,
    )


class Produk(ABC):
    """Kelas dasar abstrak untuk seluruh item produk di LokaMart."""

    def __init__(
        self,
        nama: str,
        harga: int,
        stok: int,
        diskon_strategy: DiskonStrategy | None = None,
    ) -> None:
        self.__nama = nama
        self.__harga = harga
        self.__stok = stok
        self._diskon_strategy: DiskonStrategy = diskon_strategy or TanpaDiskonStrategy()

    @property
    def nama(self) -> str:
        return self.__nama

    @property
    def harga(self) -> int:
        return self.__harga

    @property
    def stok(self) -> int:
        return self.__stok

    @property
    def diskon_strategy(self) -> DiskonStrategy:
        return self._diskon_strategy

    def set_diskon_strategy(self, strategy: DiskonStrategy) -> None:
        """Mengubah algoritma diskon produk saat runtime (Strategy Pattern)."""
        self._diskon_strategy = strategy

    def hitung_diskon(self) -> int:
        """Menghitung potongan harga menggunakan strategi aktif."""
        return self._diskon_strategy.hitung_diskon(self.__harga)

    def harga_akhir(self) -> int:
        """Mengembalikan harga satuan setelah dikurangi diskon produk."""
        return self.__harga - self.hitung_diskon()

    def cek_stok(self, jumlah: int) -> bool:
        """Memvalidasi ketersediaan stok untuk kuantitas tertentu."""
        return jumlah > 0 and self.__stok >= jumlah

    def kurangi_stok(self, jumlah: int) -> None:
        """Mengurangi stok produk jika mencukupi."""
        if self.cek_stok(jumlah):
            self.__stok -= jumlah

    def info(self) -> str:
        """Deskripsi ringkas produk."""
        return f"{self.nama} - Rp{self.harga} (Stok: {self.stok})"

    def to_dict(self) -> dict[str, Any]:
        """Serialisasi produk ke dictionary sesuai skema database_toko.json."""
        return {
            "kategori": self.__class__.__name__,
            "nama": self.__nama,
            "harga": self.__harga,
            "stok": self.__stok,
        }


class Makanan(Produk):
    """Produk kategori Makanan dengan diskon default 10%."""

    def __init__(
        self,
        nama: str,
        harga: int,
        stok: int,
        kadaluarsa: str,
        diskon_strategy: DiskonStrategy | None = None,
    ) -> None:
        super().__init__(
            nama=nama,
            harga=harga,
            stok=stok,
            diskon_strategy=diskon_strategy or DiskonMakananStrategy(),
        )
        self.__kadaluarsa = kadaluarsa

    @property
    def kadaluarsa(self) -> str:
        return self.__kadaluarsa

    def info(self) -> str:
        return (
            f"Makanan: {self.nama}, Harga: Rp{self.harga}, "
            f"Stok: {self.stok}, Kadaluarsa: {self.__kadaluarsa}"
        )

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["kadaluarsa"] = self.__kadaluarsa
        return data


class Mainan(Produk):
    """Produk kategori Mainan dengan diskon default 5%."""

    def __init__(
        self,
        nama: str,
        harga: int,
        stok: int,
        rekomendasi_umur: int,
        diskon_strategy: DiskonStrategy | None = None,
    ) -> None:
        super().__init__(
            nama=nama,
            harga=harga,
            stok=stok,
            diskon_strategy=diskon_strategy or DiskonMainanStrategy(),
        )
        self.__rekomendasi_umur = rekomendasi_umur

    @property
    def rekomendasi_umur(self) -> int:
        return self.__rekomendasi_umur

    def info(self) -> str:
        return (
            f"Mainan: {self.nama}, Harga: Rp{self.harga}, "
            f"Stok: {self.stok}, Umur: {self.__rekomendasi_umur}+"
        )

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["rekomendasi_umur"] = self.__rekomendasi_umur
        return data


class Minuman(Produk):
    """Produk kategori Minuman dengan diskon default 20%."""

    def __init__(
        self,
        nama: str,
        harga: int,
        stok: int,
        ukuran_ml: int,
        diskon_strategy: DiskonStrategy | None = None,
    ) -> None:
        super().__init__(
            nama=nama,
            harga=harga,
            stok=stok,
            diskon_strategy=diskon_strategy or DiskonMinumanStrategy(),
        )
        self.__ukuran_ml = ukuran_ml

    @property
    def ukuran_ml(self) -> int:
        return self.__ukuran_ml

    def info(self) -> str:
        return (
            f"Minuman: {self.nama}, Harga: Rp{self.harga}, "
            f"Stok: {self.stok}, Ukuran: {self.__ukuran_ml}ml"
        )

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["ukuran_ml"] = self.__ukuran_ml
        return data
