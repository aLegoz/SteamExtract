"""Test CMsgFSGetFollowerCount - fixed body init + correct clan steamid"""
import json, os, gevent
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

def get_follower_count(steam_id):
    """Send CMsgFSGetFollowerCount and wait for response."""
    msg = MsgProto(EMsg.ClientFSGetFollowerCount)
    # Override body with correct proto type
    proto_body = CMsgFSGetFollowerCount()
    proto_body.steam_id = steam_id
    msg.body = proto_body

    # Use send_job + wait_event pattern
    jobid = client.send_job(msg)
    resp = client.wait_event(jobid, timeout=10)
    return resp

def show(label): print(f"\n{'='*50}\n=== {label} ===")

# --- First get the creator_clan_account_id via StoreBrowse ---
show("Get creator_clan_account_id from StoreBrowse")
creator_clan_id = None
try:
    resp = client.send_um_and_wait("StoreBrowse.GetItems#1", {
        "ids": [{"appid": TEST_APPID}],
        "context": {"language": "english", "country_code": "US", "steam_realm": 1},
        "data_request": {"include_basic_info": True}
    }, timeout=10)
    if resp and resp.body.store_items:
        item = resp.body.store_items[0]
        for pub in item.basic_info.publishers:
            print(f"  publisher: {pub.name}, clan_id={pub.creator_clan_account_id}")
            if pub.creator_clan_account_id:
                creator_clan_id = pub.creator_clan_account_id
        for dev in item.basic_info.developers:
            print(f"  developer: {dev.name}, clan_id={dev.creator_clan_account_id}")
            if dev.creator_clan_account_id and not creator_clan_id:
                creator_clan_id = dev.creator_clan_account_id
except Exception as e:
    print(f"  error: {e}")

# Build full clan SteamID (type=7, universe=1)
def to_clan_steamid(account_id):
    return (1 << 56) | (7 << 52) | (0 << 32) | account_id

# --- Try FSGetFollowerCount with clan steamid ---
show(f"CMsgFSGetFollowerCount - creator clan (id={creator_clan_id})")
if creator_clan_id:
    clan_steamid = to_clan_steamid(creator_clan_id)
    print(f"  steamid64={clan_steamid}")
    resp = get_follower_count(clan_steamid)
    if resp:
        r = resp[0]
        try:
            body = CMsgFSGetFollowerCountResponse()
            body.ParseFromString(r.body.SerializeToString() if hasattr(r.body, 'SerializeToString') else b'')
            print(f"  eresult={body.eresult}, count={body.count}")
        except:
            print(f"  raw resp: {resp}")
    else:
        print("  timeout/no response")

# --- Try with appid interpreted as account_id (game clan) ---
show(f"CMsgFSGetFollowerCount - game clan appid={TEST_APPID}")
game_clan_steamid = to_clan_steamid(TEST_APPID)
print(f"  steamid64={game_clan_steamid}")
resp = get_follower_count(game_clan_steamid)
if resp:
    print(f"  got response: {resp}")
else:
    print("  timeout/no response")

# --- Try with raw appid ---
show(f"CMsgFSGetFollowerCount - raw appid")
resp = get_follower_count(TEST_APPID)
if resp:
    print(f"  got response: {resp}")
else:
    print("  timeout/no response")

# --- Check event system: wait for FSGetFollowerCountResponse ---
show("Direct send + on_event approach")
try:
    result_holder = []
    def on_fs_resp(msg):
        result_holder.append(msg)

    client.on(EMsg.ClientFSGetFollowerCountResponse, on_fs_resp)

    msg = MsgProto(EMsg.ClientFSGetFollowerCount)
    proto_body = CMsgFSGetFollowerCount()
    proto_body.steam_id = to_clan_steamid(creator_clan_id) if creator_clan_id else TEST_APPID
    msg.body = proto_body
    client.send(msg)

    gevent.sleep(5)

    if result_holder:
        print(f"  Got response!")
        for r in result_holder:
            print(f"  {r}")
    else:
        print("  No response after 5 seconds")
except Exception as e:
    print(f"  {type(e).__name__}: {e}")
    import traceback; traceback.print_exc()

client.disconnect()
