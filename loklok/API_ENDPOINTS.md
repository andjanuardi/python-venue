# API Endpoints — Loklok (h5.despseek.com)

> Hasil analisis dari JavaScript bundle Nuxt website `https://h5.despseek.com/`.
> Platform streaming Loklok dengan berbagai fitur: video on-demand, live streaming, social features, games.

## Base URL

```
https://h5-api.hehekang.com
```

Semua endpoint REST API menggunakan base URL ini kecuali disebutkan lain.

## Authentication & Signing

Setiap request HARUS menyertakan header signing berikut:

| Header | Nilai | Keterangan |
|--------|-------|------------|
| `currentTime` | `str(int(time.now() * 1000))` | Timestamp milidetik |
| `aesKey` | `RSA(PUBLIC_KEY, random16char)` | Random key 16 char, dienkripsi RSA dengan public key Loklok |
| `sign` | `MD5(AES_ECB(time + base64(params), random16char))` | Tanda tangan request |
| `clientType` | `H5` | Tipe client |
| `versionCode` | `32` | Versi aplikasi |
| `lang` | `en` | Bahasa (en, zh, id, dll) |
| `timezone` | `GMT+7` | Zona waktu |
| `deviceid` | `string` | ID perangkat (dari login) |
| `token` | `string` | Token autentikasi (dari login) |
| `adid` | `string` | Advertising ID (opsional) |

**Proses signing:**
1. Generate random 16 karakter → `randomKey`
2. RSA encrypt `randomKey` dengan public key → `aesKey` header
3. Serialize params (sorted by key) → base64 → gabung dengan `currentTime`
4. AES-ECB encrypt hasilnya dengan `randomKey`, lalu MD5 hash → `sign` header

**Public Key (RSA 1024):**
```
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC7GW1zgx9/ssgCjoZhuCvISy5N
s9T2UgAzjJqS2uTGuCVtZsN3TE5wd4OIeiVG2TVDH2Gxlzrxd5jg7P6IiUKqsliS
dZxx/ceqLDawKgvO8mJ+hJJsuIxSL7Bi6T0p+xH6ibw4orGfCFUJhGryE9hqp9qT
RiHOMvgC2si1VqrgaQIDAQAB
```

## Domain Terkait

| Domain | Fungsi |
|--------|--------|
| `h5.loklok.site` | Web app utama (Nuxt SPA) |
| `h5-api.hehekang.com` | **Backend API server utama** |
| `h5.decryptplan.com` | Alternative host |
| `h5.netpop.app` | Alternative host |
| `js1.dutun.cc` | CDN JS/CSS Nuxt bundles (`/loklok/3.23.70/_nuxt/`) |
| `img.loklok.video` | CDN gambar statis |
| `static.loklok.video` | Static assets gambar |
| `img.snssb.com` | Cover video dan thumbnail |
| `ali-cdn-preview-web.snssb.com` | CDN video preview |
| `netpop-e792a-default-rtdb.asia-southeast1.firebasedatabase.app` | Firebase Realtime DB |
| `checkout-sdk1.uat.useepay.com` | Useepay payment SDK |
| `www.paypal.com/sdk/js` | PayPal SDK |
| `fpjs.dev/pro` | FingerprintJS |
| `arms-retcode.aliyuncs.com` | Alibaba ARMS monitoring |

---

# Endpoints

## Account / Biscuit

### `POST /account/h5/biscuit/exchange/baseInfo`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `POST /account/h5/biscuit/exchange/createOrder`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e||{`
: Note:    [unknown]

## Activity

### `GET /activity/game/h5/doubleDan/getAnchorRankList`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||[]`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||[]`
: Note:    [unknown]

### `GET /activity/game/h5/doubleDan/getGuildRankList`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||[]`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||[]`
: Note:    [unknown]

### `GET /activity/game/h5/doubleDan/getTask`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||[]`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||[]`
: Note:    [unknown]

### `GET /activity/game/h5/doubleDan/getUserRankList`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||[]`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||[]`
: Note:    [unknown]

