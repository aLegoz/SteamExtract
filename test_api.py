"""Test: Steam Web API endpoints for follower/wishlist data"""
import json, os, urllib.request, urllib.parse

TEST_APPID = 3041230
STEAM_API_KEY = os.environ.get("STEAM_API_KEY", "")

def get_json(url, params={}):
    full_url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(full_url, headers={"User-Agent": "SteamExtract/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

def show(label, r):
    print(f"\n{'='*50}\n=== {label} ===")
    print(json.dumps(r, indent=2, default=str)[:2000])

# IStoreService/GetAppInfo - extended app info including engagement
show("IStoreService.GetAppInfo",
    get_json("https://api.steampowered.com/IStoreService/GetAppInfo/v1/", {
        "key": STEAM_API_KEY,
        "appids": TEST_APPID,
    }))

# ISteamApps.GetAppList - see if any extra fields
show("IStoreService.GetAppList sample",
    get_json("https://api.steampowered.com/IStoreService/GetAppList/v1/", {
        "key": STEAM_API_KEY,
        "include_games": True,
        "include_dlc": False,
        "max_results": 3,
        "last_appid": TEST_APPID - 1,
    }))

# Try store review endpoint for context
show("Store reviews",
    get_json(f"https://store.steampowered.com/appreviews/{TEST_APPID}", {
        "json": 1,
        "language": "all",
        "purchase_type": "all",
        "num_per_page": 0,
    }))

# appdetails - what's in movies/screenshots for shovelware check
show("appdetails movies+screenshots",
    {k: v for k, v in (get_json("https://store.steampowered.com/api/appdetails", {
        "appids": TEST_APPID, "cc": "us", "l": "english"
    }).get(str(TEST_APPID), {}).get("data", {}) or {}).items()
     if k in ("movies", "screenshots", "recommendations", "categories", "developers", "publishers")})
