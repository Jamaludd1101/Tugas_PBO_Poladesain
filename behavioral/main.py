from behavioral_patterns import (
    KonteksVoucher,
    TanpaDiskon,
    VoucherNominal,
    VoucherPersen,
)
from pembeli import Pembeli
from toko import Toko


def uji_strategy_diskon():
    print("=== Uji Strategy Pattern (Voucher & Diskon) ===")
    subtotal = 60000
    konteks = KonteksVoucher(TanpaDiskon())

    print(f"Subtotal awal            : Rp{subtotal}")
    print(f"1. Tanpa diskon          : Rp{konteks.terapkan(subtotal)}")

    konteks.set_strategi(VoucherNominal(5000))
    print(f"2. HEMAT5K (potongan 5k) : Rp{konteks.terapkan(subtotal)}")

    konteks.set_strategi(VoucherPersen(10, maks_potongan=15000))
    print(f"3. HEMAT10 (diskon 10%)  : Rp{konteks.terapkan(subtotal)}")

    konteks.set_strategi(VoucherNominal(20000, min_belanja=50000))
    print(f"4. HEMAT20K (min 50k)    : Rp{konteks.terapkan(subtotal)}")


def main():
    uji_strategy_diskon()

    toko = Toko("Minimarket OOP")
    toko.muat_database_json("database_toko.json")

    pembeli = Pembeli("Nira", 100000)
    print(f"\nToko '{toko.nama}' siap digunakan untuk pembeli {pembeli.nama}.")


if __name__ == "__main__":
    main()