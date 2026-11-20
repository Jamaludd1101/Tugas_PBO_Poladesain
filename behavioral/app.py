from datetime import datetime
from flask import Flask, jsonify, render_template, request

from behavioral_patterns import (
    KonteksVoucher,
    TanpaDiskon,
    VoucherNominal,
    VoucherPersen,
)
from produk import Mainan, Makanan, Minuman
from toko import Toko

app = Flask(__name__)

toko = Toko("Minimarket OOP")
toko.muat_database_json("database_toko.json")

VOUCHER_STRATEGI = {
    "HEMAT5K": VoucherNominal(5000),
    "HEMAT10": VoucherPersen(10, maks_potongan=15000),
    "HEMAT20K": VoucherNominal(20000, min_belanja=50000),
}

SESSIONS = {}
DEFAULT_KEY = "_guest"


def _get_session(key: str = DEFAULT_KEY) -> dict:
    if key not in SESSIONS:
        SESSIONS[key] = {
            "pembeli": None,
            "keranjang": [],
            "voucher": None,
            "konteks": KonteksVoucher(TanpaDiskon()),
        }
    return SESSIONS[key]


def _hitung_dari_keranjang(raw_keranjang: list, kode_voucher: str | None) -> dict:
    items_view = []
    subtotal = 0

    for item in raw_keranjang or []:
        nama_atau_id = (item.get("nama") or item.get("id_produk") or "").strip()
        produk = toko.cari_produk(nama_atau_id)
        if not produk:
            continue
        try:
            jumlah = int(item.get("jumlah", 0))
        except (ValueError, TypeError):
            jumlah = 0
        if jumlah <= 0 or produk.stok <= 0:
            continue

        qty_valid = min(jumlah, produk.stok)
        harga = produk.harga_akhir()
        sub = harga * qty_valid
        subtotal += sub
        items_view.append(
            {
                "id_produk": produk.nama,
                "nama": produk.nama,
                "kategori": produk.__class__.__name__,
                "jumlah": qty_valid,
                "harga": harga,
                "subtotal": sub,
            }
        )

    kode = (kode_voucher or "").strip().upper() or None
    strategi = VOUCHER_STRATEGI.get(kode) if kode else None
    konteks = KonteksVoucher(strategi or TanpaDiskon())
    total = konteks.terapkan(subtotal) if subtotal > 0 else 0
    potongan = max(0, subtotal - total)

    return {
        "keranjang": items_view,
        "voucher": kode if strategi else None,
        "subtotal": subtotal,
        "potongan": potongan,
        "total": total,
    }


