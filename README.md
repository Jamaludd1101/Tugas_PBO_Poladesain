# 🛒 LokaMart-DPF: Evaluasi Arsitektur Sistem Informasi Minimarket

Repositori ini berisi implementasi dan pengujian komparatif tiga paradigma arsitektur perangkat lunak pada Sistem Informasi Minimarket berbasis Python (Flask Web & CLI) dengan serialisasi JSON:

1. **`tanpa_oop/`** — Pendekatan prosedural murni menggunakan fungsi dan struktur data dasar (`dict`/`list`) tanpa `class` maupun UML.
2. **`Implementasi-UML/`** — Pendekatan *Object-Oriented Programming* (OOP) konvensional berdasarkan rancangan UML tanpa *Design Pattern*.
3. **`poladesain/` (LokaMart-DPF)** — Arsitektur *multilayer* yang mengimplementasikan empat pola desain: **Singleton** (`DatabaseManager`), **Facade** (`MinimarketFacade`), **Factory Method** (`ProdukCreator`), dan **Strategy** (`DiskonStrategy`).

---

## 📁 Struktur Direktori

| Folder / File | Keterangan |
| :--- | :--- |
| `tanpa_oop/` | Kode sumber versi prosedural (Baseline 1) |
| `Implementasi-UML/` | Kode sumber versi OOP + UML standar (Baseline 2) |
| `poladesain/` | Kode sumber versi *Design Patterns* / LokaMart-DPF (Proposed) |
| `benchmark/` | Skrip pengujian memori (`tracemalloc`), latensi, dan kompleksitas kode |
| `docs/` | Diagram arsitektur (DFD Level 0, UML Class, Swimlane) & naskah paper IEEE |
| `requirements.txt` | Daftar dependensi Python |

---

## ⚙️ Instalasi & Cara Menjalankan

Pastikan **Python 3.10+** sudah terinstal, lalu pasang dependensi:

```bash
pip install -r requirements.txt
