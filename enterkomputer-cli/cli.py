import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text
from rich.style import Style

from database import (
    count_products,
    get_brands,
    get_categories,
    get_distinct_brands,
    get_distinct_categories,
    get_product,
    init_db,
    save_brands,
    save_categories,
    save_products,
    search_products,
)
from models import Brand, Category, Product
from scraper import EnterkomputerScraper, parse_products_from_api, BASE_URL, COOKIE_FILE

console = Console()
COOKIE_FILE = Path(".ek_cookies.json")


def print_header():
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Enterkomputer CLI[/bold cyan] — Pencarian & Scraping Produk",
        border_style="cyan"
    ))
    console.print()


def cmd_credentials():
    """Manually set API credentials (cf_clearance, token, signature)."""
    console.print("[bold yellow]Masukkan kredensial API Enterkomputer[/bold yellow]")
    console.print("[dim]Cara mendapatkannya:[/dim]")
    console.print("[dim]1. Buka https://www.enterkomputer.com/ di Chrome[/dim]")
    console.print("[dim]2. Buka DevTools (F12) → Application → Cookies[/dim]")
    console.print("[dim]3. Copy nilai cookie [bold]cf_clearance[/bold][/dim]")
    console.print("[dim]4. Buka https://www.enterkomputer.com/category/17/processor[/dim]")
    console.print("[dim]5. Inspect element, cari div dgn attribute [bold]data-api-token[/bold][/dim]")
    console.print("[dim]6. Copy nilai data-api-token dan data-api-signature[/dim]")
    console.print()

    cf = Prompt.ask("cf_clearance", password=False)
    tok = Prompt.ask("data-api-token")
    sig = Prompt.ask("data-api-signature")

    s = EnterkomputerScraper()
    s.set_credentials(cf, tok, sig)
    console.print("[green]✓ Kredensial disimpan ke .ek_cookies.json[/green]")

    test = Prompt.ask("Test koneksi?", default="y")
    if test.lower() in ("y", "yes"):
        if s.fetch_api_credentials(f"{BASE_URL}/category/17/processor"):
            console.print("[green]✓ Koneksi berhasil![/green]")
        else:
            console.print("[red]✗ Gagal. Cek lagi credential.[/red]")


async def cmd_sync():
    init_db()
    scraper = EnterkomputerScraper()
    has_creds = scraper.load_cookies_from_file()

    if not has_creds:
        console.print("[yellow]Belum ada kredensial tersimpan.[/yellow]")
        choice = Prompt.ask(
            "Pilih metode",
            default="2",
            choices=["1", "2"],
        )
        if choice == "1":
            cmd_credentials()
            scraper.load_cookies_from_file()
        else:
            console.print("[yellow]Mencoba bypass Cloudflare via nodriver...[/yellow]")
            console.print("[dim]Membutuhkan Chrome/Chromium terinstall[/dim]")
            ok = scraper.try_nodriver_bypass()
            if not ok:
                console.print("[red]Gagal bypass Cloudflare.[/red]")
                console.print("Gunakan perintah: [bold]python main.py credentials[/bold]")
                return
            console.print("[green]✓ Bypass berhasil![/green]")

    if not scraper.has_credentials():
        console.print("[red]Kredensial tidak lengkap.[/red]")
        return

    console.print("[yellow]Mengambil sitemap & data kategori...[/yellow]")
    sitemap = scraper.fetch_sitemap()
    if sitemap:
        categories = scraper.get_categories_from_sitemap(sitemap)
    else:
        console.print("[yellow]Sitemap gagal, pakai fallback kategori.[/yellow]")
        categories = scraper._fallback_categories()
    save_categories(categories)
    console.print(f"[bold]Ditemukan {len(categories)} kategori[/bold]")

    ref_url = f"{BASE_URL}/category/{categories[0].id}/{categories[0].slug}"
    if not scraper.fetch_api_credentials(ref_url):
        console.print("[yellow]Gagal refresh token dari halaman kategori.[/yellow]")

    total_products = 0
    all_brands: dict[str, int] = {}

    overall = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    )
    overall_task = overall.add_task("[cyan]Sync produk...", total=len(categories))
    batch_size = 50
    product_batch: list[Product] = []

    with overall:
        for cat in categories:
            page = 1
            while True:
                data = scraper.fetch_product_page(
                    kcode=str(cat.id),
                    page=page,
                    referer=f"{BASE_URL}/category/{cat.id}/{cat.slug}",
                )
                if not data:
                    break

                items = data.get("result", [])
                products = parse_products_from_api(data, cat.name)
                if not products:
                    break

                for p in products:
                    product_batch.append(p)
                    total_products += 1
                    brand_name = p.brand or "Unknown"
                    all_brands[brand_name] = all_brands.get(brand_name, 0) + 1

                    if len(product_batch) >= batch_size:
                        save_products(product_batch)
                        product_batch.clear()

                page += 1

            overall.update(overall_task, advance=1)

        if product_batch:
            save_products(product_batch)

    save_brands([
        Brand(name=n, product_count=c) for n, c in
        sorted(all_brands.items(), key=lambda x: -x[1])
    ])

    console.print()
    console.print(f"[green]✓ Selesai! Total {total_products} produk disimpan.[/green]")
    console.print()


