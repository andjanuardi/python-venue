import sys, json, argparse, uuid, shutil

from loklok_api_mobile import (
    login, is_logged_in, set_auth, SESSION, make_api_call
)

COOKIE_DOMAIN = ".loklok.site"

def gen_deviceid():
    return uuid.uuid4().hex[:16]

def get_vip_status():
    resp = make_api_call("GET", "/user/vip/h5/info")
    try:
        d = resp.json()
        if d.get("code") == "00000":
            data = d.get("data", {})
            vip_data = data.get("vipInfo") or data
            return vip_data.get("vip") or vip_data.get("isVip") or False
    except:
        pass
    return False

def clear():
    w = shutil.get_terminal_size().columns
    print("\n" + "=" * w)

def header(title):
    w = shutil.get_terminal_size().columns
    print("=" * w)
    if SESSION["logged_in"]:
        u = SESSION.get("userName", "")
        print(f"  {title}  |  User: {u}")
    else:
        print(f"  {title}  |  [Belum Login]")
    print("=" * w)

def pause():
    input("\n  [Enter] ")

def pilih(options, title="MENU"):
    clear()
    header(title)
    for i, (label, _) in enumerate(options, 1):
        print(f"  {i}. {label}")
    if options:
        print(f"  {len(options)+1}. Kembali")
    else:
        print("  1. Kembali")
    print()
    try:
        c = int(input("  Pilih: "))
        if 1 <= c <= len(options):
            return options[c-1][1]()
    except (ValueError, EOFError, KeyboardInterrupt):
        pass
    return "back"

def fmt_console(token, deviceid, user_id):
    lines = [
        f'var d="{COOKIE_DOMAIN}";',
        f'document.cookie="h5-token={token};path=/;domain="+d;',
        f'document.cookie="deviceid={deviceid};path=/;domain="+d;',
        f'document.cookie="userId={user_id};path=/;domain="+d;',
        f'document.cookie="clientType=H5;path=/;domain="+d;',
        f'document.cookie="versionCode=32;path=/;domain="+d;',
        "location.reload();",
    ]
    return "\n".join(lines)

def fmt_editthiscookie(token, deviceid, user_id):
    cookies = [
        {"domain": COOKIE_DOMAIN, "name": "h5-token", "value": token, "path": "/", "httpOnly": False, "secure": False, "sameSite": "Lax"},
        {"domain": COOKIE_DOMAIN, "name": "deviceid", "value": deviceid, "path": "/", "httpOnly": False, "secure": False, "sameSite": "Lax"},
        {"domain": COOKIE_DOMAIN, "name": "userId", "value": user_id, "path": "/", "httpOnly": False, "secure": False, "sameSite": "Lax"},
        {"domain": COOKIE_DOMAIN, "name": "clientType", "value": "H5", "path": "/", "httpOnly": False, "secure": False, "sameSite": "Lax"},
        {"domain": COOKIE_DOMAIN, "name": "versionCode", "value": "32", "path": "/", "httpOnly": False, "secure": False, "sameSite": "Lax"},
    ]
    return json.dumps(cookies, indent=2)

def fmt_curl(token, deviceid, user_id):
    parts = [
        f"h5-token={token}",
        f"deviceid={deviceid}",
        f"userId={user_id}",
        "clientType=H5",
        "versionCode=32",
    ]
    return "; ".join(parts)

def salin(text):
    import subprocess
    try:
        proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
        proc.communicate(input=text.encode())
        print("  ✅ Disalin ke clipboard!")
    except FileNotFoundError:
        try:
            proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            proc.communicate(input=text.encode())
            print("  ✅ Disalin ke clipboard!")
        except FileNotFoundError:
            print("  ⚠️ Clipboard tidak tersedia. Salin manual.")

def do_login():
    clear()
    header("LOGIN")
    try:
        email = input("  Email: ").strip()
        pwd = input("  Password: ").strip()
        if not email or not pwd:
            return
    except (EOFError, KeyboardInterrupt):
        return
    print("\n  Login...")
    result = login(email, pwd)
    if result:
        print(f"  ✅ Berhasil! User: {result.get('userName', '?')}")
    else:
        print("  ❌ Login gagal. Cek email/password.")
    pause()

def do_logout():
    set_auth()
    print("\n  Logout berhasil.")
    pause()

def show_info():
    clear()
    header("INFO AKUN")
    token = SESSION.get("token", "")
    deviceid = SESSION.get("deviceid", "") or gen_deviceid()
    user_id = SESSION.get("userId", "")
    user_name = SESSION.get("userName", "")
    vip = get_vip_status()
    print(f"  User:     {user_name} ({user_id})")
    print(f"  VIP:      {'✅ Ya' if vip else '❌ Tidak'}")
    print(f"  Domain:   {COOKIE_DOMAIN}")
    print(f"  Token:    {token[:50]}...")
    print(f"  DeviceID: {deviceid}")
    pause()

