"""Find official game group clan_id via ResolveVanityURL + inspect CStoreItem fields"""
import os, gevent, urllib.request, urllib.parse, json
from steam.client import SteamClient
from steam.enums import EResult
from steam.enums.emsg import EMsg
from steam.core.msg import MsgProto
from steam.protobufs.steammessages_clientserver_2_pb2 import (
    CMsgFSGetFollowerCount, CMsgFSGetFollowerCountResponse
)

TEST_APPID = 3041230
PALWORLD_APPID = 1623730
STEAM_API_KEY = os.environ.get("STEAM_API_KEY", "")
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
        raw = result_holder[0].payload
        if raw:
            resp_proto = CMsgFSGetFollowerCountResponse()
            resp_proto.ParseFromString(raw)
            return resp_proto.eresult, resp_proto.count
    return None, "timeout"

def get_json(url, params={}):
    full_url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(full_url, headers={"User-Agent": "SteamExtract/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def show(label): print(f"\n{'='*50}\n=== {label} ===")
def to_clan_steamid(account_id):
    return (1 << 56) | (7 << 52) | (0 << 32) | account_id

# --- Try ResolveVanityURL for game groups ---
show("ResolveVanityURL for game official groups")
if STEAM_API_KEY:
    for vanity in ["palworld", "windrose", "Windrose"]:
        try:
            data = get_json("https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/", {
                "key": STEAM_API_KEY, "vanityurl": vanity, "url_type": 2  # 2=game group
            })
            result = data.get("response", {})
            print(f"  '{vanity}': success={result.get('success')}, steamid={result.get('steamid')}")
            if result.get("steamid"):
                steamid = int(result["steamid"])
                # Extract account_id from steamid64
                account_id = steamid & 0xFFFFFFFF
                print(f"    account_id={account_id}")
                eresult, count = get_follower_count(steamid)
                print(f"    followers: eresult={eresult}, count={count}")
        except Exception as e:
            print(f"  '{vanity}': error={e}")
else:
    print("  No API key")

# --- Check CStoreItem proto fields for follower field ---
show("CStoreItem all proto fields (look for follower/wish)")
try:
    from steam.protobufs.steammessages_storebrowse_pb2 import CStoreItem
    print(f"  CStoreItem has {len(CStoreItem.DESCRIPTOR.fields)} fields:")
    for f in CStoreItem.DESCRIPTOR.fields:
        if any(kw in f.name.lower() for kw in ["follow", "wish", "subscri", "interest", "fan"]):
            print(f"  *** {f.name} ({f.type}) ***")
        else:
            print(f"  {f.name} ({f.type})")
except Exception as e:
    print(f"  error: {e}")

# --- Try to get store follower data via store.steampowered.com ---
show("Store follower count via HTTP")
for appid in [TEST_APPID, PALWORLD_APPID]:
    for endpoint in [
        f"https://store.steampowered.com/app/{appid}/ajaxgetfollowerscount/",
        f"https://steamcommunity.com/actions/GroupFollowPage?appid={appid}",
    ]:
        try:
            req = urllib.request.Request(endpoint, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as r:
                data = r.read().decode("utf-8")
                print(f"  {endpoint}: {data[:200]}")
        except Exception as e:
            print(f"  {endpoint}: {type(e).__name__}: {str(e)[:100]}")

client.disconnect()
