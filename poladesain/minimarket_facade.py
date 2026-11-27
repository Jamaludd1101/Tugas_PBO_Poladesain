"""Modul Facade Pattern (MinimarketFacade) & fungsi pengujian batch checkout."""

from __future__ import annotations

import sys
from typing import Any

# Pilih jalur import sesuai konteks eksekusi (package vs skrip langsung)
if __package__:
    from .database_manager import DatabaseManager
    from .factory import ProdukCreator
    from .pembeli import Pembeli, Voucher
    from .produk import Produk
    from .strategy import DiskonStrategy
    from .toko import Toko, Transaksi
else:
    from database_manager import DatabaseManager
    from factory import ProdukCreator
    from pembeli import Pembeli, Voucher
    from produk import Produk
    from strategy import DiskonStrategy
    from toko import Toko, Transaksi


class MinimarketFacade:
    """Single entry point yang menyatukan operasi katalog, diskon, & transaksi."""

    def __init__(self, nama_toko: str = "LokaMart") -> None:
        self._db = DatabaseManager.get_instance()
        self._toko = Toko(nama_toko, db_manager=self._db)
        self._toko.muat_database_json()

    @property
    def toko(self) -> Toko:
        return self._toko

    @property
    def db_manager(self) -> DatabaseManager:
        return self._db

    def muat_ulang_data(self) -> None:
        """Memuat ulang data produk dan riwayat dari penyimpanan JSON."""
        self._toko.muat_database_json(force_reload=True)
        self._toko.riwayat.muat_dari_json()

    def ambil_semua_produk(self) -> list[dict[str, Any]]:
        """Mengembalikan daftar seluruh produk beserta atribut frontend."""
        hasil: list[dict[str, Any]] = []
        for produk in self._toko.daftar_produk:
            item = produk.to_dict()
            item["id_produk"] = produk.nama
            item["harga_akhir"] = produk.harga_akhir()
            hasil.append(item)
        return hasil

    def cari_produk(self, kode_atau_nama: str) -> Produk | None:
        """Mencari produk berdasarkan nama atau kode/indeks item."""
        if not kode_atau_nama:
            return None

        # 1. Pencarian langsung berdasarkan nama produk (skema utama)
        produk = self._toko.cari_produk(kode_atau_nama)
        if produk is not None:
            return produk

        # 2. Fallback kode indeks seperti "PRD-001" atau "1"
        bersih = kode_atau_nama.strip().upper()
        bersih = bersih.removeprefix("PRD-")
        if bersih.isdigit():
            indeks = int(bersih) - 1
            if 0 <= indeks < len(self._toko.daftar_produk):
                return self._toko.daftar_produk[indeks]
        return None

    def tambah_produk(
        self,
        kategori: str,
        nama: str,
        harga: int | str,
        stok: int | str,
        extra: Any,
    ) -> dict[str, Any]:
        """Menambahkan produk baru via ProdukCreator dan menyimpannya ke JSON."""
        nama_bersih = str(nama).strip()
        try:
            harga_int = int(harga)
            stok_int = int(stok)
        except (TypeError, ValueError):
            return {
                "status": "gagal",
                "pesan": "Harga dan Stok harus angka.",
            }

        if not nama_bersih or harga_int <= 0 or stok_int < 0:
            return {
                "status": "gagal",
                "pesan": "Data tidak lengkap/valid.",
            }

        if self._toko.cari_produk(nama_bersih) is not None:
            return {
                "status": "gagal",
                "pesan": "Produk dengan nama tersebut sudah ada.",
            }

        try:
            produk_baru = ProdukCreator.buat_produk(
                kategori=str(kategori),
                nama=nama_bersih,
                harga=harga_int,
                stok=stok_int,
                extra=extra,
            )
        except ValueError:
            return {
                "status": "gagal",
                "pesan": "Kategori tidak dikenal.",
            }

        self._toko.tambah_produk(produk_baru)
        self._toko.simpan_database_json()
        return {
            "status": "sukses",
            "pesan": f"Produk {nama_bersih} berhasil ditambahkan!",
            "produk": produk_baru.to_dict(),
        }

    def ubah_strategi_diskon_kategori(
        self, kategori: str, strategy: DiskonStrategy
    ) -> int:
        """Mengganti strategi diskon seluruh produk pada kategori saat runtime."""
        target = kategori.strip().lower()
        jumlah_diubah = 0
        for produk in self._toko.daftar_produk:
            if produk.__class__.__name__.lower() == target:
                produk.set_diskon_strategy(strategy)
                jumlah_diubah += 1
        return jumlah_diubah

    def daftarkan_voucher(self, voucher: Voucher) -> None:
        """Menambahkan atau mengganti strategi voucher aktif di toko."""
        self._toko.tambah_voucher(voucher)

    def proses_checkout(
        self,
        nama_pembeli: str,
        items: list[dict[str, Any]],
        kode_voucher: str | None = None,
        saldo_awal: int | None = None,
        pembeli: Pembeli | None = None,
        simpan_ke_disk: bool = True,
        verbose: bool = False,
    ) -> dict[str, Any]:
        """Menjalankan alur checkout lengkap secara atomik melalui Facade."""
        if not items:
            return {
                "status": "gagal",
                "pesan": "Keranjang belanja tidak boleh kosong.",
            }

        # Tahap 1: Validasi seluruh item & agregasi kuantitas sebelum mutasi
        rencana_item: list[tuple[Produk, int]] = []
        total_diminta: dict[str, int] = {}

        for entry in items:
            kode_item = str(entry.get("kode") or entry.get("id_produk") or "").strip()
            try:
                qty = int(entry.get("qty", entry.get("jumlah", 0)))
            except (TypeError, ValueError):
                return {
                    "status": "gagal",
                    "pesan": f"Kuantitas item '{kode_item}' tidak valid.",
                }

            if qty <= 0:
                return {
                    "status": "gagal",
                    "pesan": f"Kuantitas '{kode_item}' harus lebih dari 0.",
                }

            produk = self.cari_produk(kode_item)
            if produk is None:
                return {
                    "status": "gagal",
                    "pesan": f"Produk '{kode_item}' tidak ditemukan.",
                }

            akumulasi = total_diminta.get(produk.nama, 0) + qty
            if not produk.cek_stok(akumulasi):
                return {
                    "status": "gagal",
                    "pesan": (
                        f"Stok {produk.nama} tidak mencukupi "
                        f"(diminta: {akumulasi}, tersedia: {produk.stok})."
                    ),
                }

            total_diminta[produk.nama] = akumulasi
            rencana_item.append((produk, qty))

        # Tahap 2: Siapkan konteks Pembeli & Voucher (Strategy Pattern)
        if pembeli is None:
            saldo_efektif = sys.maxsize if saldo_awal is None else saldo_awal
            pembeli_aktif = Pembeli(nama_pembeli.strip() or "Pelanggan", saldo_efektif)
        else:
            pembeli_aktif = pembeli
            pembeli_aktif.keranjang.kosongkan()

        for produk, qty in rencana_item:
            pembeli_aktif.tambah_ke_keranjang(produk, qty, verbose=verbose)

        voucher_obj = self._toko.ambil_voucher(kode_voucher)
        transaksi = Transaksi(pembeli_aktif, voucher=voucher_obj)

        # Tahap 3: Eksekusi pembayaran atomik & catat ke riwayat
        if not transaksi.bayar(verbose=verbose):
            pembeli_aktif.keranjang.kosongkan()
            return {
                "status": "gagal",
                "pesan": "Transaksi gagal: saldo atau stok tidak mencukupi.",
            }

        struk = transaksi.cetak_struk()
        self._toko.riwayat.tambah_riwayat(transaksi)

        if simpan_ke_disk:
            self.simpan_perubahan()

        return {
            "status": "sukses",
            "pesan": "Transaksi berhasil diproses.",
            "struk": struk,
            "sisa_saldo": pembeli_aktif.saldo,
        }

    def simpan_perubahan(self) -> None:
        """Menyinkronkan stok produk dan riwayat ke JSON via Singleton."""
        self._toko.simpan_database_json()
        self._toko.riwayat.simpan_ke_json()

    def ambil_riwayat(self) -> list[dict[str, Any]]:
        """Mengembalikan seluruh riwayat transaksi yang tercatat."""
        return list(self._toko.riwayat.daftar)


def simulasi_batch_checkout(
    daftar_order: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Mengeksekusi batch order via MinimarketFacade tanpa server HTTP.

    Format input:
        [{"nama_pembeli": str, "items": [{"kode": str, "qty": int}], "voucher": str}]
    """
    facade = MinimarketFacade("LokaMart")
    hasil_batch: list[dict[str, Any]] = []

    for order in daftar_order:
        nama_pembeli = str(order.get("nama_pembeli", "Pembeli Batch"))
        items = order.get("items", [])
        voucher = order.get("voucher")
        saldo_opsional = order.get("saldo")

        hasil = facade.proses_checkout(
            nama_pembeli=nama_pembeli,
            items=items,
            kode_voucher=voucher,
            saldo_awal=saldo_opsional,
            simpan_ke_disk=False,
            verbose=False,
        )
        hasil_batch.append(hasil)

    # Flush satu kali di akhir batch agar I/O disk efisien dan memori terjaga
    facade.simpan_perubahan()
    return hasil_batch
