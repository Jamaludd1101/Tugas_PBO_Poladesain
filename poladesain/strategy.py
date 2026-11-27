"""Modul algoritma perhitungan diskon menggunakan Strategy Pattern."""

from __future__ import annotations

from abc import ABC, abstractmethod


class DiskonStrategy(ABC):
    """Antarmuka abstrak strategi perhitungan potongan harga."""

    @property
    @abstractmethod
    def nama_strategi(self) -> str:
        """Nama deskriptif strategi diskon."""

    @abstractmethod
    def hitung_diskon(self, nominal: int) -> int:
        """Menghitung besar potongan dalam rupiah dari nominal awal."""


class TanpaDiskonStrategy(DiskonStrategy):
    """Strategi tanpa potongan harga (Rp0)."""

    @property
    def nama_strategi(self) -> str:
        return "Tanpa Diskon (0%)"

    def hitung_diskon(self, nominal: int) -> int:
        return 0


class DiskonPersenStrategy(DiskonStrategy):
    """Strategi diskon berbasis persentase terhadap harga."""

    def __init__(self, persentase: int, label: str = "") -> None:
        if persentase < 0 or persentase > 100:
            raise ValueError("Persentase diskon harus berada di rentang 0-100.")
        self._persentase = persentase
        self._label = label or f"Diskon {persentase}%"

    @property
    def persentase(self) -> int:
        return self._persentase

    @property
    def nama_strategi(self) -> str:
        return self._label

    def hitung_diskon(self, nominal: int) -> int:
        return int((nominal * self._persentase) / 100)


class DiskonMakananStrategy(DiskonPersenStrategy):
    """Aturan diskon baku kategori Makanan: 10%."""

    def __init__(self) -> None:
        super().__init__(persentase=10, label="Diskon Makanan 10%")


class DiskonMainanStrategy(DiskonPersenStrategy):
    """Aturan diskon baku kategori Mainan: 5%."""

    def __init__(self) -> None:
        super().__init__(persentase=5, label="Diskon Mainan 5%")


class DiskonMinumanStrategy(DiskonPersenStrategy):
    """Aturan diskon baku kategori Minuman: 20%."""

    def __init__(self) -> None:
        super().__init__(persentase=20, label="Diskon Minuman 20%")


class TanpaVoucherStrategy(DiskonStrategy):
    """Strategi transaksi tanpa voucher."""

    @property
    def nama_strategi(self) -> str:
        return "Tanpa Voucher"

    def hitung_diskon(self, nominal: int) -> int:
        return 0


class VoucherNominalStrategy(DiskonStrategy):
    """Strategi potongan voucher nominal tetap (misal HEMAT5K = Rp5.000)."""

    def __init__(self, kode: str, potongan: int) -> None:
        self._kode = kode.strip().upper()
        self._potongan = max(0, potongan)

    @property
    def nama_strategi(self) -> str:
        return f"Voucher {self._kode} (-Rp{self._potongan})"

    def hitung_diskon(self, nominal: int) -> int:
        # Voucher hanya berlaku jika subtotal belanja >= nilai potongan
        if nominal >= self._potongan:
            return self._potongan
        return 0


class VoucherPersenStrategy(DiskonStrategy):
    """Strategi voucher persentase opsional dengan batas maksimal potongan."""

    def __init__(
        self,
        kode: str,
        persentase: int,
        maks_potongan: int | None = None,
    ) -> None:
        self._kode = kode.strip().upper()
        self._persentase = persentase
        self._maks_potongan = maks_potongan

    @property
    def nama_strategi(self) -> str:
        return f"Voucher {self._kode} ({self._persentase}%)"

    def hitung_diskon(self, nominal: int) -> int:
        potongan = int((nominal * self._persentase) / 100)
        if self._maks_potongan is not None:
            return min(potongan, self._maks_potongan)
        return potongan
