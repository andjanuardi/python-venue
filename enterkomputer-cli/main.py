#!/usr/bin/env python3
"""
Enterkomputer CLI — Interactive product search & scraper for enterkomputer.com
"""

import argparse
import asyncio
import sys

from cli import (
    cmd_brands,
    cmd_categories,
    cmd_credentials,
    cmd_detail,
    cmd_export,
    cmd_search,
    cmd_status,
    cmd_sync,
    interactive_mode,
)
from database import init_db


def main():
    parser = argparse.ArgumentParser(
        description="Enterkomputer CLI - Cari & Scrape Produk",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh:
  python main.py             Mode interaktif (TUI)
  python main.py search rtx  Cari produk
  python main.py sync        Sync data dari enterkomputer.com
  python main.py detail 123  Lihat detail produk via SKU
  python main.py categories  Lihat kategori
  python main.py brands      Lihat brand
  python main.py credentials Atur token API manual
  python main.py export      Export data
  python main.py status      Status database
        """,
    )

    parser.add_argument("command", nargs="?", default="interactive",
                        help="Perintah: sync, search, detail, categories, brands, credentials, export, status")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Argumen tambahan")

    args = parser.parse_args()
    init_db()

    commands = {
        "sync": lambda: asyncio.run(cmd_sync()),
        "search": lambda: cmd_search(args.args),
        "detail": lambda: cmd_detail(args.args),
        "categories": cmd_categories,
        "brands": cmd_brands,
        "credentials": cmd_credentials,
        "export": lambda: cmd_export(),
        "status": cmd_status,
    }

    if args.command in commands:
        commands[args.command]()
    elif args.command == "interactive":
        asyncio.run(interactive_mode())
    else:
        print(f"Perintah tidak dikenal: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        asyncio.run(interactive_mode())