### `GET /activity/game/h5/halloween/ranking/list`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `GET /activity/game/h5/honorDuel/list`
: Params:  none
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||[]`)
: JS:      tanpa parameter (hardcoded di JS) → `e=>e.data||[]`
: Note:    [unknown]

### `GET /activity/game/h5/honorDuel/rank/list`
: Params:  none
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||[]`)
: JS:      tanpa parameter (hardcoded di JS) → `e=>e.data||[]`
: Note:    [unknown]

### `GET /activity/game/h5/live/queryUserLive`
: Params:  e||null
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter: `e||null` → `e=>e.data||{`
: Note:    [unknown]

### `GET /activity/game/h5/panjat/ranking/list`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `POST /activity/game/h5/panjatPinang/bulletChat/list`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `POST /activity/game/h5/panjatPinang/roomTask`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `POST /activity/game/h5/panjatPinang/roomTask/draw`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `POST /activity/game/h5/panjatPinang/userTask`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e,key:"userTask"`)
: JS:      parameter dari caller (Vue komponen) → `e=>e,key:"userTask"`
: Note:    [unknown]

### `POST /activity/game/h5/panjatPinang/userTask/receive`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `GET /activity/game/h5/ramadan/sing/list`
: Params:  {type:0}
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter: `{type:0}` → `e=>e.data||{`
: Note:    [unknown]

### `POST /activity/game/h5/ramadan/sing/vote`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e,key:t`)
: JS:      parameter dari caller (Vue komponen) → `e=>e,key:t`
: Note:    [unknown]

### `GET /activity/game/h5/share/accumulateLotteryPrizeList`
: Params:  none
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data`)
: JS:      tanpa parameter (hardcoded di JS) → `e=>e.data`
: Note:    [unknown]

### `GET /activity/game/h5/share/activityInfo`
: Params:  none
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data`)
: JS:      tanpa parameter (hardcoded di JS) → `e=>e.data`
: Note:    [unknown]

### `GET /activity/game/h5/share/getLotteryStatus`
: Params:  none
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data`)
: JS:      tanpa parameter (hardcoded di JS) → `e=>e.data`
: Note:    [unknown]

### `GET /activity/game/h5/share/lottery`
: Params:  none
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      tanpa parameter (hardcoded di JS) → `e=>e`
: Note:    [unknown]

### `GET /activity/game/h5/share/lotteryPrizeList`
: Params:  none
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data`)
: JS:      tanpa parameter (hardcoded di JS) → `e=>e.data`
: Note:    [unknown]

### `GET /activity/game/h5/share/lotteryRecord`
: Params:  none
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data`)
: JS:      tanpa parameter (hardcoded di JS) → `e=>e.data`
: Note:    [unknown]

### `GET /activity/game/h5/share/prizeUsage`
: Params:  none
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data`)
: JS:      tanpa parameter (hardcoded di JS) → `e=>e.data`
: Note:    [unknown]

### `GET /activity/game/h5/share/receivePrize`
: Params:  {prizeId:e}
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter: `{prizeId:e}` → `e=>e`
: Note:    [unknown]

### `GET /activity/game/h5/share/share`
: Params:  none
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      tanpa parameter (hardcoded di JS) → `e=>e`
: Note:    [unknown]

