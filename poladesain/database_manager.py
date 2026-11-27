"""Modul pengelola persistensi JSON tunggal menggunakan Singleton Pattern."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Union

# Alias tipe yang kompatibel dengan Python 3.9 maupun Python 3.10+
PathLikeStr = Union[str, Path]


class DatabaseManager:
    """Singleton pengelola baca/tulis database_toko.json dan riwayat.json."""

    _instance: DatabaseManager | None = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> DatabaseManager:
        # Double-checked locking agar thread-safe sekaligus menjamin 1 instance
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._inisialisasi()
                    cls._instance = instance
        return cls._instance

    def _inisialisasi(self) -> None:
        """Inisialisasi path default dan cache memori internal."""
        base_dir = Path(__file__).resolve().parent
        self._path_produk: Path = base_dir / "database_toko.json"
        self._path_riwayat: Path = base_dir / "riwayat.json"
        self._cache_produk: list[dict[str, Any]] | None = None
        self._cache_riwayat: list[dict[str, Any]] | None = None

    @classmethod
    def get_instance(cls) -> DatabaseManager:
        """Mengembalikan satu-satunya instance DatabaseManager."""
        return cls()

    def atur_path(
        self,
        path_produk: PathLikeStr | None = None,
        path_riwayat: PathLikeStr | None = None,
    ) -> None:
        """Mengubah lokasi file JSON dan mereset cache memori."""
        with self._lock:
            if path_produk is not None:
                self._path_produk = Path(path_produk)
                self._cache_produk = None
            if path_riwayat is not None:
                self._path_riwayat = Path(path_riwayat)
                self._cache_riwayat = None

    def _resolve_path(self, filename: PathLikeStr | None, default_path: Path) -> Path:
        """Menentukan path file tujuan tanpa duplikasi logika."""
        if filename is None:
            return default_path
        path_obj = Path(filename)
        if path_obj.is_absolute() or path_obj.exists():
            return path_obj
        return default_path.parent / path_obj

    def _baca_json(self, target_path: Path) -> list[dict[str, Any]]:
        """Membaca file JSON dari disk; mengembalikan list kosong jika belum ada."""
        if not target_path.exists():
            return []
        with target_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []

    def _tulis_json(self, target_path: Path, data: list[dict[str, Any]]) -> None:
        """Menulis data list dictionary ke file JSON dengan format rapi."""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with target_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def muat_database_toko(
        self,
        filename: PathLikeStr | None = None,
        force_reload: bool = False,
    ) -> list[dict[str, Any]]:
        """Memuat data produk dari database_toko.json dengan efisiensi cache."""
        with self._lock:
            target = self._resolve_path(filename, self._path_produk)
            if filename is None and self._cache_produk is not None and not force_reload:
                return self._cache_produk

            data = self._baca_json(target)
            if filename is None:
                self._cache_produk = data
            return data

    def simpan_database_toko(
        self,
        data: list[dict[str, Any]],
        filename: PathLikeStr | None = None,
    ) -> None:
        """Menyimpan daftar produk ke database_toko.json secara terkontrol."""
        with self._lock:
            target = self._resolve_path(filename, self._path_produk)
            self._tulis_json(target, data)
            if filename is None:
                self._cache_produk = data

    def muat_riwayat(
        self,
        filename: PathLikeStr | None = None,
        force_reload: bool = False,
    ) -> list[dict[str, Any]]:
        """Memuat data riwayat transaksi dari riwayat.json."""
        with self._lock:
            target = self._resolve_path(filename, self._path_riwayat)
            if (
                filename is None
                and self._cache_riwayat is not None
                and not force_reload
            ):
                return self._cache_riwayat

            data = self._baca_json(target)
            if filename is None:
                self._cache_riwayat = data
            return data

    def simpan_riwayat(
        self,
        data: list[dict[str, Any]],
        filename: PathLikeStr | None = None,
    ) -> None:
        """Menyimpan daftar struk transaksi ke riwayat.json."""
        with self._lock:
            target = self._resolve_path(filename, self._path_riwayat)
            self._tulis_json(target, data)
            if filename is None:
                self._cache_riwayat = data
