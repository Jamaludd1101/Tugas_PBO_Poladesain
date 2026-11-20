
# ==========================================
# FACADE PATTERN
# ==========================================

class MinimarketFacade:

    def __init__(self, toko, pembeli):
        self.toko = toko
        self.pembeli = pembeli

    # Menampilkan produk
    def lihat_produk(self):
        self.toko.tampilkan_produk()

    # Mencari produk
    def cari_produk(self, nama):
        return self.toko.cari_produk(nama)

    # Memulai proses belanja
    def mulai_belanja(self):
        self.toko.mulai_transaksi(self.pembeli)

    # Menyimpan database JSON
    def simpan_data(self):
        self.toko.simpan_database_json()

    # Memuat database JSON
    def muat_data(self):
        self.toko.muat_database_json()

    # Menambahkan produk
    def tambah_produk(self):
        self.toko.tambah_produk_interaktif()
