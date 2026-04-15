"""Test: find follower data via Steam CM with real login"""
import json, os
from steam.client import SteamClient

TEST_APPID = 3041230
STEAM_USER = os.environ.get("STEAM_USER", "")
STEAM_PASS = os.environ.get("STEAM_PASS", "")
STEAM_SHARED_SECRET = os.environ.get("STEAM_SHARED_SECRET", "")

client = SteamClient()

if STEAM_USER and STEAM_PASS:
    print(f"Logging in as {STEAM_USER}...")
    if STEAM_SHARED_SECRET:
        # Auto 2FA via shared_secret (no interactive prompt needed)
        try:
            from steam.guard import SteamAuthenticator
            code = SteamAuthenticator({"shared_secret": STEAM_SHARED_SECRET}).get_code()
            print(f"Using 2FA code from shared_secret: {code}")
            client.login(username=STEAM_USER, password=STEAM_PASS, two_factor_code=code)
        except Exception as e:
            print(f"2FA error: {e}, falling back to cli_login...")
            client.cli_login(username=STEAM_USER, password=STEAM_PASS)
    else:
        # Will ask for Steam Guard code interactively
        client.cli_login(username=STEAM_USER, password=STEAM_PASS)
else:
    print("No credentials set. Add STEAM_USER, STEAM_PASS (and STEAM_SHARED_SECRET for 2FA) secrets.")
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

# --- Key methods to test ---

# GetFollowerCount - the target endpoint
show("Store.GetFollowerCount#1",
    try_um("Store.GetFollowerCount#1", {"appid": TEST_APPID}))

# Community follower count
show("Community.GetSteamFollowers#1",
    try_um("Community.GetSteamFollowers#1", {"steamid": TEST_APPID}))

# StoreBrowse.GetItems with extended data
show("StoreBrowse.GetItems#1",
    try_um("StoreBrowse.GetItems#1", {
        "ids": [{"appid": TEST_APPID}],
        "context": {"language": "english", "country_code": "US", "steam_realm": 1},
        "data_request": {
            "include_tag_count": True,
            "include_reviews": True,
            "include_basic_info": True,
            "include_extended": True,
        }
    }))

client.disconnect()
