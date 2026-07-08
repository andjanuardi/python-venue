import requests
import base64
import hashlib
import time
import random
import string
import json
import os

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


def set_auth(token="", deviceid="", user_id="", user_name=""):
    SESSION["token"] = token
    SESSION["deviceid"] = deviceid
    SESSION["userId"] = user_id
    SESSION["userName"] = user_name
    SESSION["logged_in"] = bool(token)
    AUTH_HEADERS["token"] = token
    if deviceid:
        AUTH_HEADERS["deviceid"] = deviceid


def login(email, pwd):
    resp = make_api_call("POST", "/user/h5/auth/email/login",
                         data={"email": email, "pwd": pwd})
    data = resp.json()
    if data.get("code") == "00000":
        d = data.get("data", {})
        set_auth(
            token=d.get("token", ""),
            user_id=str(d.get("userId", "")),
            user_name=d.get("userName", ""),
            deviceid=d.get("deviceid", ""),
        )
        return d
    return None


def is_logged_in():
    return SESSION["logged_in"]


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


def make_api_call(method, path, params=None, data=None, client_type=None, version_code=None):
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

    if method.upper() == "GET":
        resp = requests.get(url, params=params or {}, headers=headers, timeout=30)
    else:
        resp = requests.post(url, json=data, headers=headers, timeout=30)

    return resp


# --- Endpoints for all client types (work with H5, ANDROID, IOS) ---

def get_movie_detail(movie_id, category=1):
    resp = make_api_call("GET", "/cms/web/movieDrama/get",
                         params={"id": movie_id, "category": category})
    return resp


def get_play_info(movie_id, episode_id, category=1):
    resp = make_api_call("GET", "/cms/web/h5/movieDrama/getPlayInfo",
                         params={"id": movie_id, "episodeId": episode_id, "category": category})
    return resp


def get_play_info_ios(movie_id, episode_id, category=1, definition=None):
    params = {"id": movie_id, "episodeId": episode_id, "category": category}
    if definition:
        params["definition"] = definition
    resp = make_api_call("GET", "/cms/web/ios_h5/movieDrama/getPlayInfo",
                         params=params)
    return resp


def get_all_qualities(movie_id, episode_id, category=1):
    import concurrent.futures
    defs = ["GROOT_HD", "GROOT_SD", "GROOT_LD", "GROOT_FD"]
    results = {}

    def fetch(d):
        r = get_play_info_ios(movie_id, episode_id, category, definition=d)
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == "00000":
                pi = data.get("data", {})
                subs = pi.get("subtitlingList") or []
                return d, (pi.get("mediaUrl", ""), pi.get("totalDuration"), subs)
        return d, ("", None, [])

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fetch, d): d for d in defs}
        for fut in concurrent.futures.as_completed(futs):
            d, result = fut.result()
            results[d] = result
    return results


def get_home(navigation_id=118, page=0):
    resp = make_api_call("GET", "/home/h5/getHome",
                         params={"navigationId": navigation_id, "page": page})
    return resp


def get_navigation_bar():
    resp = make_api_call("GET", "/home/h5/navigationBar", params={})
    return resp


def get_popular_list(page=0, size=20):
    resp = make_api_call("GET", "/cms/h5/popular/list", params={"page": page, "size": size})
    return resp


def get_video_info(video_id):
    resp = make_api_call("GET", "/cms/web/video/info", params={"id": video_id})
    return resp


def get_rank_navigation():
    resp = make_api_call("GET", "/cms/h5/recommendRanking/navigationBar", params={})
    return resp


def get_rank_more(ranking_id, page=0, size=20):
    resp = make_api_call("POST", "/cms/h5/recommendRanking/more/v3",
                         data={"rankingId": ranking_id, "page": page, "size": size})
    return resp


def get_album_detail(album_id, page=0, size=20):
    resp = make_api_call("GET", "/cms/web/album/detail",
                         params={"id": album_id, "page": page, "size": size})
    return resp