def cmd_search(args: list[str] = None):
    keyword = " ".join(args) if args else Prompt.ask("[bold]Kata kunci pencarian[/bold]")
    if not keyword:
        return

    results = search_products(keyword, limit=100)
    if not results:
        console.print("[yellow]Tidak ada produk ditemukan.[/yellow]")
        return

    console.print(f"\n[bold]Ditemukan {len(results)} produk:[/bold]")
    _show_products_table(results)

    actions = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    actions.add_column("Aksi", style="bold cyan")
    actions.add_column("Keterangan")
    actions.add_row("[d]", "Lihat detail produk (masukkan SKU)")
    actions.add_row("[e]", "Export hasil ke CSV/JSON")
    actions.add_row("[f]", "Filter lanjutan")
    actions.add_row("[q]", "Kembali")

    console.print(Panel(actions, title="Aksi", border_style="blue"))
    action = Prompt.ask("Pilih", default="q", choices=["d", "e", "f", "q"])

    if action == "d":
        sku = Prompt.ask("Masukkan SKU produk")
        cmd_detail([sku])
    elif action == "e":
        cmd_export(results)
    elif action == "f":
        _interactive_search(keyword)


def _interactive_search(initial_keyword: str = ""):
    categories = get_distinct_categories()
    brands = get_distinct_brands()

    keyword = initial_keyword or Prompt.ask("Kata kunci")
    if not keyword:
        return

    category = ""
    if Confirm.ask("Filter kategori?", default=False):
        choices = [""] + categories
        for i, c in enumerate(choices[:30]):
            console.print(f"  {i}. {c or 'Semua'}")
        choice = IntPrompt.ask("Nomor", default=0)
        if 0 <= choice < len(choices):
            category = choices[choice]

    brand = ""
    if Confirm.ask("Filter brand?", default=False):
        choices = [""] + brands
        for i, b in enumerate(choices[:30]):
            console.print(f"  {i}. {b or 'Semua'}")
        choice = IntPrompt.ask("Nomor", default=0)
        if 0 <= choice < len(choices):
            brand = choices[choice]

    min_p = 0
    max_p = 0
    if Confirm.ask("Filter harga?", default=False):
        min_p = int(FloatPrompt.ask("Minimum (Rp)", default=0))
        max_p = int(FloatPrompt.ask("Maksimum (Rp)", default=0))

    in_stock = Confirm.ask("Ready saja?", default=False)

    sort_map = {
        "1": ("", "Default"),
        "2": ("termurah", "Termurah"),
        "3": ("termahal", "Termahal"),
        "4": ("nama", "Nama A-Z"),
    }
    console.print("Urutan:")
    for k, (_, label) in sort_map.items():
        console.print(f"  {k}. {label}")
    sort_by = sort_map.get(Prompt.ask("Pilih", default="1", choices=list(sort_map.keys())), ("", ""))[0]

    results = search_products(
        keyword=keyword, category=category, brand=brand,
        min_price=min_p, max_price=max_p, in_stock=in_stock,
        sort_by=sort_by, limit=100,
    )

    if not results:
        console.print("[yellow]Tidak ada hasil.[/yellow]")
        return

    console.print(f"\n[bold]{len(results)} produk:[/bold]")
    _show_products_table(results)


def _show_products_table(products: list[Product]):
    table = Table(box=box.SIMPLE, show_lines=True)
    table.add_column("SKU", style="cyan", no_wrap=True)
    table.add_column("Nama Produk", style="white")
    table.add_column("Harga", style="green", justify="right")
    table.add_column("Status")
    table.add_column("Brand", style="blue")
    table.add_column("Kategori", style="yellow")

    for p in products:
        status = "[bold green]READY[/bold green]" if p.stock_status == "ready" else "[red]KOSONG[/red]"
        price = f"Rp{p.price:,}" if p.price > 0 else "-"
        table.add_row(
            p.code,
            (p.name[:55] + "..") if len(p.name) > 55 else p.name,
            price, status, p.brand, p.category,
        )
    console.print(table)
    console.print()


def cmd_detail(args: list[str]):
    sku = args[0] if args else Prompt.ask("[bold]Masukkan SKU produk[/bold]")
    product = get_product(sku)
    if not product:
        console.print(f"[red]Produk {sku} tidak ditemukan.[/red]")
        return

    console.print()
    console.print(Panel(product.name, border_style="cyan"))

    info = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    info.add_column("Field", style="bold yellow")
    info.add_column("Nilai")
    info.add_row("SKU", product.code)
    info.add_row("Harga", f"Rp{product.price:,}" if product.price > 0 else "-")
    info.add_row("Brand", product.brand)
    info.add_row("Kategori", product.category)
    status = "[bold green]READY[/bold green]" if product.stock_status == "ready" else "[red]KOSONG[/red]"
    info.add_row("Status", status)
    info.add_row("Berat", product.weight or "-")
    if product.description:
        info.add_row("Deskripsi", product.description[:300])
    console.print(info)

    if product.specs:
        console.print("\n[bold yellow]Spesifikasi:[/bold yellow]")
        spec_table = Table(box=box.SIMPLE)
        spec_table.add_column("Komponen", style="cyan")
        spec_table.add_column("Nilai", style="white")
        for k, v in product.specs.items():
            spec_table.add_row(k, v)
        console.print(spec_table)

    url = f"{BASE_URL}/detail/{product.code}/{product.slug}"
    console.print(f"\n🔗 [link={url}]{url}[/link]")
    console.print()


