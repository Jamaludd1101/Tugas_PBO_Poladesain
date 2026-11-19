# 🛒 Sistem Manajemen Minimarket — Komparasi Design Patterns (OOP Python)

Repositori ini berisi implementasi **Object-Oriented Programming (OOP)** dan **Gang of Four (GoF) Design Patterns** dalam bahasa Python dengan studi kasus **Sistem Manajemen Minimarket (LokaMart)**. Proyek ini mendukung dua mode antarmuka (**CLI Terminal** dan **Web Flask**) yang terintegrasi penuh dengan penyimpanan berbasis **JSON** (`database_toko.json` dan `riwayat.json`).

Setiap kategori pola desain dipisahkan ke dalam direktori tersendiri agar memudahkan komparasi arsitektur, pengujian mandiri, dan penyusunan laporan kelompok.

---

## 📁 Struktur Direktori Repositori

```text
minimarket-design-patterns/
├── README.md
├── creational/                 # Implementasi Creational Design Patterns
│   ├── produk.py               # Produk (ABC), Makanan, Mainan, Minuman, ProdukFactory, .clone()
│   ├── pembeli.py              # Voucher, Keranjang, Pembeli
│   ├── toko.py                 # Toko (Singleton), TransaksiBuilder, Transaksi, RiwayatTransaksi
│   ├── main.py                 # Entry point aplikasi mode CLI (Terminal)
│   ├── app.py                  # Entry point aplikasi mode Web API (Flask)
│   ├── database_toko.json      # Database inventaris produk
│   ├── riwayat.json            # Database riwayat struk transaksi
│   └── templates/
│       └── index.html          # Antarmuka Web LokaMart
├── structural/                 # Implementasi Structural Design Patterns
│   └── ...                     # (Isi file kode bagian Structural Patterns)
└── behavioral/                 # Implementasi Behavioral Design Patterns
    └── ...                     # (Isi file kode bagian Behavioral Patterns)