### `GET /activity/game/h5/share/winners`
: Params:  none
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data`)
: JS:      tanpa parameter (hardcoded di JS) → `e=>e.data`
: Note:    [unknown]

### `GET /activity/game/h5/template/honor/queryList`
: Params:  {activityId:e}
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter: `{activityId:e}` → `e=>e.data||{`
: Note:    [unknown]

### `GET /activity/game/h5/template/queryList`
: Params:  {activityId:e}
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter: `{activityId:e}` → `e=>e.data||{`
: Note:    [unknown]

## Auth & User Account

### `POST /order/h5/vip/pingpong/wallet/authorization/applyToken`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `POST /order/h5/vip/pingpong/wallet/authorization/prepare`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `POST /user/auth/h5/forgot/captcha/check`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e.code==SERVER_STATUS$1.SUCCESS`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.code==SERVER_STATUS$1.SUCCESS`
: Note:    [unknown]

### `POST /user/auth/h5/forgot/captcha/send`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e.code==SERVER_STATUS$1.SUCCESS`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.code==SERVER_STATUS$1.SUCCESS`
: Note:    [unknown]

### `POST /user/auth/h5/pwd/reset`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e.code==SERVER_STATUS$1.SUCCESS`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.code==SERVER_STATUS$1.SUCCESS`
: Note:    [unknown]

### `POST /user/h5/auth/email/captcha/send`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e.code==SERVER_STATUS$1.SUCCESS`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.code==SERVER_STATUS$1.SUCCESS`
: Note:    [unknown]

### `POST /user/h5/auth/email/login`
: Params:  none
: Body:    {"email":"str","pwd":"str"}
: Response: {"code":"00000","data":{"token","userId","userName","deviceid"}}
: JS:      parameter dari caller (Vue komponen) → `e=>e.code==SERVER_STATUS$1.SUCCESS&&e.data`
: Note:    Login via email. Field password adalah `pwd`, bukan `password`.

### `POST /user/h5/auth/email/register`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e.code==SERVER_STATUS$1.SUCCESS&&e.data`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.code==SERVER_STATUS$1.SUCCESS&&e.data`
: Note:    [unknown]

### `GET /user/h5/auth/email/register/check`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.code==SERVER_STATUS$1.SUCCESS&&e.data`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.code==SERVER_STATUS$1.SUCCESS&&e.data`
: Note:    [unknown]

### `GET /user/h5/auth/queryUserInfo`
: Params:  none
: Body:    none
: Response: {"code":"00000","data":{"userId","userName","email","avatar"}}
: JS:      tanpa parameter (hardcoded di JS) → `e=>e.code==SERVER_STATUS$1.SUCCESS&&e.data`
: Note:    Data user yang sedang login.

### `POST /user/h5/auth/third/login`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

## Billboard / Ranking

### `GET /live/h5/billboard/charmBillboard/day`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `GET /live/h5/billboard/charmBillboard/month`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `GET /live/h5/billboard/charmBillboard/week`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `GET /live/h5/billboard/gloryBillboard/day`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `GET /live/h5/billboard/gloryBillboard/month`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `GET /live/h5/billboard/gloryBillboard/week`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

## Commodity / Goods

### `GET /commodity/app/goods/h5/list`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||[]`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||[]`
: Note:    [unknown]

### `GET /commodity/h5/banner/get`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||[]`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||[]`
: Note:    [unknown]

### `GET /commodity/h5/coinAgency/virtualCoin/list`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||[]`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||[]`
: Note:    [unknown]

### `POST /commodity/h5/preferentialLog/ack`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `GET /commodity/h5/virtualCoin/goodsWithPassport`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `GET /commodity/h5/virtualCoin/queryGoodsInfo`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||null`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||null`
: Note:    [unknown]

### `GET /commodity/h5/virtualCoin/website/list`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||[]`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||[]`
: Note:    [unknown]

## Config & System

### `GET /api/config`
: Params:  [unknown]
: Body:    none
: Response: [unknown]
: JS:      parameter dari caller (Vue komponen)
: Note:    [unknown]

### `GET /api/getIp`
: Params:  [unknown]
: Body:    none
: Response: [unknown]
: JS:      parameter dari caller (Vue komponen)
: Note:    [unknown]

### `GET /config/app/apk/downloadUrl`
: Params:  none
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      tanpa parameter (hardcoded di JS) → `e=>e.data||{`
: Note:    [unknown]

### `GET /config/app/countryInfo`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data`
: Note:    [unknown]

### `GET /config/app/ip/get`
: Params:  none
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data`)
: JS:      tanpa parameter (hardcoded di JS) → `e=>e.data`
: Note:    [unknown]

### `GET /config/h5/downloadPrompt/enabled`
: Params:  none
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||null`)
: JS:      tanpa parameter (hardcoded di JS) → `e=>e.data||null`
: Note:    [unknown]

## Gift

### `GET /gift/app/h5/bannerConfigInfo`
: Params:  e
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||[]`)
: JS:      parameter: `e)` → `e=>e.data||[]`
: Note:    [unknown]

## Guild / Anchor (Live Streaming)

### `POST /live/h5/guild/center/anchor/export2Email`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `POST /live/h5/guild/center/anchor/page`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `POST /live/h5/guild/center/data`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `GET /live/h5/guild/center/queryLiveExist`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e||{`
: Note:    [unknown]

### `POST /live/h5/guild/center/room`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `POST /user/h5/guild/center/anchor/list`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `POST /user/h5/guild/center/anchor/remove`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e||{`
: Note:    [unknown]

### `GET /user/h5/guild/center/dot/get`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e||{`
: Note:    [unknown]

### `POST /user/h5/guild/center/exitApplyList`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{content:[],totalElements:0`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{content:[],totalElements:0`
: Note:    [unknown]

### `POST /user/h5/guild/center/joinApplyList`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{content:[],totalElements:0`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{content:[],totalElements:0`
: Note:    [unknown]

### `POST /user/h5/guild/center/manager/cancel`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e||{`
: Note:    [unknown]

### `POST /user/h5/guild/center/manager/empower`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e||{`
: Note:    [unknown]

### `POST /user/h5/guild/center/manager/list`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `GET /user/h5/guild/center/queryGuildInfo`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `POST /user/h5/guild/center/role`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `POST /user/h5/guild/center/saveCardInfo`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `POST /user/h5/guild/center/saveGuildName`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>!(!e||e.code!==SERVER_STATUS$1.SUCCESS)`)
: JS:      parameter dari caller (Vue komponen) → `e=>!(!e||e.code!==SERVER_STATUS$1.SUCCESS)`
: Note:    [unknown]

### `POST /user/h5/guild/exitGuildApply`
: Params:  none
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>!(!e||e.code!==SERVER_STATUS$1.SUCCESS)&&e`)
: JS:      tanpa parameter (hardcoded di JS) → `e=>!(!e||e.code!==SERVER_STATUS$1.SUCCESS)&&e`
: Note:    [unknown]

### `GET /user/h5/guild/findUserGuildJoinInfo`
: Params:  none
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||[]`)
: JS:      tanpa parameter (hardcoded di JS) → `e=>e.data||[]`
: Note:    [unknown]

