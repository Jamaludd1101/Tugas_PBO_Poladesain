"""Web (Flask) - versi prosedural. Jalankan: python app.py"""

from flask import Flask, jsonify, render_template, request

import fungsi_minimarket as fm

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/produk", methods=["GET"])
def get_produk():
    return jsonify(fm.ambil_semua_produk())


@app.route("/api/checkout", methods=["POST"])
def checkout():
    data = request.json or {}
    items = []
    for item in data.get("keranjang", []):
        items.append({"kode": item.get("id_produk"), "qty": item.get("jumlah", 1)})

    hasil = fm.proses_transaksi(
        data.get("nama_pembeli", "Pelanggan"), items, data.get("voucher")
    )
    return jsonify(hasil)


@app.route("/api/tambah_produk", methods=["POST"])
def tambah_produk():
    data = request.json or {}
    hasil = fm.tambah_produk(
        data.get("kategori"),
        data.get("nama"),
        data.get("harga", 0),
        data.get("stok", 0),
        data.get("extra", ""),
    )
    return jsonify(hasil)


if __name__ == "__main__":
    app.run(debug=True)
