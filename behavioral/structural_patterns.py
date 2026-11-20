
# ==========================================
# DECORATOR PATTERN
# ==========================================

class ProdukDecorator:
    def __init__(self, produk):
        self._produk = produk

    def __getattr__(self, nama):
        return getattr(self._produk, nama)

    @property
    def harga(self):
        return self.harga_akhir()

    def harga_akhir(self):
        return self._produk.harga


class BiayaKemasanDecorator(ProdukDecorator):
    def __init__(self, produk, biaya=1000):
        super().__init__(produk)
        self.biaya = biaya

    def harga_akhir(self):
        return super().harga_akhir() + self.biaya


class PajakDecorator(ProdukDecorator):
    def __init__(self, produk, persen=11):
        super().__init__(produk)
        self.persen = persen

    def harga_akhir(self):
        harga = super().harga_akhir()
        return int(harga * (1 + self.persen / 100))


def tambahkan_biaya(produk):
    produk = BiayaKemasanDecorator(produk, 1000)
    produk = PajakDecorator(produk, 11)
    return produk



import json
import csv


class JSONToCSVAdapter:

    def export(self, file_json, file_csv):

        with open(file_json, "r", encoding="utf-8") as file:
            data = json.load(file)

        with open(file_csv, "w", newline="",
                  encoding="utf-8-sig") as file:

            writer = csv.writer(file)

            writer.writerow([
                "Pembeli",
                "Produk",
                "Jumlah",
                "Total"
            ])

            for transaksi in data:
                for item in transaksi.get("items", []):
                    writer.writerow([
                        transaksi.get("pembeli", ""),
                        item.get("nama", ""),
                        item.get("qty", 0),
                        transaksi.get("total_bayar", 0)
                    ])

        print("Berhasil mengubah JSON menjadi CSV!")



class StrukToPDFAdapter:

    def export(self, data, nama_file="struk.pdf"):

        pass

        # from reportlab.lib.pagesizes import A4
        # from reportlab.pdfgen import canvas

        # pdf = canvas.Canvas(nama_file, pagesize=A4)

        # y = 800

        # pdf.setFont("Helvetica-Bold", 16)
        # pdf.drawString(50, y, "STRUK MINIMARKET")

        # y -= 40

        # pdf.setFont("Helvetica", 11)

        # pdf.drawString(
        #     50, y,
        #     "Pembeli: " + str(data.get("pembeli", ""))
        # )

        # y -= 30

        # for item in data.get("items", []):
        #     teks = (
        #         f"{item.get('nama', '')} "
        #         f"x{item.get('qty', 0)}"
        #     )

        #     pdf.drawString(50, y, teks)
        #     y -= 20

        # y -= 20

        # pdf.drawString(
        #     50, y,
        #     "Total: Rp" + str(data.get("total_bayar", 0))
        # )

        # pdf.save()

        print("Berhasil membuat struk PDF!")
