"""Test: SteamDB GetGraphFollowersLoggedIn endpoint"""
import json
import os
import urllib.request
import urllib.parse

TEST_APPID = 3041230
STEAMDB_COOKIE = os.environ.get("STEAMDB_COOKIE", "")

def get(url, params={}, headers={}):
    full_url = url + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(full_url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": f"https://steamdb.info/app/{TEST_APPID}/",
        "X-Requested-With": "XMLHttpRequest",
        **headers,
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            print(f"Status: {resp.status}")
            try:
                return json.loads(raw)
            except:
                return {"raw": raw[:1000]}
    except Exception as e:
        return {"error": str(e)}

def show(label, r):
    print(f"\n{'='*50}")
    print(f"=== {label} ===")
    print(json.dumps(r, indent=2)[:1000])

# 1. Без куков
show("Without auth",
    get(f"https://steamdb.info/api/GetGraphFollowersLoggedIn/",
        {"appid": TEST_APPID}))

# 2. С куками (если заданы)
if STEAMDB_COOKIE:
    show("With cookie",
        get(f"https://steamdb.info/api/GetGraphFollowersLoggedIn/",
            {"appid": TEST_APPID},
            {"Cookie": STEAMDB_COOKIE}))
else:
    print("\n[STEAMDB_COOKIE not set — add it as GitHub secret to test with auth]")

# 3. Попробуем незалогиненный аналог
show("GetGraphFollowers (no login?)",
    get(f"https://steamdb.info/api/GetGraphFollowers/",
        {"appid": TEST_APPID}))