def search_with_keyword(keyword, page=0, size=20):
    resp = make_api_call("POST", "/cms/v2/h5/search/searchWithKeyWord",
                         data={"keyword": keyword, "page": page, "size": size})
    return resp


def search_lenovo(keyword, size=10):
    resp = make_api_call("POST", "/cms/v2/h5/search/searchLenovo",
                         data={"keyword": keyword, "size": size})
    return resp


# --- Auth / Account ---

def query_user_info():
    resp = make_api_call("GET", "/user/h5/auth/queryUserInfo", params={})
    return resp


def get_vip_info():
    resp = make_api_call("GET", "/user/vip/h5/info", params={})
    return resp


# --- App-specific endpoints (clientType ANDROID/IOS) ---

def get_app_goods_list():
    resp = make_api_call("GET", "/commodity/app/goods/h5/list", params={}, client_type="ANDROID")
    return resp


def get_app_article_detail(article_id):
    resp = make_api_call("GET", "/cms/app/article/detail",
                         params={"id": article_id}, client_type="ANDROID")
    return resp


def get_app_article_system_detail(article_id):
    resp = make_api_call("GET", "/cms/app/article/system/detail",
                         params={"id": article_id}, client_type="ANDROID")
    return resp


def get_app_group_random_id(followed=False):
    resp = make_api_call("GET", "/cms/app/group/queryRandomId",
                         params={"followed": followed}, client_type="ANDROID")
    return resp


def get_app_download_url():
    resp = make_api_call("GET", "/config/app/apk/downloadUrl", params={}, client_type="ANDROID")
    return resp


def get_app_country_info():
    resp = make_api_call("GET", "/config/app/countryInfo", params={}, client_type="ANDROID")
    return resp


def get_app_ip():
    resp = make_api_call("GET", "/config/app/ip/get", params={}, client_type="ANDROID")
    return resp


def get_app_pay_channel_list():
    resp = make_api_call("GET", "/order/app/pay_channel/list", params={}, client_type="ANDROID")
    return resp


def get_app_gift_banner():
    resp = make_api_call("GET", "/gift/app/h5/bannerConfigInfo", params={}, client_type="ANDROID")
    return resp


def submit_vip_code(vip_code):
    resp = make_api_call("POST", "/user/app/vipcode/submitVipCode",
                         data={"vipCode": vip_code}, client_type="ANDROID")
    return resp


# --- Movie DB (unchanged) ---

MOVIE_DB_PATH = os.path.join(os.path.dirname(__file__), "movie_db.json")
_movie_cache = None


def load_movie_db():
    global _movie_cache
    if _movie_cache is not None:
        return _movie_cache
    if os.path.exists(MOVIE_DB_PATH):
        with open(MOVIE_DB_PATH, encoding="utf-8") as f:
            _movie_cache = json.load(f)
    else:
        _movie_cache = []
    return _movie_cache


def refresh_movie_db():
    global _movie_cache
    _movie_cache = None
    return load_movie_db()


def save_movie_db(movies):
    global _movie_cache
    _movie_cache = movies
    with open(MOVIE_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(movies, f, indent=2, ensure_ascii=False)


def search_db(keyword):
    movies = load_movie_db()
    kw = keyword.lower().strip()
    if not kw:
        return movies
    return [m for m in movies if kw in m.get("title", "").lower()
            or kw in m.get("alias", "").lower()
            or any(kw in a.lower() for a in m.get("area", []))]


def filter_db(year=None, area=None, tag=None, sort="id"):
    movies = load_movie_db()
    if year:
        movies = [m for m in movies if str(m.get("year", "")) == str(year)]
    if area:
        movies = [m for m in movies if any(area.lower() in a.lower() for a in m.get("area", []))]
    if tag:
        movies = [m for m in movies if any(tag.lower() in t.lower() for t in m.get("tags", []))]
    if sort == "year":
        movies.sort(key=lambda m: m.get("year") or "", reverse=True)
    elif sort == "id":
        movies.sort(key=lambda m: int(m.get("id") or 0))
    return movies
