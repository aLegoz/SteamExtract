"""Test: find follower data via Steam CM with real login"""
import json, os
from steam.client import SteamClient
from steam.enums import EResult

TEST_APPID = 3041230
STEAM_USER = os.environ.get("STEAM_USER", "")
STEAM_PASS = os.environ.get("STEAM_PASS", "")
STEAM_SHARED_SECRET = os.environ.get("STEAM_SHARED_SECRET", "")

client = SteamClient()

if STEAM_USER and STEAM_PASS:
    print(f"Logging in as {STEAM_USER}...")

    if STEAM_SHARED_SECRET:
        from steam.guard import SteamAuthenticator
        code = SteamAuthenticator({"shared_secret": STEAM_SHARED_SECRET}).get_code()
        print(f"Using TOTP 2FA code...")
        result = client.login(username=STEAM_USER, password=STEAM_PASS, two_factor_code=code)
    else:
        result = client.login(username=STEAM_USER, password=STEAM_PASS)

    print(f"Login result: {result}")

    if result == EResult.AccountLogonDenied:
        print("ERROR: Steam Guard (email) is enabled.")
        print("Fix: disable Steam Guard in Steam settings, OR add STEAM_SHARED_SECRET secret.")
        exit(1)
    elif result == EResult.AccountLoginDeniedNeedTwoFactor:
        print("ERROR: Mobile authenticator 2FA is required.")
        print("Fix: add STEAM_SHARED_SECRET secret (get it from your Steam mobile app).")
        exit(1)
    elif result != EResult.OK:
        print(f"ERROR: Login failed with {result}")
        exit(1)

    print("Login OK!")
else:
    print("No credentials — anonymous login.")
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

show("Store.GetFollowerCount#1",
    try_um("Store.GetFollowerCount#1", {"appid": TEST_APPID}))

show("Community.GetSteamFollowers#1",
    try_um("Community.GetSteamFollowers#1", {"steamid": TEST_APPID}))

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
