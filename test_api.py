"""Test: find follower data via Steam CM with real login"""
import json, os
from steam.client import SteamClient

TEST_APPID = 3041230
STEAM_USER = os.environ.get("STEAM_USER", "")
STEAM_PASS = os.environ.get("STEAM_PASS", "")

client = SteamClient()

if STEAM_USER and STEAM_PASS:
    print(f"Logging in as {STEAM_USER}...")
    client.cli_login(username=STEAM_USER, password=STEAM_PASS)
else:
    print("Anonymous login...")
    client.anonymous_login()

def try_um(method, body={}):
    try:
        resp = client.send_um_and_wait(method, body, timeout=10)
        if resp is None:
            return {"result": "timeout/no response"}
        body_obj = resp.body
        try:
            result = {}
            for field in body_obj.DESCRIPTOR.fields:
                val = getattr(body_obj, field.name, None)
                result[field.name] = str(val)
            return result
        except:
            return {"raw": str(body_obj)[:500]}
    except Exception as e:
        return {"error": type(e).__name__, "msg": str(e)}

def show(label, r):
    print(f"\n{'='*50}\n=== {label} ===")
    print(json.dumps(r, indent=2, default=str)[:1000])

# Store.GetFollowerCount - needs appid
show("Store.GetFollowerCount#1",
    try_um("Store.GetFollowerCount#1", {"appid": TEST_APPID}))

# Community.GetSteamFollowers - needs steamid of app (appid as steamid)
show("Community.GetSteamFollowers#1",
    try_um("Community.GetSteamFollowers#1", {"steamid": TEST_APPID}))

# StoreBrowse.GetItems with all data fields
show("StoreBrowse.GetItems (full)",
    try_um("StoreBrowse.GetItems#1", {
        "ids": [{"appid": TEST_APPID}],
        "context": {"language": "english", "country_code": "US", "steam_realm": 1},
        "data_request": {
            "include_tag_count": True,
            "include_reviews": True,
            "include_basic_info": True,
            "include_assets": True,
            "include_extended": True,
        }
    }))

# StoreAppSimilarity
show("StoreAppSimilarity.GetRelatedApps#1",
    try_um("StoreAppSimilarity.GetRelatedApps#1", {"appid": TEST_APPID}))

# PlayerService.GetOwnedGames style - check if follower endpoint exists
for method in [
    "Store.GetFollowerCount#1",
    "StoreAppSimilarity.GetSimilarApps#1",
    "StoreQuery.SearchResults#1",
    "Store.GetLocalizedNameForTags#1",
    "Community.GetCommunityBadgeProgress#1",
]:
    show(method, try_um(method, {"appid": TEST_APPID}))

client.disconnect()