### `POST /user/h5/guild/inviteUser`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e||{`
: Note:    [unknown]

### `GET /user/h5/guild/queryUserInfo`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `POST /user/h5/guild/updateInviteOrApplyRecord`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

## Home / Navigation

### `GET /home/h5/getHome`
: Params:  `navigationId` (int, required), `page` (int, default 0)
: Body:    none
: Response: {"code":"00000","data":{"navigationId","page","recommendItems"}}
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{recommendItems:[]`
: Note:    Halaman utama. `navigationId=118` hanya mengembalikan 2 BANNER item.

### `GET /home/h5/getHomeRank`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||[]`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||[]`
: Note:    [unknown]

### `GET /home/h5/navigationBar`
: Params:  none
: Body:    none
: Response: {"code":"00000","data":{"navigationBarItemList"}}
: JS:      tanpa parameter (hardcoded di JS) → `e=>e.data||{navigationBarItemList:[]`
: Note:    Hanya 1 item: id=118, name="Home".

## Miscellaneous

### `GET /user/h5/abTest`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `GET /user/h5/popup/expiredVipDiscount/info`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||null`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||null`
: Note:    [unknown]

## Payment

### `POST /order/app/pay/payPal/coinAgency/sign`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `POST /order/app/pay/payPal/sign`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `POST /order/app/pay/payermax/coinAgency/order`
: Params:  e
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e||{`)
: JS:      parameter: `e)` → `e=>e||{`
: Note:    [unknown]

### `POST /order/app/pay/payermax/order`
: Params:  e
: Body:    [unknown]
: Response: [unknown]
: JS:      parameter: `e)`
: Note:    [unknown]

### `GET /order/app/pay_channel/list`
: Params:  e
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||[]`)
: JS:      parameter: `e)` → `e=>e.data||[]`
: Note:    [unknown]

### `GET /order/h5/pay_channel/list`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||[]`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||[]`
: Note:    [unknown]

### `GET /order/h5/payermax/getOrderStatus`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data`
: Note:    [unknown]

