"""Server Web Flask LokaMart-DPF yang terhubung ke MinimarketFacade."""

from __future__ import annotations

from flask import Flask, jsonify, render_template, request

# Gunakan relative import hanya jika dijalankan sebagai package (python -m poladesain.app)
if __package__:
    from .minimarket_facade import MinimarketFacade
else:
    from minimarket_facade import MinimarketFacade

app = Flask(__name__)
facade = MinimarketFacade("LokaMart")


@app.route("/")
def index():
    """Menampilkan halaman utama antarmuka web LokaMart."""
    return render_template("index.html")


@app.route("/api/produk", methods=["GET"])
def get_produk():
    """Mengambil daftar produk dalam format JSON."""
    return jsonify(facade.ambil_semua_produk())


@app.route("/api/riwayat", methods=["GET"])
def get_riwayat():
    """Mengambil riwayat transaksi dari riwayat.json."""
    return jsonify(facade.ambil_riwayat())


@app.route("/api/checkout", methods=["POST"])
def checkout():
    """Memproses checkout secara atomik melalui MinimarketFacade."""
    data_transaksi = request.get_json(silent=True) or {}
    nama_pembeli = data_transaksi.get("nama_pembeli", "Pelanggan Web")
    keranjang_frontend = (
        data_transaksi.get("keranjang") or data_transaksi.get("items") or []
    )
    kode_voucher = data_transaksi.get("voucher")
    saldo_awal = data_transaksi.get("saldo")

    hasil = facade.proses_checkout(
        nama_pembeli=nama_pembeli,
        items=keranjang_frontend,
        kode_voucher=kode_voucher,
        saldo_awal=saldo_awal,
        simpan_ke_disk=True,
        verbose=False,
    )

    if hasil["status"] == "sukses":
        return jsonify(
            {
                "status": "sukses",
                "pesan": "Transaksi berhasil diproses.",
                "struk": hasil["struk"],
            }
        )

    return jsonify({"status": "gagal", "pesan": hasil["pesan"]}), 400


@app.route("/api/tambah_produk", methods=["POST"])
def tambah_produk():
    """Menambahkan produk baru melalui MinimarketFacade & ProdukCreator."""
    data = request.get_json(silent=True) or {}
    hasil = facade.tambah_produk(
        kategori=data.get("kategori", ""),
        nama=data.get("nama", ""),
        harga=data.get("harga", 0),
        stok=data.get("stok", 0),
        extra=data.get("extra", ""),
    )
    return jsonify({"status": hasil["status"], "pesan": hasil["pesan"]})


if __name__ == "__main__":
    app.run(debug=True)
