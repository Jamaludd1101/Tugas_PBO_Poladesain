"""Modul instansiasi produk menggunakan Factory Method Pattern."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

try:
    from .produk import Mainan, Makanan, Minuman, Produk
except ImportError:
    from produk import Mainan, Makanan, Minuman, Produk


class ProdukCreator(ABC):
    """Creator abstrak yang mendefinisikan Factory Method pembuatan Produk."""

    kategori_key: ClassVar[str] = ""
    extra_field: ClassVar[str] = ""
    _registry: ClassVar[dict[str, ProdukCreator]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Mendaftarkan setiap ConcreteCreator otomatis ke registry."""
        super().__init_subclass__(**kwargs)
        if cls.kategori_key:
            ProdukCreator._registry[cls.kategori_key.lower()] = cls()

    @abstractmethod
    def create_produk(self, nama: str, harga: int, stok: int, extra: Any) -> Produk:
        """Factory Method yang diimplementasikan oleh subclass konkret."""

    @classmethod
    def get_creator(cls, kategori: str) -> ProdukCreator:
        """Mengambil ConcreteCreator berdasarkan nama kategori tanpa if-elif."""
        key = kategori.strip().lower()
        creator = cls._registry.get(key)
        if creator is None:
            raise ValueError(f"Kategori '{kategori}' tidak dikenal.")
        return creator

    @classmethod
    def buat_produk(
        cls, kategori: str, nama: str, harga: int, stok: int, extra: Any
    ) -> Produk:
        """Membuat instance Produk konkret lewat ConcreteCreator terkait."""
        creator = cls.get_creator(kategori)
        return creator.create_produk(nama, harga, stok, extra)

    @classmethod
    def dari_dict(cls, data: dict[str, Any]) -> Produk:
        """Membangun objek Produk dari dictionary JSON tanpa percabangan."""
        kategori = str(data.get("kategori", ""))
        creator = cls.get_creator(kategori)
        extra_val = data.get(creator.extra_field)
        return creator.create_produk(
            nama=str(data["nama"]),
            harga=int(data["harga"]),
            stok=int(data["stok"]),
            extra=extra_val,
        )


class MakananCreator(ProdukCreator):
    """ConcreteCreator untuk instansiasi produk Makanan."""

    kategori_key = "makanan"
    extra_field = "kadaluarsa"

    def create_produk(self, nama: str, harga: int, stok: int, extra: Any) -> Makanan:
        kadaluarsa = str(extra) if extra is not None else ""
        return Makanan(nama, int(harga), int(stok), kadaluarsa)


class MainanCreator(ProdukCreator):
    """ConcreteCreator untuk instansiasi produk Mainan."""

    kategori_key = "mainan"
    extra_field = "rekomendasi_umur"

    def create_produk(self, nama: str, harga: int, stok: int, extra: Any) -> Mainan:
        umur = int(extra) if extra not in (None, "") else 0
        return Mainan(nama, int(harga), int(stok), umur)


class MinumanCreator(ProdukCreator):
    """ConcreteCreator untuk instansiasi produk Minuman."""

    kategori_key = "minuman"
    extra_field = "ukuran_ml"

    def create_produk(self, nama: str, harga: int, stok: int, extra: Any) -> Minuman:
        ukuran = int(extra) if extra not in (None, "") else 0
        return Minuman(nama, int(harga), int(stok), ukuran)