### `POST /order/h5/virtualCoin/aggregation/prePay`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `POST /order/h5/virtualCoin/alipay/prePay`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `POST /order/h5/virtualCoin/pingpong/coinAgency/prePay `
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `POST /order/h5/virtualCoin/pingpong/prePay`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `GET /order/h5/virtualCoin/user/deliverStatus`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data`
: Note:    [unknown]

### `GET /user/info/h5pay`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

## User Behavior

### `POST /user/behavior/h5/favorites/add`
: Params:  none
: Body:    [unknown]
: Response: `e.data` (JS transform)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data`
: Note:    Tambah favorit.

### `POST /user/behavior/h5/favorites/delete`
: Params:  none
: Body:    [unknown]
: Response: `e.data` (JS transform)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data`
: Note:    Hapus favorit.

### `GET /user/behavior/h5/star/signin/detail`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `POST /user/behavior/h5/star/signin/resign`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e||{code:"",msg:""`)
: JS:      parameter dari caller (Vue komponen) → `e=>e||{code:"",msg:""`
: Note:    [unknown]

### `GET /user/behavior/h5/star/signin/signIn/calendar`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

## User Task / Point / StarPK

### `GET /usertask/h5/passport/queryInfo`
: Params:  e
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e||{`)
: JS:      parameter: `e)` → `e=>e||{`
: Note:    [unknown]

### `POST /usertask/h5/passport/reward/receive`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e||{`
: Note:    [unknown]

### `GET /usertask/h5/point/task/starSignIn/query`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `GET /usertask/h5/starpk/account/info`
: Params:  none
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      tanpa parameter (hardcoded di JS) → `e=>e.data||{`
: Note:    [unknown]

### `GET /usertask/h5/starpk/history/list`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `GET /usertask/h5/starpk/sponsor/list`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `POST /usertask/h5/starpk/task/do`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `GET /usertask/h5/starpk/task/list`
: Params:  none
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      tanpa parameter (hardcoded di JS) → `e=>e.data||{`
: Note:    [unknown]

### `POST /usertask/h5/starpk/task/signIn`
: Params:  none
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      tanpa parameter (hardcoded di JS) → `e=>e`
: Note:    [unknown]

### `POST /usertask/h5/starpk/user/vote`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `GET /usertask/h5/starpk/vote/list`
: Params:  none
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      tanpa parameter (hardcoded di JS) → `e=>e.data||{`
: Note:    [unknown]

## VIP & Subscription

### `GET /commodity/h5/market/vip/goods/detail`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||null`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||null`
: Note:    [unknown]

### `GET /commodity/h5/market/vip/goods/goodsLongUrl`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `GET /commodity/h5/market/vip/goods/list`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `GET /commodity/h5/market/vip/goods/most_favorable`
: Params:  none
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data`)
: JS:      tanpa parameter (hardcoded di JS) → `e=>e.data`
: Note:    [unknown]

### `GET /commodity/h5/market/vip/goods/v2/list`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `GET /commodity/h5/market/vip/goods/v3/list`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `GET /commodity/h5/vip/privilege/rightsInterests`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `POST /order/h5/vip/aggregation/prePay`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `POST /order/h5/vip/alipay/prePay`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `GET /order/h5/vip/getUseeSessionInfo`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data`
: Note:    [unknown]

### `GET /order/h5/vip/orderStatus`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data`
: Note:    [unknown]

### `POST /order/h5/vip/payermax/purchase`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `POST /order/h5/vip/payermax/subscription`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `POST /order/h5/vip/pingpong/prePay`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `POST /order/h5/vip/pingpong/wallet/payment/prePay`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `POST /order/h5/vip/pingpong/wallet/payment/unifiedPay`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `POST /order/h5/vip/subscription/cancel`
: Params:  e
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter: `e)` → `e=>e`
: Note:    [unknown]

### `GET /order/h5/vip/user/deliverStatus`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data`
: Note:    [unknown]

### `GET /order/h5/vip/user/subscribe_goods`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||[]`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||[]`
: Note:    [unknown]

### `POST /user/app/vipcode/submitVipCode`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `GET /user/vip/h5/all`
: Params:  null
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||null`)
: JS:      parameter: `null)` → `e=>e.data||null`
: Note:    [unknown]

### `GET /user/vip/h5/info`
: Params:  e
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||[]`)
: JS:      parameter: `e)` → `e=>e.data||[]`
: Note:    [unknown]

