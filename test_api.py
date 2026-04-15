"""Find the right steam_id for game follower count"""
import os, gevent
from steam.client import SteamClient
from steam.enums import EResult
from steam.enums.emsg import EMsg
from steam.core.msg import MsgProto
from steam.protobufs.steammessages_clientserver_2_pb2 import (
    CMsgFSGetFollowerCount, CMsgFSGetFollowerCountResponse
)

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

def get_follower_count(steam_id, label=""):
    """Send CMsgFSGetFollowerCount and get count via event."""
    result_holder = []
    ev = gevent.event.Event()

    def on_resp(msg):
        result_holder.append(msg)
        ev.set()

    client.once(EMsg.ClientFSGetFollowerCountResponse, on_resp)

    msg = MsgProto(EMsg.ClientFSGetFollowerCount)
    proto_body = CMsgFSGetFollowerCount()
    proto_body.steam_id = steam_id
    msg.body = proto_body
    client.send(msg)

    ev.wait(timeout=5)

    if result_holder:
        raw = result_holder[0].body
        try:
            resp_body = CMsgFSGetFollowerCountResponse()
            if hasattr(raw, 'SerializeToString'):
                resp_body.ParseFromString(raw.SerializeToString())
            else:
                # raw might be bytes
                resp_body.ParseFromString(bytes(raw))
            return resp_body.eresult, resp_body.count
        except Exception as e:
            return None, f"parse error: {e} / raw={bytes(raw)[:20] if hasattr(raw, '__bytes__') else raw}"
    return None, "timeout"

def show(label): print(f"\n{'='*50}\n=== {label} ===")

def to_clan_steamid(account_id):
    return (1 << 56) | (7 << 52) | (0 << 32) | account_id

# --- Validate: GabeN should have many followers ---
show("GabeN user steamid (should have followers)")
gaben_steamid = 76561197960287930
eresult, count = get_follower_count(gaben_steamid, "GabeN")
print(f"  eresult={eresult}, count={count}")

# --- Windrose appid as-is (not valid SteamID but let's see) ---
show("Windrose appid raw")
eresult, count = get_follower_count(TEST_APPID)
print(f"  eresult={eresult}, count={count}")

# --- All publisher/developer clan_ids from StoreBrowse ---
show("Get all clan_ids from StoreBrowse + try each")
try:
    resp = client.send_um_and_wait("StoreBrowse.GetItems#1", {
        "ids": [{"appid": TEST_APPID}],
        "context": {"language": "english", "country_code": "US", "steam_realm": 1},
        "data_request": {"include_basic_info": True}
    }, timeout=10)
    if resp and resp.body.store_items:
        item = resp.body.store_items[0]
        clan_ids = set()
        for pub in item.basic_info.publishers:
            cid = pub.creator_clan_account_id
            print(f"  Publisher {pub.name}: clan_account_id={cid}")
            if cid: clan_ids.add(cid)
        for dev in item.basic_info.developers:
            cid = dev.creator_clan_account_id
            print(f"  Developer {dev.name}: clan_account_id={cid}")
            if cid: clan_ids.add(cid)
        print(f"\n  Testing {len(clan_ids)} clan(s):")
        for cid in clan_ids:
            steamid = to_clan_steamid(cid)
            eresult, count = get_follower_count(steamid)
            print(f"    clan_id={cid} steamid={steamid} -> eresult={eresult}, count={count}")
except Exception as e:
    print(f"  error: {e}")

# --- Try get_product_info for any community-related fields ---
show("get_product_info - look for community/clan ids")
try:
    info = client.get_product_info(apps=[TEST_APPID])
    common = info.get("apps", {}).get(TEST_APPID, {}).get("common", {})
    # Print fields that might contain community/clan info
    for key in sorted(common.keys()):
        val = str(common[key])
        if any(kw in key.lower() for kw in ["community", "clan", "group", "hub", "page", "steam_id"]):
            print(f"  {key}: {val}")
    # Also print gameid, steam_release_date for reference
    for key in ["gameid", "community_hub_visible", "community_visible_stats"]:
        if key in common:
            print(f"  {key}: {common[key]}")
except Exception as e:
    print(f"  error: {e}")

client.disconnect()