def generate():
    token = SESSION.get("token", "")
    deviceid = SESSION.get("deviceid", "") or gen_deviceid()
    user_id = SESSION.get("userId", "")
    user_name = SESSION.get("userName", "")
    vip = get_vip_status()

    formats = [
        ("Console Browser (F12)", "console"),
        ("EditThisCookie (JSON)", "editthis"),
        ("Cookie Header (curl)", "curl"),
    ]

    while True:
        clear()
        header("GENERATE COOKIE")
        print(f"  User:   {user_name} ({user_id})")
        print(f"  VIP:    {'✅' if vip else '❌'}")
        print(f"  Token:  {token[:40]}...")
        print()
        for i, (label, _) in enumerate(formats, 1):
            print(f"  {i}. {label}")
        print(f"  {len(formats)+1}. Salin Semua")
        print(f"  {len(formats)+2}. Kembali")
        print()
        try:
            c = int(input("  Pilih format cookie: "))
        except (ValueError, EOFError, KeyboardInterrupt):
            return

        if c == len(formats) + 2:
            return
        if c == len(formats) + 1:
            all_text = []
            for _, key in formats:
                if key == "console":
                    all_text.append("=== FORMAT 1: Console Browser ===")
                    all_text.append(fmt_console(token, deviceid, user_id))
                elif key == "editthis":
                    all_text.append("=== FORMAT 2: EditThisCookie ===")
                    all_text.append(fmt_editthiscookie(token, deviceid, user_id))
                elif key == "curl":
                    all_text.append("=== FORMAT 3: Cookie Header ===")
                    all_text.append(fmt_curl(token, deviceid, user_id))
                all_text.append("")
            show_output("\n".join(all_text))
            return
        if 1 <= c <= len(formats):
            label, key = formats[c-1]
            if key == "console":
                text = fmt_console(token, deviceid, user_id)
            elif key == "editthis":
                text = fmt_editthiscookie(token, deviceid, user_id)
            elif key == "curl":
                text = fmt_curl(token, deviceid, user_id)
            show_output(text, label)
            return

def show_output(text, label="COOKIE"):
    clear()
    header(label)
    print()
    print(text)
    print()
    print("  [1] Salin ke clipboard")
    print("  [0] Kembali")
    print()
    try:
        a = int(input("  Pilih: "))
        if a == 1:
            salin(text)
    except (ValueError, EOFError, KeyboardInterrupt):
        pass

def about():
    clear()
    header("TENTANG")
    print("  Loklok Cookie Generator v1.0")
    print("  Domain: " + COOKIE_DOMAIN)
    print()
    print("  Format:")
    print("  1. Console Browser — paste di F12, reload")
    print("  2. EditThisCookie — import JSON")
    print("  3. Cookie Header — pasang di curl/request")
    print()
    print("  Catatan:")
    print("  - Token expired, perlu generate ulang")
    print("  - DeviceID digenerate otomatis jika kosong")
    pause()

def main():
    while True:
        ops = [
            ("Generate Cookie", generate),
            ("Info Akun", show_info),
            ("Login" if not is_logged_in() else "Logout",
             do_login if not is_logged_in() else do_logout),
            ("Tentang", about),
        ]
        r = pilih(ops, "LOKLOK COOKIE GENERATOR")
        if r == "back":
            break
    print("\n  Sampai jumpa!")

def main_cli():
    parser = argparse.ArgumentParser(description="Loklok Cookie Generator")
    parser.add_argument("--email", type=str, help="Email untuk login")
    parser.add_argument("--pwd", type=str, help="Password untuk login")
    parser.add_argument("--format", choices=["console", "editthis", "curl", "all"], default="all",
                        help="Format output (default: all)")
    parser.add_argument("--no-header", action="store_true", help="Hanya output cookie, tanpa header")
    args = parser.parse_args()

    if args.email and args.pwd:
        result = login(args.email, args.pwd)
        if not result:
            print("Login gagal.", file=sys.stderr)
            sys.exit(1)

    if not is_logged_in():
        main()
        return

    token = SESSION.get("token", "")
    deviceid = SESSION.get("deviceid", "") or gen_deviceid()
    user_id = SESSION.get("userId", "")
    user_name = SESSION.get("userName", "")
    vip = get_vip_status()

    if args.no_header:
        if args.format in ("console", "all"):
            print(fmt_console(token, deviceid, user_id))
            print()
        if args.format in ("editthis", "all"):
            print(fmt_editthiscookie(token, deviceid, user_id))
            print()
        if args.format in ("curl", "all"):
            print(fmt_curl(token, deviceid, user_id))
        return

    sep = "=" * 50
    print()
    print(sep)
    print("           LOKLOK COOKIE GENERATOR")
    print(sep)
    print(f"  User:     {user_name} ({user_id})")
    print(f"  VIP:      {'✅ Ya' if vip else '❌ Tidak'}")
    print(f"  Domain:   {COOKIE_DOMAIN}")
    print(f"  Token:    {token[:40]}...")
    print(sep)
    print()

    if args.format in ("console", "all"):
        print("=== FORMAT 1: Console Browser (F12 -> Console) ===")
        print()
        print(fmt_console(token, deviceid, user_id))
        print()
    if args.format in ("editthis", "all"):
        print("=== FORMAT 2: EditThisCookie (JSON) ===")
        print()
        print(fmt_editthiscookie(token, deviceid, user_id))
        print()
    if args.format in ("curl", "all"):
        print("=== FORMAT 3: Cookie Header (curl) ===")
        print()
        print(fmt_curl(token, deviceid, user_id))
        print()

    print(sep)
    print("  ✅ Paste FORMAT 1 di Console Browser F12")
    print("     atau import FORMAT 2 ke EditThisCookie.")
    print("     Refresh halaman setelahnya.")
    print(sep)

if __name__ == "__main__":
    try:
        main_cli()
    except (KeyboardInterrupt, EOFError):
        print("\n  Keluar...")
