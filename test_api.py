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
        # Try to get all fields
        try:
            result = {}
            for field in body_obj.DESCRIPTOR.fields:
                val = getattr(body_obj, field.name, None)
                result[field.name] = str(val)
            return result
        except:
            return {"raw": str(body_obj)[:500]}
    except Exception as e:
        return {"error": str(e)}

def show(label, r):
    print(f"\n{'='*50}\n=== {label} ===")
    print(json.dumps(r, indent=2, default=str)[:800])

# StoreBrowse.GetItems — с деталями ответа
show("StoreBrowse.GetItems",
    try_um("StoreBrowse.GetItems#1", {
        "ids": [{"appid": TEST_APPID}],
        "context": {"language": "english", "country_code": "US", "steam_realm": 1},
        "data_request": {"include_tag_count": True, "include_reviews": True, "include_basic_info": True}
    }))

# Community follower methods
for method in [
    "Community.GetSteamFollowers#1",
    "StoreQuery.SearchResults#1",
    "Store.GetFollowerCount#1",
    "GameSearchService.SearchForGameResults#1",
    "StoreBrowse.GetDiscoveryQueue#1",
]:
    show(method, try_um(method, {"appid": TEST_APPID}))

client.disconnect()
