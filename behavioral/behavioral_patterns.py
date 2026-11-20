from abc import ABC, abstractmethod


class StrategiVoucher(ABC):
    @abstractmethod
    def hitung_potongan(self, subtotal: int) -> int:
        pass


class TanpaDiskon(StrategiVoucher):
    def hitung_potongan(self, subtotal: int) -> int:
        return 0


class VoucherNominal(StrategiVoucher):
    def __init__(self, nominal: int, min_belanja: int = 0):
        self.nominal = max(0, int(nominal))
        self.min_belanja = max(0, int(min_belanja))

    def hitung_potongan(self, subtotal: int) -> int:
        subtotal = int(subtotal)
        if subtotal <= 0 or subtotal < self.min_belanja:
            return 0
        return min(self.nominal, subtotal)


class VoucherPersen(StrategiVoucher):
    def __init__(self, persen: float, maks_potongan: int = 0):
        self.persen = max(0.0, float(persen))
        self.maks_potongan = max(0, int(maks_potongan))

    def hitung_potongan(self, subtotal: int) -> int:
        subtotal = int(subtotal)
        if subtotal <= 0:
            return 0
        potongan = int(subtotal * (self.persen / 100))
        if self.maks_potongan > 0:
            potongan = min(potongan, self.maks_potongan)
        return min(potongan, subtotal)


class KonteksVoucher:
    def __init__(self, strategi: StrategiVoucher | None = None):
        self._strategi = strategi or TanpaDiskon()

    @property
    def strategi(self) -> StrategiVoucher:
        return self._strategi

    def set_strategi(self, strategi: StrategiVoucher | None):
        self._strategi = strategi or TanpaDiskon()

    def hitung_potongan(self, subtotal: int) -> int:
        subtotal = int(subtotal)
        if subtotal <= 0:
            return 0
        potongan = int(self._strategi.hitung_potongan(subtotal))
        return max(0, min(subtotal, potongan))

    def terapkan(self, subtotal: int) -> int:
        subtotal = int(subtotal)
        if subtotal <= 0:
            return 0
        return max(0, subtotal - self.hitung_potongan(subtotal))