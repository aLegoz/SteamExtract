"""Test: find follower/subscriber count endpoints for a game by appid"""
import json
import os
import urllib.request
import urllib.parse

KEY = os.environ.get("STEAM_API_KEY", "")
TEST_APPID = 730  # CS2 — популярная игра, точно есть подписчики

def get(url, params={}, base=""):
    full_url = (base or "") + url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(full_url, headers={
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return json.loads(raw)
            except:
                return {"raw": raw[:500]}
    except Exception as e:
        return {"error": str(e)}

def show(label, r):
    print(f"\n=== {label} ===")
    print(json.dumps(r, indent=2)[:600])

# 1. Community followers via store API
show("store.steampowered.com/api/appdetails (full)",
    get("https://store.steampowered.com/api/appdetails",
        {"appids": TEST_APPID, "cc": "us", "l": "english", "filters": "basic,community_visible_stats,categories"}))

# 2. SteamSpy — owners + positive/negative reviews
show("steamspy.com appdetails",
    get("https://steamspy.com/api.php", {"request": "appdetails", "appid": TEST_APPID}))

# 3. Steam community hub AJAX — followers count
show("steamcommunity.com/games/XXX/ajaxgetfilteredactivities",
    get(f"https://steamcommunity.com/games/{TEST_APPID}/ajaxgetfilteredactivities",
        {"type": "1", "count": "1"}))

# 4. Steam broadcast game info — sometimes has viewer/follower data
show("store.steampowered.com broadcast info",
    get("https://store.steampowered.com/broadcast/ajaxgetbroadcastgameinfo",
        {"appid": TEST_APPID}))

# 5. IStoreService/GetAppInfo
show("IStoreService/GetAppInfo/v1",
    get("https://api.steampowered.com/IStoreService/GetAppInfo/v1/",
        {"key": KEY, "appids[0]": TEST_APPID}))

# 6. IStoreService/GetAppList with include_games
show("IStoreService/GetAppList/v1 (with_games)",
    get("https://api.steampowered.com/IStoreService/GetAppList/v1/",
        {"key": KEY, "include_games": 1, "max_results": 1, "last_appid": TEST_APPID - 1}))

# 7. Steam store apphoverview (used for hover cards)
show("store.steampowered.com/apphoverview",
    get(f"https://store.steampowered.com/apphoverview/{TEST_APPID}/",
        {"cc": "us", "l": "english", "review_score_preference": 0}))
