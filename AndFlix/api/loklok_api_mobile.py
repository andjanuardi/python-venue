import requests
import base64
import hashlib
import time
import random
import string
import json

from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.PublicKey import RSA as RSA_Key

BASE_URL = "https://h5-api.hehekang.com"

SESSION = {
    "token": "",
    "deviceid": "",
    "userId": "",
    "userName": "",
    "logged_in": False,
}

PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC7GW1zgx9/ssgCjoZhuCvISy5N
s9T2UgAzjJqS2uTGuCVtZsN3TE5wd4OIeiVG2TVDH2Gxlzrxd5jg7P6IiUKqsliS
dZxx/ceqLDawKgvO8mJ+hJJsuIxSL7Bi6T0p+xH6ibw4orGfCFUJhGryE9hqp9qT
RiHOMvgC2si1VqrgaQIDAQAB
-----END PUBLIC KEY-----"""

DEFAULT_HEADERS = {
    "clientType": "ANDROID",
    "versionCode": "42",
    "lang": "en",
    "timezone": "GMT+7",
    "deviceid": "",
    "token": "",
    "adid": "",
    "content-type": "application/json",
}

AUTH_HEADERS = {}


def gen_key(length=16):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def rsa_encrypt(data):
    key = RSA_Key.import_key(PUBLIC_KEY_PEM)
    cipher = PKCS1_v1_5.new(key)
    encrypted = cipher.encrypt(data.encode())
    return base64.b64encode(encrypted).decode()


def aes_ecb_encrypt(plaintext, key):
    cipher = AES.new(key.encode("utf-8"), AES.MODE_ECB)
    padded = _pkcs7_pad(plaintext.encode("utf-8"), 16)
    encrypted = cipher.encrypt(padded)
    return base64.b64encode(encrypted).decode()


def _pkcs7_pad(data, block_size=16):
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)


def md5_hash(data):
    return hashlib.md5(data.encode("utf-8") if isinstance(data, str) else data).hexdigest()


def convert_obj(params, t=False):
    a = []
    for r in sorted(params.keys()):
        n = params[r]
        if n is None:
            continue
        if isinstance(n, list):
            for i, val in enumerate(n):
                if isinstance(val, dict):
                    a.append(f"{r}={convert_obj(val, True)}")
                elif isinstance(val, list):
                    a.append(f"{r}={convert_obj({'key': val}, False)}")
                else:
                    a.append(f"{r}[{i}]={val}")
        elif isinstance(n, dict):
            a.append(f"{r}={convert_obj(n, True)}")
        else:
            a.append(f"{r}={n}")

    if t:
        i = {}
        for entry in a:
            key, _, val = entry.partition("=")
            if key in i:
                i[key].append(val)
            else:
                i[key] = [val]
        sorted_keys = sorted(i.keys())
        return "".join("".join(i[k]) for k in sorted_keys)

    return "".join(entry.split("=", 1)[1] if "=" in entry else "" for entry in a)


def get_sign(params, random_key, current_time):
    serialized = convert_obj(params, True)
    encoded = base64.b64encode(serialized.encode("utf-8")).decode("utf-8")
    r = f"{current_time}{encoded}".replace("+", "-").replace("/", "_")
    encrypted = aes_ecb_encrypt(r, random_key)
    return md5_hash(encrypted)


def make_api_call(method, path, params=None, data=None, client_type=None, version_code=None, timeout=30):
    random_key = gen_key()
    current_time = str(int(time.time() * 1000))

    sign_params = params if method.upper() == "GET" else data
    sign = get_sign(sign_params if sign_params else {}, random_key, current_time)
    aes_key = rsa_encrypt(random_key)

    h = {**DEFAULT_HEADERS}
    if client_type:
        h["clientType"] = client_type
    if version_code:
        h["versionCode"] = version_code
    h.update(AUTH_HEADERS)
    headers = {
        "currentTime": current_time,
        "sign": sign,
        "aesKey": aes_key,
        "clientType": h["clientType"],
        "versionCode": h["versionCode"],
        "lang": h["lang"],
        "timezone": h["timezone"],
        "deviceid": h["deviceid"],
        "token": h["token"],
        "adid": h["adid"],
        "content-type": "application/json",
    }

    headers = {k: v for k, v in headers.items() if v}

    url = f"{BASE_URL}{path}"

    proxies = {"http": "", "https": ""}

    if method.upper() == "GET":
        resp = requests.get(url, params=params or {}, headers=headers, timeout=timeout, proxies=proxies)
    else:
        resp = requests.post(url, json=data, headers=headers, timeout=timeout, proxies=proxies)

    return resp


def get_movie_detail(movie_id, category=1):
    return make_api_call("GET", "/cms/web/movieDrama/get",
                         params={"id": movie_id, "category": category}, timeout=8)


def get_play_info_ios(movie_id, episode_id, category=1, definition=None):
    params = {"id": movie_id, "episodeId": episode_id, "category": category}
    if definition:
        params["definition"] = definition
    return make_api_call("GET", "/cms/web/ios_h5/movieDrama/getPlayInfo", params=params)


def get_home(navigation_id=118, page=0, client_type=None, version_code=None):
    return make_api_call("GET", "/home/h5/getHome",
                         params={"navigationId": navigation_id, "page": page},
                         client_type=client_type, version_code=version_code)


LANG_MAP = {
    "en": "English",
    "id": "Indonesian",
    "in_ID": "Bahasa Indonesia",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ms": "Malay",
    "th": "Thai",
    "vi": "Vietnamese",
    "ar": "Arabic",
    "pt": "Portuguese",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ru": "Russian",
}

QUALITY_MAP = {
    "GROOT_HD": "1080P",
    "GROOT_SD": "720P",
    "GROOT_LD": "540P",
    "GROOT_FD": "360P",
}


def get_all_qualities(movie_id, episode_id, category=1):
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def fetch(q):
        try:
            r = get_play_info_ios(movie_id, episode_id, category, definition=q)
            if r.status_code != 200:
                return None
            d = r.json()
            if d.get("code") != "00000":
                return None
            url = d.get("data", {}).get("mediaUrl", "")
            if not url:
                return None
            return {"name": QUALITY_MAP.get(q, q), "url": url}
        except Exception:
            return None

    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(fetch, q): q for q in QUALITY_MAP}
        for f in as_completed(futures):
            r = f.result()
            if r:
                results.append(r)
    return results
