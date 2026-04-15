"""Test: bypass Cloudflare on SteamDB using curl_cffi"""
import json
import os

TEST_APPID = 3041230

try:
    from curl_cffi import requests

    session = requests.Session(impersonate="chrome")

    def get(url, params={}):
        try:
            r = session.get(url, params=params, timeout=15)
            print(f"  HTTP {r.status_code}")
            try:
                return r.json()
            except:
                return {"raw": r.text[:800]}
        except Exception as e:
            return {"error": str(e)}

    def show(label, r):
        print(f"\n{'='*50}\n=== {label} ===")
        print(json.dumps(r, indent=2)[:800])

    show("GetGraphFollowers (no auth)",
        get("https://steamdb.info/api/GetGraphFollowers/", {"appid": TEST_APPID}))

    show("GetGraphFollowersLoggedIn (no auth)",
        get("https://steamdb.info/api/GetGraphFollowersLoggedIn/", {"appid": TEST_APPID}))

    # Если первый вариант вернёт данные — значит Cloudflare был единственным барьером
    show("App info page check",
        get(f"https://steamdb.info/app/{TEST_APPID}/"))

except ImportError:
    print("curl_cffi not installed — check requirements")
