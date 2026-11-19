import json
import os
from datetime import datetime

from pembeli import Pembeli, Voucher
from produk import Produk, ProdukFactory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "database_toko.json")
DEFAULT_RIWAYAT_PATH = os.path.join(BASE_DIR, "riwayat.json")

MENU_BELANJA = """
--- Menu Belanja ---
1. Lihat produk
2. Tambah ke keranjang
3. Lihat keranjang
4. Hapus dari keranjang
5. Pakai voucher
6. Bayar
0. Kembali"""


def format_struk(s: dict) -> str:
    """Ubah dict struk menjadi teks yang rapi."""
    baris = [f"[{s['waktu']}] Pembeli: {s['pembeli']}"]
    for it in s["items"]:
        baris.append(
            f"  {it['nama']} x{it['qty']} @ Rp{it['harga_satuan']} = Rp{it['subtotal']}"
        )
    baris.append(f"  Subtotal    : Rp{s['subtotal']}")
    if s["potongan"] > 0:
        baris.append(f"  Potongan    : -Rp{s['potongan']}")
    baris.append(f"  TOTAL BAYAR : Rp{s['total_bayar']}")
    return "\n".join(baris)


class Transaksi:
    def __init__(self, pembeli: Pembeli, voucher: Voucher = None):
        self.__pembeli = pembeli
        self.__keranjang = pembeli.keranjang  # Agregasi dari pembeli
        self.__voucher = voucher
        self.__struk = None  # terisi setelah bayar() berhasil

    def hitung_total(self) -> int:
        total = self.__keranjang.total_harga()
        if self.__voucher:
            total = self.__voucher.terapkan(
                total
            )  # terapkan() sudah mengecek syarat voucher
        return total

    def cek_saldo(self) -> bool:
        return self.__pembeli.saldo >= self.hitung_total()

    def bayar(self) -> bool:
        items = self.__keranjang.get_items()

        # 1) Cek semua syarat dulu (data belum diubah sama sekali)
        if not items:
            print("Keranjang masih kosong.")
            return False
        for barang in items:
            if not barang["produk"].cek_stok(barang["jumlah"]):
                print(f"Stok {barang['produk'].nama} tidak cukup.")
                return False
        if not self.cek_saldo():
            print("Saldo tidak cukup.")
            return False

        # 2) Semua syarat terpenuhi -> baru ubah data
        self.__struk = self.cetak_struk()  # simpan struk SEBELUM keranjang dikosongkan
        self.__pembeli.kurangi_saldo(self.hitung_total())
        for barang in items:
            barang["produk"].kurangi_stok(barang["jumlah"])
        self.__keranjang.kosongkan()
        return True

    def cetak_struk(self) -> dict:
        """Struk final kalau sudah dibayar, atau pratinjau kalau belum."""
        if self.__struk:
            return self.__struk
        daftar_item = []
        for barang in self.__keranjang.get_items():
            produk, qty = barang["produk"], barang["jumlah"]
            daftar_item.append(
                {
                    "nama": produk.nama,
                    "qty": qty,
                    "harga_satuan": produk.harga_akhir(),
                    "subtotal": produk.harga_akhir() * qty,
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


# ==========================================
# BUILDER PATTERN: PEMBENTUKAN TRANSAKSI BERTAHAP
# ==========================================
class TransaksiBuilder:
    """
    Builder Pattern:
    Menyusun komponen Transaksi (pembeli, item keranjang, dan voucher opsional)
    secara bertahap menggunakan method chaining sebelum memanggil .build().
    """

    def __init__(self):
        self.__pembeli = None
        self.__voucher = None

    def set_pembeli(self, pembeli: Pembeli) -> "TransaksiBuilder":
        self.__pembeli = pembeli
        return self

    def tambah_item(self, produk: Produk, jumlah: int) -> "TransaksiBuilder":
        if self.__pembeli is None:
            raise ValueError("Pembeli harus diatur sebelum menambahkan item.")
        self.__pembeli.tambah_ke_keranjang(produk, jumlah)
        return self

    def set_voucher(self, voucher: Voucher) -> "TransaksiBuilder":
        self.__voucher = voucher
        return self

    def build(self) -> Transaksi:
        if self.__pembeli is None:
            raise ValueError("Objek Transaksi tidak dapat dibuat tanpa Pembeli.")
        return Transaksi(self.__pembeli, self.__voucher)


class RiwayatTransaksi:
    def __init__(self):
        self.__daftar = []  # isinya dict struk, bukan objek Transaksi

    @property
    def daftar(self) -> list:
        return list(self.__daftar)

    def tambah_riwayat(self, t: Transaksi):
        self.__daftar.append(t.cetak_struk())

    def tampilkan(self):
        if not self.__daftar:
            print("Belum ada riwayat transaksi.")
        for i, struk in enumerate(self.__daftar, start=1):
            print(f"--- Transaksi #{i} ---")
            print(format_struk(struk))

    def simpan_ke_json(self, filename: str = DEFAULT_RIWAYAT_PATH):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.__daftar, f, indent=4, ensure_ascii=False)

    def muat_dari_json(self, filename: str = DEFAULT_RIWAYAT_PATH):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                self.__daftar = json.load(f)
        except FileNotFoundError:
            self.__daftar = []


# ==========================================
# SINGLETON PATTERN: SATU INSTANCE PUSAT TOKO
# ==========================================
class Toko:
    __instance = None

    def __new__(cls, nama: str = "Minimarket OOP"):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self, nama: str = "Minimarket OOP"):
        if self.__initialized:
            return
        self.__nama = nama
        self.__daftar_produk = []
        self.__riwayat = RiwayatTransaksi()
        self.__riwayat.muat_dari_json()
        # Voucher yang tersedia
        self.__daftar_voucher = {"HEMAT5K": Voucher("HEMAT5K", 5000)}
        self.__initialized = True

    @classmethod
    def get_instance(cls, nama: str = "Minimarket OOP") -> "Toko":
        """Akses global ke satu-satunya instance Toko."""
        if cls.__instance is None:
            cls.__instance = cls(nama)
        return cls.__instance

    @property
    def nama(self) -> str:
        return self.__nama

    @property
    def daftar_produk(self):
        return self.__daftar_produk

    # ---------- Produk ----------
    def tambah_produk(self, p: Produk):
        self.__daftar_produk.append(p)

    def tambah_produk_interaktif(self):
        self.muat_database_json()
        kategori = input("Kategori (makanan/mainan/minuman): ").strip().lower()
        if kategori not in ("makanan", "mainan", "minuman"):
            print("Kategori tidak dikenal.")
            return
        nama = input("Nama produk: ").strip()
        if nama == "" or self.cari_produk(nama):
            print("Nama kosong atau produk sudah ada.")
            return
        try:
            harga = int(input("Harga: "))
            stok = int(input("Stok: "))
            if harga <= 0 or stok < 0:
                print("Harga harus lebih dari 0 dan stok tidak boleh negatif.")
                return

            if kategori == "makanan":
                extra = input("Tanggal kadaluarsa: ")
            elif kategori == "mainan":
                extra = int(input("Rekomendasi umur: "))
            else:
                extra = int(input("Ukuran (ml): "))

            # Menggunakan Simple Factory (ProdukFactory)
            p = ProdukFactory.buat_produk(kategori, nama, harga, stok, extra)
        except ValueError as err:
            print(f"Input tidak valid: {err}")
            return

        self.tambah_produk(p)
        self.simpan_database_json()
        print(f"Produk '{nama}' ditambahkan.")

    def duplikat_produk_interaktif(self):
        """Fitur duplikasi produk menggunakan Prototype Pattern (.clone())."""
        self.muat_database_json()
        produk_asal = self.__minta_produk()
        if not produk_asal:
            return

        nama_baru = input(
            f"Nama produk baru (kosongkan untuk '{produk_asal.nama} (Promo)'): "
        ).strip()
        if not nama_baru:
            nama_baru = f"{produk_asal.nama} (Promo)"

        if self.cari_produk(nama_baru):
            print("Produk dengan nama tersebut sudah ada.")
            return

        try:
            harga_input = input(
                f"Harga baru (kosongkan untuk Rp{produk_asal.harga}): "
            ).strip()
            harga_baru = int(harga_input) if harga_input else None

            stok_input = input(
                f"Stok baru (kosongkan untuk {produk_asal.stok}): "
            ).strip()
            stok_baru = int(stok_input) if stok_input else None

            # Menggunakan Prototype Pattern (.clone())
            produk_baru = produk_asal.clone(
                nama_baru=nama_baru,
                harga_baru=harga_baru,
                stok_baru=stok_baru,
            )
        except ValueError as err:
            print(f"Input tidak valid: {err}")
            return

        self.tambah_produk(produk_baru)
        self.simpan_database_json()
        print(f"Produk berhasil diduplikasi menjadi '{produk_baru.nama}'.")

    def cari_produk(self, nama: str):
        for p in self.__daftar_produk:
            if p.nama.lower() == nama.strip().lower():
                return p
        return None

    def cari_voucher(self, kode: str):
        return self.__daftar_voucher.get(kode.strip().upper())

    def tampilkan_produk(self):
        self.muat_database_json()
        if not self.__daftar_produk:
            print("Belum ada produk.")
        for i, p in enumerate(self.__daftar_produk, start=1):
            # info() beda tiap jenis produk (polimorfisme)
            print(f"{i}. {p.info()} | Setelah diskon: Rp{p.harga_akhir()}")

    def __minta_produk(self):
        """Tanya nama produk ke pengguna, kembalikan produknya (atau None)."""
        produk = self.cari_produk(input("Nama produk: "))
        if produk is None:
            print("Produk tidak ditemukan.")
        return produk

    # ---------- Transaksi & Riwayat ----------
    def catat_transaksi(self, transaksi: Transaksi):
        """Menyimpan transaksi berhasil ke RiwayatTransaksi & file JSON."""
        self.__riwayat.muat_dari_json()
        self.__riwayat.tambah_riwayat(transaksi)
        self.__riwayat.simpan_ke_json()
        self.simpan_database_json()

    def get_daftar_riwayat(self) -> list:
        self.__riwayat.muat_dari_json()
        return self.__riwayat.daftar

    def mulai_transaksi(self, pembeli: Pembeli):
        self.muat_database_json()
        voucher = None
        # Builder dipakai bertahap sepanjang sesi transaksi pembeli
        builder = TransaksiBuilder().set_pembeli(pembeli)

        while True:
            print(MENU_BELANJA)
            pilih = input("Pilih: ").strip()

            if pilih == "1":
                self.tampilkan_produk()

            elif pilih == "2":
                produk = self.__minta_produk()
                if produk:
                    try:
                        n = int(input("Jumlah: "))
                    except ValueError:
                        n = 0
                    if n > 0:
                        builder.tambah_item(produk, n)
                    else:
                        print("Jumlah harus angka lebih dari 0.")

            elif pilih == "3":
                items = pembeli.keranjang.get_items()
                if not items:
                    print("Keranjang kosong.")
                else:
                    for barang in items:
                        satuan = barang["produk"].harga_akhir()
                        qty = barang["jumlah"]
                        print(
                            f"- {barang['produk'].nama} x{qty} @ Rp{satuan} = Rp{satuan * qty}"
                        )
                    transaksi_preview = builder.set_voucher(voucher).build()
                    struk_preview = transaksi_preview.cetak_struk()
                    print(f"Subtotal      : Rp{struk_preview['subtotal']}")
                    if voucher:
                        if struk_preview["potongan"] > 0:
                            print(
                                f"Voucher {voucher.kode}: -Rp{struk_preview['potongan']}"
                            )
                        else:
                            print(
                                f"Voucher {voucher.kode}: belum berlaku (minimal belanja Rp{voucher.potongan})"
                            )
                    print(f"Total saat ini: Rp{struk_preview['total_bayar']}")

            elif pilih == "4":
                produk = self.__minta_produk()
                if produk:
                    pembeli.keranjang.hapus(produk)

            elif pilih == "5":
                kode_input = input("Kode voucher: ").strip().upper()
                voucher_baru = self.cari_voucher(kode_input)
                if voucher_baru:
                    voucher = voucher_baru
                    builder.set_voucher(voucher)
                    subtotal_saat_ini = pembeli.keranjang.total_harga()
                    if voucher.berlaku(subtotal_saat_ini):
                        print(
                            f"Voucher {voucher.kode} dipasang (potongan Rp{voucher.potongan})."
                        )
                    else:
                        print(
                            f"Voucher {voucher.kode} dipasang, akan otomatis terpotong jika subtotal >= Rp{voucher.potongan}."
                        )
                else:
                    print("Voucher tidak ditemukan.")

            elif pilih == "6":
                transaksi = builder.set_voucher(voucher).build()
                if transaksi.bayar():
                    self.catat_transaksi(transaksi)
                    print("\nPembayaran berhasil!")
                    print(format_struk(transaksi.cetak_struk()))
                    break

            elif pilih == "0":
                break

            else:
                print("Pilihan tidak valid.")

    def tampilkan_riwayat(self):
        self.__riwayat.muat_dari_json()
        self.__riwayat.tampilkan()

    # ---------- Database JSON ----------
    def simpan_database_json(self, filename: str = DEFAULT_DB_PATH):
        data = [produk.to_dict() for produk in self.__daftar_produk]
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def muat_database_json(self, filename: str = DEFAULT_DB_PATH):
        """Memuat data JSON menjadi objek Produk kembali menggunakan ProdukFactory."""
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            print(f"Database tidak ditemukan di {filename}, mulai dari kosong.")
            self.__daftar_produk = []
            return
        self.__daftar_produk = []
        for d in data:
            try:
                p = ProdukFactory.buat_dari_dict(d)
                self.__daftar_produk.append(p)
            except ValueError:
                continue
