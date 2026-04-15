"""Test: Steam CM unified messages for follower/wishlist data"""
import json
from steam.client import SteamClient

TEST_APPID = 3041230

client = SteamClient()
print("Logging in anonymously...")
client.anonymous_login()

def show(label, r):
    print(f"\n{'='*50}\n=== {label} ===")
    try:
        print(json.dumps(r, indent=2, default=str)[:1500])
    except:
        print(str(r)[:1000])

# 1. CStoreBrowse.GetItems — может содержать follower/wishlist
try:
    resp = client.unified_messages.send_and_wait(
        "StoreBrowse.GetItems#1",
        {"ids": [{"appid": TEST_APPID}], "context": {"language": "english", "country_code": "US", "steam_realm": 1}, "data_request": {"include_tag_count": True, "include_assets": False}},
        timeout=10
    )
    show("StoreBrowse.GetItems", dict(resp.body) if resp else {"error": "no response"})
except Exception as e:
    show("StoreBrowse.GetItems", {"error": str(e)})

# 2. CStoreQuery.SearchResults — новые релизы с фолловерами?
try:
    resp = client.unified_messages.send_and_wait(
        "StoreQuery.SearchResults#1",
        {"query": {"new_releases": {}}, "context": {"language": "english", "country_code": "US", "steam_realm": 1}, "data_request": {"include_tag_count": True}},
        timeout=10
    )
    show("StoreQuery.SearchResults", dict(resp.body) if resp else {"error": "no response"})
except Exception as e:
    show("StoreQuery.SearchResults", {"error": str(e)})

# 3. CPlayer.GetTopAchievementsForGames — просто проверка unified_messages
try:
    resp = client.unified_messages.send_and_wait(
        "WishlistService.GetWishlistCount#1",
        {"appid": TEST_APPID},
        timeout=10
    )
    show("WishlistService.GetWishlistCount", dict(resp.body) if resp else {"error": "no response"})
except Exception as e:
    show("WishlistService.GetWishlistCount", {"error": str(e)})

client.disconnect()