### `POST /user/vip/h5/submitVipCode`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

## Video / Drama / Content (CMS)

### `GET /cms/app/article/detail`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.code!==SERVER_STATUS$1.SUCCESS?new Error(e.msg):e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.code!==SERVER_STATUS$1.SUCCESS?new Error(e.msg):e.data||{`
: Note:    [unknown]

### `GET /cms/app/article/system/detail`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e`)
: JS:      parameter dari caller (Vue komponen) → `e=>e`
: Note:    [unknown]

### `GET /cms/app/group/queryRandomId`
: Params:  {followed:e}
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter: `{followed:e}` → `e=>e.data||{`
: Note:    [unknown]

### `GET /cms/h5/game/article/detail`
: Params:  [unknown]
: Body:    none
: Response: `{code: "00000", data: ...}` (transform: `e=>e.code!==SERVER_STATUS$1.SUCCESS?new Error(e.msg):e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.code!==SERVER_STATUS$1.SUCCESS?new Error(e.msg):e.data||{`
: Note:    [unknown]

### `GET /cms/h5/popular/list`
: Params:  `page` (int), `size` (int)
: Body:    none
: Response: {"code":"00000","data":[{name, cover}]}
: JS:      tanpa parameter (hardcoded di JS) → `e=>e.data`
: Note:    List populer — hanya name+cover, tanpa ID.

### `POST /cms/h5/recommendRanking/more/v3`
: Params:  none
: Body:    {"rankingId","page","size"}
: Response: ERROR B0001 — The given id must not be null
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||[]`
: Note:    Endpoint broken server-side.

### `GET /cms/h5/recommendRanking/navigationBar`
: Params:  none
: Body:    none
: Response: {"code":"00000","data":[{rankingGroupId,rankingGroupTitle,rankingConfigs}]}
: JS:      tanpa parameter (hardcoded di JS) → `e=>e.data||[]`
: Note:    Kategori ranking.

### `POST /cms/v2/h5/search/searchDrama`
: Params:  [unknown]
: Body:    [unknown]
: Response: `{code: "00000", data: ...}` (transform: `e=>e.data||{`)
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    [unknown]

### `POST /cms/v2/h5/search/searchLenovo`
: Params:  none
: Body:    {"keyword","size"}
: Response: {"code":"00000","data":{"searchResults":[]}}
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{searchResults:[]`
: Note:    Autocomplete — selalu kosong.

### `POST /cms/v2/h5/search/searchWithKeyWord`
: Params:  none
: Body:    {"keyword","page","size"}
: Response: {"code":"00000","data":[]}
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||[]`
: Note:    Search — selalu data kosong.

### `GET /cms/web/album/detail`
: Params:  `id` (int), `page` (int), `size` (int)
: Body:    none
: Response: {"code":"00000","data":{"name","items"}}
: JS:      parameter dari caller (Vue komponen) → `e=>e.data||{`
: Note:    Album. items: [].

### `GET /cms/web/movieDrama/get`
: Params:  `id` (int, movie/drama ID), `category` (int, 0/1)
: Body:    none
: Response: `{"code":"00000","data":{"episodeVo":[{"subtitlingList":[...]}]}}`
: Note:    **Sumber utama subtitle.** Setiap item `episodeVo[]` memiliki `subtitlingList[]`. Didokumentasikan dari proyek filmhot (archived) dan verifikasi langsung. Subtitle di-cache di CDN `subtitles.netpop.app`.

### `GET /cms/web/h5/movieDrama/getPlayInfo`
: Params:  `id` (int, movie/drama ID), `episodeId` (int), `category` (int, 0/1)
: Body:    none
: Response: `{"code":"00000","data":{"mediaUrl","totalDuration","subtitlingList":[...],"definitionList":[...],"currentDefinition":"GROOT_FD","freeDuration":300}}`
: Note:    Play info via H5 client. Return **preview-only** (15s, freeDuration 300s, size kecil, CDN preview). `subtitlingList` berisi daftar subtitle (fallback jika dari detail kosong).

### `GET /cms/web/ios_h5/movieDrama/getPlayInfo`
: Params:  `id` (int), `episodeId` (int), `category` (int, 0/1), `definition` (string, optional: GROOT_HD/SD/LD/FD)
: Body:    none
: Response: `{"code":"00000","data":{"mediaUrl","totalDuration","subtitlingList":[...],"definitionList":[...],"currentDefinition":"GROOT_SD","freeDuration":null}}`
: JS:      `fetchGetPlayInfoIos=e=>request.get("/cms/web/ios_h5/movieDrama/getPlayInfo",e)`
: Note:    Play info via iOS endpoint. Return **full episode** (durasi penuh, size besar, CDN play). `subtitlingList` mungkin kosong jika tanpa login.

**Response field `subtitlingList[]`:**
: Setiap item memiliki struktur:
: - `subtitlingUrl` (string) — URL file subtitle (format SRT/VTT, CDN `subtitles.netpop.app`)
: - `language` (string) — Nama bahasa display (e.g., "English", "Bahasa Indonesia")
: - `languageAbbr` (string) — Kode bahasa (e.g., "en", "in_ID", "vi", "zh_CN")
: - `translateType` (int) — 0 = original/manual, 1 = auto-translate
: Sumber: `episodeVo[index].subtitlingList` dari `/cms/web/movieDrama/get` (primary), fallback ke playInfo. CLI prioritaskan `in_ID` > `en`, skip sisanya.

**Response field `definitionList[]`:**
: Setiap item:
: - `code` (string) — "GROOT_HD", "GROOT_SD", "GROOT_LD", "GROOT_FD"
: - `description` (string) — "1080P", "720P", dll

---

## Catatan Teknis

- **Auth:** Semua request memerlukan header signing (`currentTime`, `sign`, `aesKey`). Token autentikasi ditambahkan setelah login.
- **Error codes:** `00000` = sukses, `B0001` = bad request/parameter error, `B0300` = resource not found, `A0001` = resource does not exist.
- **JS param types:** `none` = endpoint tidak menerima parameter (hardcoded di JS), `caller` = parameter ditentukan oleh komponen Vue (perlu inspect lazy chunk).
- **Firebase:** `netpop-e792a-default-rtdb.asia-southeast1.firebasedatabase.app` digunakan sebagai realtime database.
- **Transform:** Fungsi `transform:` pada definisi JS menunjukkan bagaimana response API diolah sebelum dikembalikan ke komponen.
- **Payment Gateway:** Useepay, PayPal, Alipay, Pingpong, Payermax.
- **File Upload:** Menggunakan Qiniu Cloud.
- **Monitoring:** Alibaba ARMS.
- **Device Fingerprinting:** FingerprintJS.

> **Disclaimer:** Dokumentasi ini berdasarkan hasil reverse engineering dari file JavaScript bundle publik dan pengujian langsung. Beberapa endpoint mungkin memerlukan autentikasi, parameter spesifik, atau konteks tertentu. Parameter untuk endpoint `caller` hanya bisa diketahui dengan inspect lazy-loaded Nuxt chunk. Gunakan dengan bijak dan sesuai ketentuan hukum yang berlaku.
