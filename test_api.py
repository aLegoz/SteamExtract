"""Quick test: what Steam API endpoints are available with an API key?"""
import json
import os
import urllib.request
import urllib.parse

KEY = os.environ.get("STEAM_API_KEY", "")
TEST_APPID = 730  # CS2

def get(url, params={}):
    full_url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(full_url, headers={"User-Agent": "SteamExtract/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

print("=== IStoreService/GetAppDetails ===")
r = get("https://api.steampowered.com/IStoreService/GetAppDetails/v1/", {"key": KEY, "appids": TEST_APPID})
print(json.dumps(r, indent=2)[:800])

print("\n=== IWishlistService/GetWishlist (game) ===")
r = get("https://api.steampowered.com/IWishlistService/GetWishlist/v1/", {"key": KEY, "appid": TEST_APPID})
print(json.dumps(r, indent=2)[:800])

print("\n=== ISteamUserStats/GetNumberOfCurrentPlayers ===")
r = get("https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/", {"key": KEY, "appid": TEST_APPID})
print(json.dumps(r, indent=2)[:800])

print("\n=== IStoreService/GetMostPopularTags ===")
r = get("https://api.steampowered.com/IStoreService/GetMostPopularTags/v1/", {"key": KEY})
print(json.dumps(r, indent=2)[:400])

print("\n=== ISteamApps/GetAppList (with key) ===")
r = get("https://api.steampowered.com/ISteamApps/GetAppList/v2/", {"key": KEY})
print(str(r)[:300])
