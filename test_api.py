"""Test: Steam CM unified messages via send_um_and_wait"""
import json
from steam.client import SteamClient

TEST_APPID = 3041230

client = SteamClient()
print("Logging in anonymously...")
client.anonymous_login()

def show(label, r):
    print(f"\n{'='*50}\n=== {label} ===")
    try:
        print(json.dumps(r, indent=2, default=str)[:2000])
    except:
        print(str(r)[:1000])

# Check what methods are available for unified messaging
um_methods = [m for m in dir(client) if 'um' in m.lower() or 'unified' in m.lower() or 'service' in m.lower()]
print(f"UM-related methods: {um_methods}")

# Try send_um_and_wait
try:
    resp = client.send_um_and_wait(
        "StoreBrowse.GetItems#1",
        {
            "ids": [{"appid": TEST_APPID}],
            "context": {"language": "english", "country_code": "US", "steam_realm": 1},
            "data_request": {"include_tag_count": True}
        },
        timeout=10
    )
    show("StoreBrowse.GetItems (send_um_and_wait)", resp.body if resp else "no response")
except Exception as e:
    show("StoreBrowse.GetItems error", {"error": str(e)})

# Try WishlistService
try:
    resp = client.send_um_and_wait(
        "WishlistService.GetWishlistSortedFiltered#1",
        {"steamid": 0, "appid": TEST_APPID},
        timeout=10
    )
    show("WishlistService", resp.body if resp else "no response")
except Exception as e:
    show("WishlistService error", {"error": str(e)})

# Check available services via Steam
try:
    from steam.core.msg import MsgProto
    from steam.enums.emsg import EMsg
    msg = MsgProto(EMsg.ClientRequestedClientStats)
    print(f"\nMsgProto works: {type(msg)}")
except Exception as e:
    print(f"MsgProto error: {e}")

client.disconnect()
