import os

from flask import Flask, jsonify, render_template, request
from pembeli import Pembeli
from produk import ProdukFactory
from toko import Toko, TransaksiBuilder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = (
    os.path.join(BASE_DIR, "templates")
    if os.path.exists(os.path.join(BASE_DIR, "templates", "index.html"))
    else BASE_DIR
)

app = Flask(__name__, template_folder=TEMPLATE_DIR)

# Mengambil satu-satunya instance Toko (Singleton Pattern)
toko = Toko.get_instance("Minimarket OOP")
toko.muat_database_json()

# State sesi aktif berbasis objek OOP Python (Pembeli & Voucher)
pembeli_aktif = None
voucher_aktif = None


def bangun_ringkasan_sesi() -> dict:
    """Menyusun status pembeli, keranjang, dan perhitungan via TransaksiBuilder."""
    if pembeli_aktif is None:
        return {
            "pembeli": None,
            "keranjang": [],
            "voucher": None,
            "subtotal": 0,
            "potongan": 0,
            "total": 0,
        }

    # Gunakan TransaksiBuilder untuk menghitung pratinjau subtotal, potongan, & total
    transaksi_preview = (
        TransaksiBuilder().set_pembeli(pembeli_aktif).set_voucher(voucher_aktif).build()
    )
    struk_preview = transaksi_preview.cetak_struk()

    items_keranjang = []
    for barang in pembeli_aktif.keranjang.get_items():
        prod = barang["produk"]
        qty = barang["jumlah"]
        items_keranjang.append(
            {
                "nama": prod.nama,
                "kategori": prod.__class__.__name__,
                "jumlah": qty,
                "harga": prod.harga_akhir(),
                "subtotal": prod.harga_akhir() * qty,
            }
        )

    return {
        "pembeli": {
            "nama": pembeli_aktif.nama,
            "saldo": pembeli_aktif.saldo,
        },
        "keranjang": items_keranjang,
        "voucher": voucher_aktif.kode if voucher_aktif else None,
        "subtotal": struk_preview["subtotal"],
        "potongan": struk_preview["potongan"],
        "total": struk_preview["total_bayar"],
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/state", methods=["GET"])
def get_state():
    toko.muat_database_json()
    return jsonify(bangun_ringkasan_sesi())


@app.route("/api/login", methods=["POST"])
def login_pembeli():
    global pembeli_aktif, voucher_aktif
    data = request.json or {}
    nama = data.get("nama", "").strip()
    try:
        saldo = int(data.get("saldo", -1))
    except (ValueError, TypeError):
        return jsonify({"status": "gagal", "pesan": "Saldo harus berupa angka."})

    if not nama:
        return jsonify({"status": "gagal", "pesan": "Nama pembeli harus diisi."})
    if saldo < 0:
        return jsonify({"status": "gagal", "pesan": "Saldo tidak boleh negatif."})

    # Membuat objek Pembeli OOP
    pembeli_aktif = Pembeli(nama, saldo)
    voucher_aktif = None
    return jsonify(
        {
            "status": "sukses",
            "pesan": f"Selamat datang, {pembeli_aktif.nama}!",
            "state": bangun_ringkasan_sesi(),
        }
    )


@app.route("/api/logout", methods=["POST"])
def logout_pembeli():
    global pembeli_aktif, voucher_aktif
    pembeli_aktif = None
    voucher_aktif = None
    return jsonify({"status": "sukses", "state": bangun_ringkasan_sesi()})


@app.route("/api/produk", methods=["GET"])
def get_produk():
    toko.muat_database_json()
    data_produk = []
    for produk in toko.daftar_produk:
        item = produk.to_dict()
        item["id_produk"] = produk.nama
        # Gunakan Polymorphism harga_akhir() & hitung_diskon() langsung dari Python
        item["harga_akhir"] = produk.harga_akhir()
        item["diskon_nominal"] = produk.hitung_diskon()
        data_produk.append(item)
    return jsonify(data_produk)


@app.route("/api/keranjang/tambah", methods=["POST"])
def keranjang_tambah():
    if pembeli_aktif is None:
        return jsonify(
            {"status": "butuh_login", "pesan": "Silakan isi data pembeli dulu."}
        )

    toko.muat_database_json()
    data = request.json or {}
    nama_produk = data.get("nama", "")
    try:
        jumlah = int(data.get("jumlah", 1))
    except (ValueError, TypeError):
        jumlah = 0

    produk = toko.cari_produk(nama_produk)
    if not produk:
        return jsonify({"status": "gagal", "pesan": "Produk tidak ditemukan."})

    if jumlah <= 0 or not produk.cek_stok(jumlah):
        return jsonify(
            {
                "status": "gagal",
                "pesan": f"Stok {produk.nama} tidak mencukupi (Sisa: {produk.stok}).",
            }
        )

    # Cek total jumlah jika produk sudah ada di keranjang
    for barang in pembeli_aktif.keranjang.get_items():
        if barang["produk"].nama == produk.nama:
            if not produk.cek_stok(barang["jumlah"] + jumlah):
                return jsonify(
                    {
                        "status": "gagal",
                        "pesan": f"Jumlah melebihi stok maksimum ({produk.stok}).",
                    }
                )
            break

    berhasil = pembeli_aktif.tambah_ke_keranjang(produk, jumlah)
    if not berhasil:
        return jsonify({"status": "gagal", "pesan": "Gagal menambahkan ke keranjang."})

    return jsonify(
        {
            "status": "sukses",
            "pesan": f"{produk.nama} berhasil masuk ke keranjang.",
            "state": bangun_ringkasan_sesi(),
        }
    )


@app.route("/api/keranjang/hapus", methods=["POST"])
def keranjang_hapus():
    if pembeli_aktif is None:
        return jsonify(
            {"status": "butuh_login", "pesan": "Silakan isi data pembeli dulu."}
        )

    data = request.json or {}
    nama_produk = data.get("nama", "")
    produk = toko.cari_produk(nama_produk)

    if produk and pembeli_aktif.keranjang.hapus(produk):
        return jsonify(
            {
                "status": "sukses",
                "pesan": f"{nama_produk} dihapus dari keranjang.",
                "state": bangun_ringkasan_sesi(),
            }
        )

    # Fallback jika produk terhapus dari katalog saat masih di keranjang
    for barang in list(pembeli_aktif.keranjang.get_items()):
        if barang["produk"].nama.lower() == nama_produk.strip().lower():
            pembeli_aktif.keranjang.hapus(barang["produk"])
            break

    return jsonify(
        {
            "status": "sukses",
            "pesan": f"{nama_produk} dihapus dari keranjang.",
            "state": bangun_ringkasan_sesi(),
        }
    )


@app.route("/api/voucher", methods=["POST"])
def terapkan_voucher():
    global voucher_aktif
    if pembeli_aktif is None:
        return jsonify(
            {"status": "butuh_login", "pesan": "Silakan isi data pembeli dulu."}
        )

    data = request.json or {}
    kode = data.get("kode", "").strip().upper()
    voucher = toko.cari_voucher(kode)

    if not voucher:
        return jsonify({"status": "gagal", "pesan": "Kode voucher tidak valid."})

    subtotal = pembeli_aktif.keranjang.total_harga()
    if not voucher.berlaku(subtotal):
        return jsonify(
            {
                "status": "gagal",
                "pesan": f"Voucher {voucher.kode} membutuhkan minimal belanja Rp{voucher.potongan:,}.".replace(
                    ",", "."
                ),
            }
        )

    voucher_aktif = voucher
    return jsonify(
        {
            "status": "sukses",
            "pesan": f"Voucher {voucher.kode} berhasil diterapkan!",
            "state": bangun_ringkasan_sesi(),
        }
    )


@app.route("/api/checkout", methods=["POST"])
def checkout():
    global voucher_aktif
    if pembeli_aktif is None:
        return jsonify(
            {"status": "butuh_login", "pesan": "Silakan isi data pembeli dulu."}
        )

    if not pembeli_aktif.keranjang.get_items():
        return jsonify({"status": "gagal", "pesan": "Keranjang masih kosong."})

    # Sinkronkan referensi produk terbaru dengan database_toko.json sebelum bayar
    toko.muat_database_json()
    for barang in pembeli_aktif.keranjang.get_items():
        produk_terbaru = toko.cari_produk(barang["produk"].nama)
        if not produk_terbaru or not produk_terbaru.cek_stok(barang["jumlah"]):
            return jsonify(
                {
                    "status": "gagal",
                    "pesan": f"Stok {barang['produk'].nama} tidak mencukupi.",
                }
            )
        barang["produk"] = produk_terbaru

    # Membangun objek Transaksi menggunakan Builder Pattern (TransaksiBuilder)
    transaksi = (
        TransaksiBuilder().set_pembeli(pembeli_aktif).set_voucher(voucher_aktif).build()
    )

    if not transaksi.cek_saldo():
        return jsonify(
            {"status": "gagal", "pesan": "Saldo tidak cukup untuk pembayaran."}
        )

    if not transaksi.bayar():
        return jsonify(
            {"status": "gagal", "pesan": "Gagal memproses transaksi pembayaran."}
        )

    # Simpan struk ke riwayat.json dan stok terbaru ke database_toko.json
    toko.catat_transaksi(transaksi)
    struk_final = transaksi.cetak_struk()
    voucher_aktif = None

    return jsonify(
        {
            "status": "sukses",
            "pesan": "Pembayaran berhasil diproses!",
            "struk": struk_final,
            "state": bangun_ringkasan_sesi(),
        }
    )


@app.route("/api/riwayat", methods=["GET"])
def get_riwayat():
    return jsonify(toko.get_daftar_riwayat())


@app.route("/api/tambah_produk", methods=["POST"])
def tambah_produk():
    toko.muat_database_json()
    data = request.json or {}
    kategori = data.get("kategori", "")
    nama = data.get("nama", "").strip()

    try:
        harga = int(data.get("harga", 0))
        stok = int(data.get("stok", 0))
    except (ValueError, TypeError):
        return jsonify({"status": "gagal", "pesan": "Harga dan Stok harus angka."})

    if not nama or harga <= 0 or stok < 0:
        return jsonify({"status": "gagal", "pesan": "Data tidak lengkap/valid."})

    if toko.cari_produk(nama):
        return jsonify(
            {"status": "gagal", "pesan": "Produk dengan nama tersebut sudah ada."}
        )

    # Membuat object produk secara terpusat via Simple Factory (ProdukFactory)
    try:
        p = ProdukFactory.buat_produk(
            kategori, nama, harga, stok, data.get("extra", "")
        )
    except ValueError as err:
        return jsonify({"status": "gagal", "pesan": str(err)})

    toko.tambah_produk(p)
    toko.simpan_database_json()

    return jsonify(
        {"status": "sukses", "pesan": f"Produk {nama} berhasil ditambahkan!"}
    )


@app.route("/api/duplikat_produk", methods=["POST"])
def duplikat_produk():
    """Endpoint untuk menduplikasi produk menggunakan Prototype Pattern (.clone())."""
    toko.muat_database_json()
    data = request.json or {}
    nama_asal = data.get("nama_asal", "").strip()
    nama_baru = data.get("nama_baru", "").strip()

    produk_asal = toko.cari_produk(nama_asal)
    if not produk_asal:
        return jsonify({"status": "gagal", "pesan": "Produk asal tidak ditemukan."})

    if not nama_baru:
        nama_baru = f"{produk_asal.nama} (Promo)"

    if toko.cari_produk(nama_baru):
        return jsonify(
            {"status": "gagal", "pesan": "Produk dengan nama baru sudah ada."}
        )

    try:
        harga_baru = (
            int(data["harga_baru"])
            if data.get("harga_baru") not in (None, "")
            else None
        )
        stok_baru = (
            int(data["stok_baru"]) if data.get("stok_baru") not in (None, "") else None
        )
        # Menggunakan Prototype Pattern (.clone())
        produk_clone = produk_asal.clone(
            nama_baru=nama_baru, harga_baru=harga_baru, stok_baru=stok_baru
        )
    except ValueError as err:
        return jsonify({"status": "gagal", "pesan": str(err)})

    toko.tambah_produk(produk_clone)
    toko.simpan_database_json()

    return jsonify(
        {
            "status": "sukses",
            "pesan": f"Produk berhasil diduplikasi menjadi {produk_clone.nama}!",
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