def _hitung_state(sess: dict) -> dict:
    ringkasan = _hitung_dari_keranjang(sess["keranjang"], sess.get("voucher"))
    return {
        "pembeli": sess["pembeli"],
        **ringkasan,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/produk", methods=["GET"])
def get_produk():
    data_produk = []
    for produk in toko.daftar_produk:
        item = produk.to_dict()
        item["id_produk"] = produk.nama
        item["harga_akhir"] = produk.harga_akhir()
        data_produk.append(item)
    return jsonify(data_produk)


@app.route("/api/riwayat", methods=["GET"])
def get_riwayat():
    return jsonify(toko.riwayat.daftar)


@app.route("/api/state", methods=["GET"])
def get_state():
    sess = _get_session()
    return jsonify(_hitung_state(sess))


@app.route("/api/login", methods=["POST"])
def login():
    data = request.json or {}
    nama = (data.get("nama") or "").strip()
    try:
        saldo = int(data.get("saldo", 0))
    except (ValueError, TypeError):
        return jsonify({"status": "gagal", "pesan": "Saldo harus berupa angka."})

    if not nama:
        return jsonify({"status": "gagal", "pesan": "Nama pembeli harus diisi."})
    if saldo < 0:
        return jsonify({"status": "gagal", "pesan": "Saldo tidak boleh negatif."})

    sess = _get_session()
    sess["pembeli"] = {"nama": nama, "saldo": saldo}
    return jsonify(
        {
            "status": "sukses",
            "pesan": f"Selamat datang, {nama}!",
            "state": _hitung_state(sess),
        }
    )


@app.route("/api/logout", methods=["POST"])
def logout():
    sess = _get_session()
    sess["pembeli"] = None
    sess["keranjang"] = []
    sess["voucher"] = None
    sess["konteks"].set_strategi(TanpaDiskon())
    return jsonify({"status": "sukses", "state": _hitung_state(sess)})


@app.route("/api/keranjang/tambah", methods=["POST"])
def tambah_keranjang():
    sess = _get_session()
    data = request.json or {}
    nama = (data.get("nama") or "").strip()
    try:
        jumlah = int(data.get("jumlah", 1))
    except (ValueError, TypeError):
        jumlah = 0

    produk = toko.cari_produk(nama)
    if not produk:
        return jsonify({"status": "gagal", "pesan": "Produk tidak ditemukan."})
    if jumlah <= 0:
        return jsonify({"status": "gagal", "pesan": "Jumlah harus lebih dari 0."})

    existing = next((i for i in sess["keranjang"] if i["nama"] == produk.nama), None)
    total_qty = jumlah + (existing["jumlah"] if existing else 0)
    if total_qty > produk.stok:
        return jsonify(
            {"status": "gagal", "pesan": f"Stok {produk.nama} tidak mencukupi."}
        )

    if existing:
        existing["jumlah"] = total_qty
    else:
        sess["keranjang"].append({"nama": produk.nama, "jumlah": jumlah})

    return jsonify(
        {
            "status": "sukses",
            "pesan": f"{produk.nama} ditambahkan ke keranjang.",
            "state": _hitung_state(sess),
        }
    )


@app.route("/api/keranjang/hapus", methods=["POST"])
def hapus_keranjang():
    sess = _get_session()
    data = request.json or {}
    nama = (data.get("nama") or "").strip()

    sess["keranjang"] = [
        i for i in sess["keranjang"] if i["nama"].lower() != nama.lower()
    ]
    return jsonify(
        {
            "status": "sukses",
            "pesan": "Item dihapus dari keranjang.",
            "state": _hitung_state(sess),
        }
    )


@app.route("/api/voucher", methods=["POST"])
def pakai_voucher():
    sess = _get_session()
    data = request.json or {}
    kode = (data.get("kode") or data.get("kode_voucher") or "").strip().upper()
    keranjang_req = data.get("keranjang")

    if isinstance(keranjang_req, list):
        sess["keranjang"] = [
            {
                "nama": (i.get("nama") or i.get("id_produk") or "").strip(),
                "jumlah": int(i.get("jumlah", 0)),
            }
            for i in keranjang_req
        ]

    ringkasan = _hitung_dari_keranjang(sess["keranjang"], kode)

    if not kode:
        sess["voucher"] = None
        sess["konteks"].set_strategi(TanpaDiskon())
        return jsonify(
            {
                "status": "sukses",
                "voucher": None,
                "potongan": 0,
                "total": ringkasan["subtotal"],
                "pesan": "Voucher dihapus.",
                "state": _hitung_state(sess),
            }
        )

    strategi = VOUCHER_STRATEGI.get(kode)
    if not strategi:
        return jsonify(
            {
                "status": "gagal",
                "voucher": None,
                "potongan": 0,
                "total": ringkasan["subtotal"],
                "pesan": "Kode voucher tidak ditemukan.",
            }
        )

    sess["voucher"] = kode
    sess["konteks"].set_strategi(strategi)
    ringkasan = _hitung_dari_keranjang(sess["keranjang"], kode)

    pesan = f"Voucher {kode} aktif."
    if ringkasan["subtotal"] > 0 and ringkasan["potongan"] == 0:
        pesan = f"Voucher {kode} terpasang, namun syarat minimum belanja belum terpenuhi."

    return jsonify(
        {
            "status": "sukses",
            "voucher": kode,
            "potongan": ringkasan["potongan"],
            "total": ringkasan["total"],
            "pesan": pesan,
            "state": _hitung_state(sess),
        }
    )


@app.route("/api/checkout", methods=["POST"])
def checkout():
    sess = _get_session()
    data = request.json or {}

    keranjang_req = data.get("keranjang")
    if isinstance(keranjang_req, list) and keranjang_req:
        sess["keranjang"] = [
            {
                "nama": (i.get("nama") or i.get("id_produk") or "").strip(),
                "jumlah": int(i.get("jumlah", 0)),
            }
            for i in keranjang_req
        ]

    kode_voucher = data.get("kode_voucher") or data.get("kode") or sess.get("voucher")
    ringkasan = _hitung_dari_keranjang(sess["keranjang"], kode_voucher)

    if not ringkasan["keranjang"]:
        return jsonify({"status": "gagal", "pesan": "Keranjang masih kosong."})

    for item in ringkasan["keranjang"]:
        produk = toko.cari_produk(item["nama"])
        if not produk or not produk.cek_stok(item["jumlah"]):
            return jsonify(
                {"status": "gagal", "pesan": f"Stok {item['nama']} tidak cukup."}
            )

    for item in ringkasan["keranjang"]:
        produk = toko.cari_produk(item["nama"])
        produk.kurangi_stok(item["jumlah"])

    nama_pembeli = (
        (data.get("nama_pembeli") or "")
        or ((sess.get("pembeli") or {}).get("nama") or "Pembeli")
    ).strip()

    struk = {
        "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pembeli": nama_pembeli,
        "voucher": ringkasan["voucher"],
        "items": [
            {
                "nama": i["nama"],
                "qty": i["jumlah"],
                "harga_satuan": i["harga"],
                "subtotal": i["subtotal"],
            }
            for i in ringkasan["keranjang"]
        ],
        "subtotal": ringkasan["subtotal"],
        "potongan": ringkasan["potongan"],
        "total_bayar": ringkasan["total"],
    }

    toko.riwayat.tambah_struk_dict(struk)
    toko.riwayat.simpan_ke_json("riwayat.json")
    toko.simpan_database_json("database_toko.json")

    sess["keranjang"] = []
    sess["voucher"] = None
    sess["konteks"].set_strategi(TanpaDiskon())

    return jsonify(
        {
            "status": "sukses",
            "pesan": "Pembayaran berhasil!",
            "struk": struk,
            "state": _hitung_state(sess),
        }
    )


@app.route("/api/tambah_produk", methods=["POST"])
def tambah_produk():
    data = request.json or {}
    kategori = (data.get("kategori") or "").strip().lower()
    nama = (data.get("nama") or "").strip()

    try:
        harga = int(data.get("harga", 0))
        stok = int(data.get("stok", 0))
    except (ValueError, TypeError):
        return jsonify({"status": "gagal", "pesan": "Harga dan stok harus angka."})

    if not nama or harga <= 0 or stok < 0:
        return jsonify({"status": "gagal", "pesan": "Data produk belum valid."})

    if toko.cari_produk(nama):
        return jsonify({"status": "gagal", "pesan": "Produk sudah terdaftar."})

    extra = data.get("extra", "")
    try:
        if kategori == "makanan":
            p = Makanan(nama, harga, stok, str(extra))
        elif kategori == "mainan":
            p = Mainan(nama, harga, stok, int(extra))
        elif kategori == "minuman":
            p = Minuman(nama, harga, stok, int(extra))
        else:
            return jsonify({"status": "gagal", "pesan": "Kategori tidak dikenal."})
    except (ValueError, TypeError):
        return jsonify({"status": "gagal", "pesan": "Data tambahan tidak valid."})

    toko.tambah_produk(p)
    toko.simpan_database_json("database_toko.json")

    return jsonify(
        {"status": "sukses", "pesan": f"Produk '{nama}' berhasil ditambahkan!"}
    )


@app.route("/api/hapus_produk", methods=["POST"])
def hapus_produk():
    data = request.json or {}
    nama = (data.get("nama") or data.get("id_produk") or "").strip()

    if not nama:
        return jsonify({"status": "gagal", "pesan": "Nama produk belum diisi."})

    if not toko.hapus_produk(nama):
        return jsonify({"status": "gagal", "pesan": "Produk tidak ditemukan."})

    toko.simpan_database_json("database_toko.json")

    for sess in SESSIONS.values():
        sess["keranjang"] = [
            i for i in sess["keranjang"] if i["nama"].lower() != nama.lower()
        ]

    return jsonify(
        {"status": "sukses", "pesan": f"Produk '{nama}' berhasil dihapus."}
    )


if __name__ == "__main__":
    app.run(debug=True)