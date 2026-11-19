import copy
from abc import ABC, abstractmethod


# ==========================================
# BAGIAN 1: PRODUK & TURUNANNYA (ABSTRACTION, INHERITANCE, PROTOTYPE)
# ==========================================
class Produk(ABC):
    def __init__(self, nama: str, harga: int, stok: int):
        self.__nama = nama  # Private attribute (-)
        self.__harga = harga  # Private attribute (-)
        self.__stok = stok  # Private attribute (-)

    @property
    def harga(self) -> int:
        return self.__harga

    @property
    def nama(self) -> str:
        return self.__nama

    @property
    def stok(self) -> int:
        return self.__stok

    @abstractmethod
    def hitung_diskon(self):
        """Method abstrak (Polymorphism)"""

    def harga_akhir(self) -> int:
        return self.harga - self.hitung_diskon()

    def cek_stok(self, n: int) -> bool:
        return self.stok >= n

    def kurangi_stok(self, n: int):
        if self.cek_stok(n):
            self.__stok -= n

    def clone(
        self,
        nama_baru: str = None,
        harga_baru: int = None,
        stok_baru: int = None,
    ) -> "Produk":
        """
        Prototype Pattern:
        Menduplikasi objek produk menggunakan copy.deepcopy() tanpa mengubah objek asli.
        """
        hasil_clone = copy.deepcopy(self)
        if nama_baru is not None and nama_baru.strip() != "":
            hasil_clone.__nama = nama_baru.strip()
        if harga_baru is not None:
            if harga_baru <= 0:
                raise ValueError("Harga produk hasil duplikasi harus lebih dari 0.")
            hasil_clone.__harga = harga_baru
        if stok_baru is not None:
            if stok_baru < 0:
                raise ValueError("Stok produk hasil duplikasi tidak boleh negatif.")
            hasil_clone.__stok = stok_baru
        return hasil_clone

    def info(self) -> str:
        return f"{self.nama} - Rp{self.harga} (Stok: {self.stok})"

    def to_dict(self) -> dict:
        return {
            "kategori": self.__class__.__name__,
            "nama": self.__nama,
            "harga": self.__harga,
            "stok": self.__stok,
        }


class Makanan(Produk):
    def __init__(self, nama: str, harga: int, stok: int, kadaluarsa: str):
        super().__init__(nama, harga, stok)
        self.__kadaluarsa = kadaluarsa

    def hitung_diskon(self):
        return int((self.harga * 10) / 100)

    def info(self) -> str:
        return f"Makanan: {self.nama}, Harga: Rp{self.harga}, Stok: {self.stok}, Kadaluarsa: {self.__kadaluarsa}"

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["kadaluarsa"] = self.__kadaluarsa
        return data


class Mainan(Produk):
    def __init__(self, nama: str, harga: int, stok: int, rekomendasi_umur: int):
        super().__init__(nama, harga, stok)
        self.__rekomendasi_umur = rekomendasi_umur

    def hitung_diskon(self):
        return int((self.harga * 5) / 100)

    def info(self) -> str:
        return f"Mainan: {self.nama}, Harga: Rp{self.harga}, Stok: {self.stok}, Umur: {self.__rekomendasi_umur}+"

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["rekomendasi_umur"] = self.__rekomendasi_umur
        return data


class Minuman(Produk):
    def __init__(self, nama: str, harga: int, stok: int, ukuran_ml: int):
        super().__init__(nama, harga, stok)
        self.__ukuran_ml = ukuran_ml

    def hitung_diskon(self):
        return int((self.harga * 20) / 100)

    def info(self) -> str:
        return f"Minuman: {self.nama}, Harga: Rp{self.harga}, Stok: {self.stok}, Ukuran: {self.__ukuran_ml}ml"

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["ukuran_ml"] = self.__ukuran_ml
        return data


# ==========================================
# BAGIAN 2: SIMPLE FACTORY (PEMBUATAN PRODUK TERPUSAT)
# ==========================================
class ProdukFactory:
    """
    Simple Factory Pattern:
    Memusatkan logika pembuatan instance Makanan, Mainan, dan Minuman
    agar client (Toko maupun Flask API) tidak bergantung langsung pada subclass.
    """

    @staticmethod
    def buat_produk(kategori: str, nama: str, harga: int, stok: int, extra) -> Produk:
        kat = kategori.strip().lower()
        if kat == "makanan":
            return Makanan(nama, harga, stok, str(extra).strip())
        elif kat == "mainan":
            umur = int(extra) if extra not in (None, "") else 0
            return Mainan(nama, harga, stok, umur)
        elif kat == "minuman":
            ukuran = int(extra) if extra not in (None, "") else 0
            return Minuman(nama, harga, stok, ukuran)
        else:
            raise ValueError(f"Kategori '{kategori}' tidak dikenal.")

    @staticmethod
    def buat_dari_dict(data: dict) -> Produk:
        kategori = data.get("kategori", "").strip().lower()
        nama = data["nama"]
        harga = int(data["harga"])
        stok = int(data["stok"])

        if kategori == "makanan":
            extra = data.get("kadaluarsa", "")
        elif kategori == "mainan":
            extra = data.get("rekomendasi_umur", 0)
        elif kategori == "minuman":
            extra = data.get("ukuran_ml", 0)
        else:
            raise ValueError(f"Kategori '{data.get('kategori')}' tidak dikenal.")

        return ProdukFactory.buat_produk(kategori, nama, harga, stok, extra)
