"""Test CMsgFSGetFollowerCount - parse raw payload"""
import os, gevent
from steam.client import SteamClient
from steam.enums import EResult
from steam.enums.emsg import EMsg
from steam.core.msg import MsgProto
from steam.protobufs.steammessages_clientserver_2_pb2 import (
    CMsgFSGetFollowerCount, CMsgFSGetFollowerCountResponse
)

TEST_APPID = 3041230
# Palworld (well-known game with followers)
PALWORLD_APPID = 1623730

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

def get_follower_count(steam_id):
    """Send CMsgFSGetFollowerCount, parse raw payload response."""
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
        r = result_holder[0]
        # Try all ways to get raw bytes
        raw_bytes = None
        for attr in ['payload', 'body_data', 'msg_data', '_data']:
            val = getattr(r, attr, None)
            if val and isinstance(val, (bytes, bytearray)) and len(val) > 0:
                raw_bytes = bytes(val)
                print(f"  got bytes via r.{attr}: {raw_bytes.hex()}")
                break

        if raw_bytes is None:
            # Try serializing the whole message and extracting body
            try:
                full_bytes = bytes(r)
                print(f"  full serialized len={len(full_bytes)}")
                raw_bytes = full_bytes[-20:]  # try last bytes as body
            except Exception as e:
                print(f"  serialize error: {e}")

        if raw_bytes:
            try:
                resp_proto = CMsgFSGetFollowerCountResponse()
                resp_proto.ParseFromString(raw_bytes)
                return resp_proto.eresult, resp_proto.count
            except Exception as e:
                print(f"  parse error: {e}")
                # Try to print all attributes of r
                print(f"  r attrs: {[a for a in dir(r) if not a.startswith('_')]}")
        return None, f"no bytes (r type={type(r).__name__})"
    return None, "timeout"

def show(label): print(f"\n{'='*50}\n=== {label} ===")

def to_clan_steamid(account_id):
    return (1 << 56) | (7 << 52) | (0 << 32) | account_id

# --- Test with GabeN ---
show("GabeN user steamid")
eresult, count = get_follower_count(76561197960287930)
print(f"  eresult={eresult}, count={count}")

# --- Get Palworld clan_id from StoreBrowse and test ---
show("Palworld StoreBrowse clan_ids")
try:
    resp = client.send_um_and_wait("StoreBrowse.GetItems#1", {
        "ids": [{"appid": PALWORLD_APPID}],
        "context": {"language": "english", "country_code": "US", "steam_realm": 1},
        "data_request": {"include_basic_info": True}
    }, timeout=10)
    if resp and resp.body.store_items:
        item = resp.body.store_items[0]
        print(f"  Game: {item.name}")
        for pub in item.basic_info.publishers:
            cid = pub.creator_clan_account_id
            print(f"  Publisher {pub.name}: clan_id={cid}")
            if cid:
                steamid = to_clan_steamid(cid)
                eresult, count = get_follower_count(steamid)
                print(f"    -> eresult={eresult}, count={count}")
        for dev in item.basic_info.developers:
            cid = dev.creator_clan_account_id
            print(f"  Developer {dev.name}: clan_id={cid}")
            if cid:
                steamid = to_clan_steamid(cid)
                eresult, count = get_follower_count(steamid)
                print(f"    -> eresult={eresult}, count={count}")
except Exception as e:
    print(f"  error: {e}")

client.disconnect()
