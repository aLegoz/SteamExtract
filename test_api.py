"""Scan all proto files for follower/wishlist, test GetUserGameInterestState"""
import json, os
from steam.client import SteamClient
from steam.enums import EResult

TEST_APPID = 3041230
STEAM_USER = os.environ.get("STEAM_USER", "")
STEAM_PASS = os.environ.get("STEAM_PASS", "")

client = SteamClient()
if STEAM_USER and STEAM_PASS:
    result = client.login(username=STEAM_USER, password=STEAM_PASS)
    if result != EResult.OK:
        print(f"Login failed: {result}"); exit(1)
    print("Login OK!")
else:
    client.anonymous_login(); print("Anonymous")

def show(label): print(f"\n{'='*50}\n=== {label} ===")

# --- Scan ALL proto modules for follower/wishlist ---
show("Proto scan: follower/wishlist/subscriber mentions")
try:
    import steam.protobufs, pkgutil
    KEYWORDS = ["follow", "wishlist", "subscri", "interest"]
    for importer, modname, ispkg in pkgutil.walk_packages(
        path=steam.protobufs.__path__,
        prefix=steam.protobufs.__name__ + ".",
        onerror=lambda x: None
    ):
        try:
            mod = __import__(modname, fromlist=[""])
            # Check all message types
            for msg_name, msg_desc in mod.DESCRIPTOR.message_types_by_name.items():
                for f in msg_desc.fields:
                    for kw in KEYWORDS:
                        if kw in f.name.lower() or kw in msg_name.lower():
                            print(f"  [{modname.split('.')[-1]}] {msg_name}.{f.name}")
            # Check all service methods
            for svc_name, svc_desc in mod.DESCRIPTOR.services_by_name.items():
                for method in svc_desc.methods:
                    for kw in KEYWORDS:
                        if kw in method.name.lower() or kw in svc_name.lower():
                            print(f"  [{modname.split('.')[-1]}] Service:{svc_name}.{method.name}")
        except Exception:
            pass
except Exception as e:
    print(f"  error: {e}")

# --- Store.GetUserGameInterestState - per-user wishlist status ---
show("Store.GetUserGameInterestState#1")
try:
    resp = client.send_um_and_wait("Store.GetUserGameInterestState#1",
        {"appid": TEST_APPID}, timeout=10)
    if resp:
        print(f"  eresult: {resp.header.eresult}")
        print(f"  body: {resp.body}")
    else:
        print("  timeout")
except Exception as e:
    print(f"  {type(e).__name__}: {e}")

# --- StoreBrowse: check if include_extended exists via other approach ---
show("StoreBrowse.GetItems - include_trailers to verify trailer data")
try:
    resp = client.send_um_and_wait("StoreBrowse.GetItems#1", {
        "ids": [{"appid": TEST_APPID}],
        "context": {"language": "english", "country_code": "US", "steam_realm": 1},
        "data_request": {"include_trailers": True, "include_basic_info": True, "include_reviews": True}
    }, timeout=10)
    if resp and resp.body.store_items:
        item = resp.body.store_items[0]
        # trailers
        print(f"  trailers count: {len(item.trailers.highlights) + len(item.trailers.other_trailers)}")
        for t in list(item.trailers.highlights)[:2]:
            print(f"    trailer: {t.trailer_name}")
        # reviews
        r = item.reviews
        print(f"  reviews: {r.summary_filtered.review_count} total, {r.summary_filtered.percent_positive}% positive")
except Exception as e:
    print(f"  {type(e).__name__}: {e}")
    import traceback; traceback.print_exc()

client.disconnect()
