import base64, json, os, sys, urllib.request

# BASE = "https://raw.githubusercontent.com/movietrailersxxi-pixel/web/main/dtv/v215/"
BASE = "https://raw.githubusercontent.com/movietrailersxxi-pixel/web/main/dtv/v216/"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def k0(data):
    r1 = data[::-1]
    b1 = base64.b64decode(r1.encode("ascii"))
    s1 = b1.decode("utf-8", errors="replace")
    r2 = s1[::-1]
    b3 = r2.encode("utf-8")
    b64chars = b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    b64table = {c: i for i, c in enumerate(b64chars)}
    filtered = bytes(c for c in b3 if c in b64table)
    result = bytearray()
    buf = 0
    bits = 0
    for c in filtered:
        buf = (buf << 6) | b64table[c]
        bits += 6
        if bits >= 8:
            bits -= 8
            result.append((buf >> bits) & 0xFF)
            buf &= (1 << bits) - 1
    s4 = bytes(result).decode("utf-8", errors="replace")
    return s4[::-1]

def find_prefix_offset(data):
    for offset in range(0, min(200, len(data))):
        try:
            result = k0(data[offset:])
            if result.startswith("{"):
                try:
                    json.loads(result)
                    return offset
                except json.JSONDecodeError:
                    pass
        except:
            pass
    return -1

def decrypt(code):
    url = BASE + code + ".json"
    print(f"{code}.json: ", end="", flush=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=30)
        data = resp.read().decode("ascii")
        print(f"{len(data)} bytes, ", end="", flush=True)

        raw_path = os.path.join(CACHE, f"{code}.json")
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(data)

        offset = find_prefix_offset(data)
        if offset >= 0:
            print(f"prefix={offset}, ", end="", flush=True)
            result = k0(data[offset:])
            try:
                j = json.loads(result)
            except json.JSONDecodeError:
                depth = 0
                for i, c in enumerate(result):
                    if c == '{':
                        depth += 1
                    elif c == '}':
                        depth -= 1
                        if depth == 0:
                            j = json.loads(result[:i+1])
                            break
                else:
                    print("parse_error", end="")
                    return

            channels = len(j.get("info", []))
            countries = j.get("countrylist", [])
            print(f"channels={channels}, countries={len(countries)}", end="")

            dec_path = os.path.join(CACHE, f"{code}_decrypted.json")
            with open(dec_path, "w", encoding="utf-8") as f:
                json.dump(j, f, indent=2, ensure_ascii=False)
        else:
            print("NO PREFIX FOUND", end="")
    except Exception as e:
        print(f"ERROR: {e}", end="")
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python decrypt.py <CODE> [CODE2 ...]")
        sys.exit(1)
    for code in sys.argv[1:]:
        decrypt(code.upper())
