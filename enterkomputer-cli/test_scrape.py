#!/usr/bin/env python3
import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from scraper import EnterkomputerScraper, parse_products_from_api, BASE_URL
from database import init_db, save_products, search_products, count_products

TITLE = "=== Enterkomputer Scraper Test ==="
PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
BOLD = "\033[1m"
RST = "\033[0m"

def ok(msg=""):
    print(f"  {PASS} {msg}" if msg else f"  {PASS}")

def fail(msg=""):
    print(f"  {FAIL} {msg}" if msg else f"  {FAIL}")

results = []

def test(name, fn):
    start = time.time()
    try:
        fn()
        elapsed = time.time() - start
        results.append((name, True, elapsed))
    except Exception as e:
        elapsed = time.time() - start
        results.append((name, False, elapsed))
        print(f"  {FAIL} {name}: {e}")

def main():
    print(f"\n{BOLD}{TITLE}{RST}\n")
    scraper = EnterkomputerScraper()

    # Test 1: Load credentials
    def t1():
        ok = scraper.load_cookies_from_file()
        assert ok, "Gagal load credential"
        print(f"    cf_clearance: {scraper.cookies.get('cf_clearance', '')[:30]}...")
        print(f"    token: {scraper.api_token[:20]}..." if scraper.api_token else "    token: None")
        assert scraper.api_token, "token kosong"
        assert scraper.api_signature, "signature kosong"
    test("Load credentials", t1)

    # Test 2: Fetch sitemap
    def t2():
        xml = scraper.fetch_sitemap()
        assert xml, "Sitemap None"
        assert len(xml) > 1000, f"Sitemap terlalu pendek ({len(xml)} bytes)"
        print(f"    Size: {len(xml)} bytes")
        cats = scraper.get_categories_from_sitemap(xml)
        assert len(cats) > 0, "Kategori kosong"
        print(f"    Kategori: {len(cats)} ditemukan")
        for c in cats[:5]:
            print(f"      [{c.id}] {c.name}")
        if len(cats) > 5:
            print(f"      ... dan {len(cats)-5} lainnya")
    test("Fetch sitemap & kategori", t2)

    # Test 3: Refresh API token from category page
    def t3():
        ok = scraper.fetch_api_credentials(f"{BASE_URL}/category/17/processor")
        assert ok, "Gagal refresh token"
        print(f"    token: {scraper.api_token[:30]}...")
        print(f"    signature: {scraper.api_signature[:20]}...")
    test("Refresh API credentials", t3)

    # Test 4: Fetch product page
    products_page1 = []
    def t4():
        data = scraper.fetch_product_page(
            kcode="17", page=1,
            referer=f"{BASE_URL}/category/17/processor",
        )
        assert data, "API response None"
        assert data.get("status"), f"API status false: {data}"
        prods = parse_products_from_api(data, "Processor")
        assert len(prods) > 0, f"Produk kosong dari API"
        products_page1.extend(prods)
        print(f"    Produk di halaman 1: {len(prods)}")
        for p in prods[:5]:
            price = f"Rp{p.price:,}" if p.price > 0 else "-"
            status = "READY" if p.stock_status == "ready" else p.stock_status
            print(f"      [{p.code}] {p.name[:45]:45s}  {price:>15s}  {status}  {p.brand}")
    test("Fetch & parse produk page 1", t4)

    # Test 5: Fetch page 2 (to verify pagination works)
    def t5():
        data = scraper.fetch_product_page(
            kcode="17", page=2,
            referer=f"{BASE_URL}/category/17/processor",
        )
        assert data, "API page 2 response None"
        prods = parse_products_from_api(data, "Processor")
        print(f"    Produk di halaman 2: {len(prods)}")
        if prods:
            p = prods[0]
            price = f"Rp{p.price:,}" if p.price > 0 else "-"
            print(f"      Sample: [{p.code}] {p.name[:45]:45s}  {price}")
    test("Fetch page 2 (pagination)", t5)

    # Test 6: Save to DB and verify
    def t6():
        init_db()
        save_products(products_page1)
        total = count_products()
        assert total >= len(products_page1), f"DB hanya {total}, expected >= {len(products_page1)}"
        print(f"    Produk tersimpan: {total}")
        results = search_products("processor", limit=5)
        print(f"    Search 'processor': {len(results)} hasil")
        if results:
            print(f"      Sample: [{results[0].code}] {results[0].name[:45]}")
    test("Save ke DB & search", t6)

    # Test 7: Fetch product detail
    def t7():
        if not products_page1:
            raise Exception("Tidak ada produk untuk test detail")
        p = products_page1[0]
        detail = scraper.fetch_product_detail(p.code, p.slug)
        assert detail, f"Detail None untuk {p.code}"
        assert detail.name, "Nama produk detail kosong"
        print(f"    SKU: {detail.code}")
        print(f"    Nama: {detail.name[:50]}")
        price = f"Rp{detail.price:,}" if detail.price > 0 else "-"
        print(f"    Harga: {price}")
        print(f"    Status: {detail.stock_status}")
        print(f"    Spesifikasi: {len(detail.specs)} item")
        if detail.specs:
            for i, (k, v) in enumerate(list(detail.specs.items())[:5]):
                print(f"      {k}: {v}")
            if len(detail.specs) > 5:
                print(f"      ... dan {len(detail.specs)-5} lainnya")
        print(f"    Deskripsi: {detail.description[:80]}..." if detail.description else "    Deskripsi: (kosong)")
    test("Fetch detail produk", t7)

    # Summary
    total_time = sum(r[2] for r in results)
    print(f"\n{BOLD}{'='*50}{RST}")
    print(f"{BOLD}  HASIL TEST{RST}")
    print(f"{BOLD}{'='*50}{RST}")
    for name, ok_flag, elapsed in results:
        icon = PASS if ok_flag else FAIL
        print(f"  {icon} {name:40s} {elapsed:.1f}s")
    print(f"{BOLD}{'='*50}{RST}")
    all_ok = all(r[1] for r in results)
    status = "SEMUA BERHASIL" if all_ok else "ADA YANG GAGAL"
    color = "\033[92m" if all_ok else "\033[91m"
    print(f"  {color}{BOLD}{status}{RST} — {sum(1 for r in results if r[1])}/{len(results)} test passed, total {total_time:.1f}s")
    print()

    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
