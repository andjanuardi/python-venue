import base64, json, os, re, urllib.request

BASE = "https://raw.githubusercontent.com/movietrailersxxi-pixel/web/main/dtv/v216/"
# BASE = "https://raw.githubusercontent.com/movietrailersxxi-pixel/web/main/dtv/v215/"
COUNTRIES = ["ID", "KR", "MY", "BR", "FR", "RU", "SG", "TR", "UA", "AE", "GB"]

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def k0(data):
    """Apply k0 decryption: reverse -> b64decode -> reverse -> b64decode -> reverse"""
    r1 = data[::-1]
    b1 = base64.b64decode(r1.encode("ascii"))
    s1 = b1.decode("utf-8", errors="replace")
    r2 = s1[::-1]
    b3 = r2.encode("utf-8")
    # Skip non-base64 chars (Android Base64.decode behavior)
    b64chars = b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    b64table = {c: i for i, c in enumerate(b64chars)}
    filtered = bytes(c for c in b3 if c in b64table)
    # Manual decode (handle any length)
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
    """Try to find the correct prefix offset by checking if k0 produces JSON"""
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

# Fetch and decrypt each country
decrypted = {}
for code in COUNTRIES:
    url = BASE + code + ".json"
    print(f"\n{code}.json: ", end="", flush=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=30)
        data = resp.read().decode("ascii")
        print(f"{len(data)} bytes, ", end="", flush=True)
        
        # Save raw
        raw_path = os.path.join(CACHE, f"{code}.json")
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(data)
        
        # Find prefix offset
        offset = find_prefix_offset(data)
        if offset >= 0:
            print(f"prefix={offset}, ", end="", flush=True)
            result = k0(data[offset:])
            # Parse JSON (might have extra data after first object)
            try:
                j = json.loads(result)
            except json.JSONDecodeError as e:
                # Try to find where valid JSON ends
                # Find matching brace
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
                    print(f"parse_error={e}", end="")
                    continue
            
            decrypted[code] = j
            channels = len(j.get("info", []))
            countries = j.get("country_list", j.get("countrylist", []))
            print(f"channels={channels}, countries={len(countries)}", end="")
            
            # Save decrypted
            dec_path = os.path.join(CACHE, f"{code}_decrypted.json")
            with open(dec_path, "w", encoding="utf-8") as f:
                json.dump(j, f, indent=2, ensure_ascii=False)
        else:
            print("NO PREFIX FOUND", end="")
    except Exception as e:
        print(f"ERROR: {e}", end="")
    print()

print(f"\n=== Successfully decrypted: {list(decrypted.keys())} ===")

# Analyze structure of first decrypted
if decrypted:
    code = list(decrypted.keys())[0]
    j = decrypted[code]
    print(f"\n=== Structure of {code}_decrypted.json ===")
    print(f"Top keys: {list(j.keys())}")
    if "info" in j and j["info"]:
        ch = j["info"][0]
        print(f"Channel fields: {list(ch.keys())}")
        
        # Count channel types
        jenis_count = {}
        for ch in j["info"]:
            t = ch.get("jenis", "?")
            jenis_count[t] = jenis_count.get(t, 0) + 1
        print(f"\nChannel types: {jenis_count}")
        
        # Count live/event fields
        live_count = sum(1 for ch in j["info"] if ch.get("is_live") == "true")
        fake_event = sum(1 for ch in j["info"] if ch.get("fake_event") == "true")
        is_movie = sum(1 for ch in j["info"] if ch.get("is_movie") == "true")
        print(f"Live: {live_count}, Fake event: {fake_event}, Movie: {is_movie}")
        
        # Sample channels with is_live
        for ch in j["info"][:5]:
            print(f"\n  [{ch['id']}] {ch['name']}")
            print(f"    jenis={ch.get('jenis')}, live={ch.get('is_live')}, event={ch.get('fake_event')}")
            print(f"    namespace={ch.get('namespace')}")
            print(f"    t_stamp={ch.get('t_stamp')}")
    
    # Show country list
    cl = j.get("country_list", j.get("countrylist", []))
    if cl:
        print(f"\nCountries ({len(cl)}):")
        for c in cl[:5]:
            print(f"  {c.get('alpha_2_code','?')}: {c.get('country_name','?')}")