def cmd_categories():
    cats = get_categories()
    if not cats:
        console.print("[yellow]Belum sync. Jalankan: python main.py sync[/yellow]")
        return
    table = Table(box=box.SIMPLE)
    table.add_column("ID", style="cyan")
    table.add_column("Kategori", style="white")
    table.add_column("Slug", style="dim")
    for c in cats:
        table.add_row(str(c.id), c.name, c.slug)
    console.print(table)


def cmd_brands():
    brands = get_brands()
    if not brands:
        console.print("[yellow]Belum sync. Jalankan: python main.py sync[/yellow]")
        return
    table = Table(box=box.SIMPLE)
    table.add_column("Brand", style="blue")
    table.add_column("Produk", style="green", justify="right")
    for b in brands:
        table.add_row(b.name, str(b.product_count))
    console.print(table)


def cmd_export(products: Optional[list[Product]] = None):
    if products is None:
        total = count_products()
        if total == 0:
            console.print("[yellow]Database kosong. Sync dulu.[/yellow]")
            return
        keyword = Prompt.ask("Kata kunci export")
        products = search_products(keyword, limit=1000) if keyword else []

    if not products:
        console.print("[yellow]Tidak ada data.[/yellow]")
        return

    fmt = Prompt.ask("Format", default="csv", choices=["csv", "json"])
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"enterkomputer_{ts}.{fmt}"

    if fmt == "csv":
        with open(fname, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["SKU", "Nama", "Harga", "Brand", "Kategori", "Status", "URL"])
            for p in products:
                url = f"{BASE_URL}/detail/{p.code}/{p.slug}" if p.slug else ""
                w.writerow([p.code, p.name, p.price, p.brand, p.category, p.stock_status, url])
    else:
        data = []
        for p in products:
            data.append({
                "sku": p.code, "nama": p.name, "harga": p.price,
                "brand": p.brand, "kategori": p.category,
                "status": p.stock_status,
                "url": f"{BASE_URL}/detail/{p.code}/{p.slug}" if p.slug else "",
            })
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    console.print(f"[green]✓ {len(products)} produk → [bold]{fname}[/bold][/green]")


def cmd_status():
    total = count_products()
    cats = get_categories()
    brands = get_brands()
    has_creds = COOKIE_FILE.exists()

    console.print()
    info = Table(box=box.SIMPLE, show_header=False)
    info.add_column("Item", style="bold yellow")
    info.add_column("Value", style="green")
    info.add_row("Database", "enterkomputer.db")
    info.add_row("Total Produk", str(total))
    info.add_row("Kategori", str(len(cats)))
    info.add_row("Brand", str(len(brands)))
    info.add_row("Kredensial", "✓ Ada" if has_creds else "[red]✗ Belum[/red]")
    console.print(info)
    console.print()


async def interactive_mode():
    init_db()

    while True:
        console.clear()
        print_header()

        total = count_products()
        status_text = f"[bold cyan]{total}[/bold cyan] produk" if total else "[yellow]Belum sync[/yellow]"
        cred_status = "✓" if COOKIE_FILE.exists() else "✗"

        menu = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        menu.add_column("", style="bold cyan", width=16)
        menu.add_column("Keterangan", style="white", width=55)

        menu.add_row("[1] Cari Produk", "Cari produk di database lokal")
        menu.add_row("[2] Sync Data", f"Scrape dari enterkomputer.com ({status_text})")
        menu.add_row("[3] Kategori", "Lihat semua kategori")
        menu.add_row("[4] Brand", "Lihat semua brand")
        menu.add_row("[5] Detail", "Lihat detail produk via SKU")
        menu.add_row("[6] Export", "Export data ke CSV/JSON")
        menu.add_row("[7] Status", "Info database & kredensial")
        menu.add_row("[8] Credentials", f"Atur token API ({cred_status})")
        menu.add_row("[q] Keluar", "Tutup aplikasi")

        console.print(Panel(menu, title="Menu Utama", border_style="cyan"))
        console.print()

        choice = Prompt.ask("Pilih", default="q")

        if choice == "1":
            cmd_search()
        elif choice == "2":
            await cmd_sync()
        elif choice == "3":
            cmd_categories()
        elif choice == "4":
            cmd_brands()
        elif choice == "5":
            cmd_detail([])
        elif choice == "6":
            cmd_export()
        elif choice == "7":
            cmd_status()
        elif choice == "8":
            cmd_credentials()
        elif choice.lower() == "q":
            console.print("[cyan]Terima kasih![/cyan]")
            break

        if choice in ("1", "3", "4", "5", "7", "8"):
            Prompt.ask("\n[dim]Enter untuk kembali[/dim]")
