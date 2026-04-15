"""Test: Steam CM follower data with real login"""
import json, os
from steam.client import SteamClient
from steam.enums import EResult

TEST_APPID = 3041230
STEAM_USER = os.environ.get("STEAM_USER", "")
STEAM_PASS = os.environ.get("STEAM_PASS", "")

client = SteamClient()

if STEAM_USER and STEAM_PASS:
    print(f"Logging in as {STEAM_USER}...")
    result = client.login(username=STEAM_USER, password=STEAM_PASS)
    print(f"Login result: {result}")
    if result != EResult.OK:
        print(f"Login failed: {result}")
        exit(1)
    print("Login OK!")
else:
    print("Anonymous login...")
    client.anonymous_login()

def try_um_raw(method, body={}):
    """Return raw response without parsing to see what we actually get."""
    try:
        resp = client.send_um_and_wait(method, body, timeout=10)
        if resp is None:
            return "None (timeout)"
        print(f"  eresult header: {resp.header.eresult}")
        print(f"  body type: {type(resp.body)}")
        print(f"  body str: {str(resp.body)[:1000]}")
        # Try to list all fields
        try:
            for field in resp.body.DESCRIPTOR.fields:
                val = getattr(resp.body, field.name, None)
                print(f"  field {field.name} = {val}")
        except Exception as fe:
            print(f"  fields error: {fe}")
        return "OK"
    except Exception as e:
        print(f"  exception {type(e).__name__}: {e}")
        return "ERROR"

def show(label):
    print(f"\n{'='*50}\n=== {label} ===")

# --- Try Store.GetFollowerCount with all body variations ---
show("Store.GetFollowerCount#1 - appid only")
try_um_raw("Store.GetFollowerCount#1", {"appid": TEST_APPID})

show("Store.GetFollowerCount#1 - empty body")
try_um_raw("Store.GetFollowerCount#1", {})

show("Store.GetFollowerCount#1 - steamid")
try_um_raw("Store.GetFollowerCount#1", {"steamid": TEST_APPID})

# --- Try StoreBrowse.GetItems - worked anonymously ---
show("StoreBrowse.GetItems#1 - minimal")
try_um_raw("StoreBrowse.GetItems#1", {
    "ids": [{"appid": TEST_APPID}],
    "context": {"language": "english", "country_code": "US", "steam_realm": 1},
    "data_request": {"include_basic_info": True}
})

# --- List available proto services ---
show("Available proto services (Store-related)")
try:
    import steam.protobufs
    import pkgutil, importlib
    for importer, modname, ispkg in pkgutil.walk_packages(
        path=steam.protobufs.__path__,
        prefix=steam.protobufs.__name__ + ".",
        onerror=lambda x: None
    ):
        if "store" in modname.lower() or "follow" in modname.lower():
            print(f"  module: {modname}")
except Exception as e:
    print(f"  error: {e}")

# --- get_product_info - check all sections for follower data ---
show("get_product_info - all keys")
try:
    info = client.get_product_info(apps=[TEST_APPID])
    app_data = info.get("apps", {}).get(TEST_APPID, {})
    for section, data in app_data.items():
        keys = list(data.keys()) if hasattr(data, 'keys') else str(data)[:100]
        print(f"  section '{section}': {keys}")
        # Look specifically for follower/wishlist data
        data_str = str(data).lower()
        if any(kw in data_str for kw in ["follow", "wish", "subscri"]):
            print(f"    *** FOUND RELEVANT DATA: {str(data)[:500]}")
except Exception as e:
    print(f"  error: {e}")

client.disconnect()
