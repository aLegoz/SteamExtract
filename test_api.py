"""Test: connect to Steam as client using ValvePython/steam"""
import json
import os
from steam.client import SteamClient
from steam.enums import EResult
from steam.core.msg import MsgProto
from steam.enums.emsg import EMsg

STEAM_USER = os.environ.get("STEAM_USER", "")
STEAM_PASS = os.environ.get("STEAM_PASS", "")
TEST_APPID = 3041230

client = SteamClient()

@client.on("logged_on")
def on_logged_on():
    print("Logged in!")

    # Try to get app info via CM
    print("\n=== GetProductInfo (app details via CM) ===")
    resp = client.get_product_info(apps=[TEST_APPID])
    if resp and "apps" in resp:
        app = resp["apps"].get(TEST_APPID, {})
        common = app.get("common", {})
        print(json.dumps({
            "name": common.get("name"),
            "type": common.get("type"),
            "followers": common.get("followers"),
            "wishlists": common.get("wishlists"),
            "review_score": common.get("review_score"),
            "all_keys": list(common.keys())[:30],
        }, indent=2))

    # Try CStoreQuery for trending/follower data
    print("\n=== All common keys for app ===")
    if resp and "apps" in resp:
        app = resp["apps"].get(TEST_APPID, {})
        for section, data in app.items():
            print(f"\n[{section}]")
            if isinstance(data, dict):
                print(list(data.keys()))

    client.disconnect()

@client.on("error")
def on_error(result):
    print(f"Login error: {result}")
    client.disconnect()

if STEAM_USER and STEAM_PASS:
    print(f"Logging in as {STEAM_USER}...")
    result = client.login(username=STEAM_USER, password=STEAM_PASS)
else:
    print("Logging in anonymously...")
    client.anonymous_login()
    # Trigger on_logged_on manually for anonymous
    resp = client.get_product_info(apps=[TEST_APPID])
    if resp and "apps" in resp:
        app = resp["apps"].get(TEST_APPID, {})
        common = app.get("common", {})
        print(json.dumps({
            "name": common.get("name"),
            "followers": common.get("followers"),
            "all_keys": list(common.keys()),
        }, indent=2, default=str))
