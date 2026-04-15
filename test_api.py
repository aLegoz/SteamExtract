"""Find game clan_id via associations + ResolveVanityURL"""
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
            r = CMsgFSGetFollowerCountResponse()
            r.ParseFromString(raw)
            return r.eresult, r.count
    return None, "timeout"

def get_json(url, params={}):
    try:
        full_url = url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(full_url, headers={"User-Agent": "SteamExtract/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

def show(label): print(f"\n{'='*50}\n=== {label} ===")
def to_clan_steamid(account_id):
    return (1 << 56) | (7 << 52) | (0 << 32) | account_id

# --- get_product_info associations ---
show("get_product_info associations (both games)")
for appid in [TEST_APPID, PALWORLD_APPID]:
    try:
        info = client.get_product_info(apps=[appid])
        common = info.get("apps", {}).get(appid, {}).get("common", {})
        print(f"\n  appid={appid} ({common.get('name', '?')})")
        assoc = common.get("associations", {})
        if assoc:
            for k, v in assoc.items():
                print(f"    assoc[{k}]: {v}")
        else:
            print("    (no associations)")
        # Also check all fields that might have steam_id/clan
        for key in sorted(common.keys()):
            val = common[key]
            val_str = str(val)
            if any(kw in key.lower() for kw in ["clan", "group", "community", "hub"]) or \
               (len(val_str) > 10 and val_str.isdigit() and int(val_str) > 10**15):
                print(f"    {key}: {val_str[:200]}")
    except Exception as e:
        print(f"  error for {appid}: {e}")

# --- ResolveVanityURL for game groups ---
show("ResolveVanityURL for game official groups (url_type=2)")
if STEAM_API_KEY:
    for appid, names in [
        (PALWORLD_APPID, ["Palworld", "palworld", "pocketpair"]),
        (TEST_APPID, ["Windrose", "windrose", "krakenexpress"])
    ]:
        print(f"\n  appid={appid}:")
        for vanity in names:
            data = get_json("https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/", {
                "key": STEAM_API_KEY, "vanityurl": vanity, "url_type": 2
            })
            result = data.get("response", {})
            success = result.get("success")
            steamid = result.get("steamid")
            print(f"    '{vanity}': success={success}, steamid={steamid}")
            if steamid and success == 1:
                sid = int(steamid)
                eresult, count = get_follower_count(sid)
                print(f"      -> followers: eresult={eresult}, count={count}")
else:
    print("  No STEAM_API_KEY set")

# --- Try to find clan via ISteamApps.GetAppInfo ---
show("IStoreService/GetAppInfo via Web API")
if STEAM_API_KEY:
    for appid in [PALWORLD_APPID, TEST_APPID]:
        data = get_json("https://api.steampowered.com/IStoreService/GetAppInfo/v1/", {
            "key": STEAM_API_KEY, "appids": appid, "include_all_platforms": True
        })
        print(f"  appid={appid}: {json.dumps(data, default=str)[:300]}")
else:
    print("  No STEAM_API_KEY")

# --- Try CommunityService.GetApps ---
show("CommunityService.GetApps#1 via CM")
try:
    resp = client.send_um_and_wait("CommunityService.GetApps#1", {"appids": [PALWORLD_APPID]}, timeout=10)
    if resp:
        print(f"  eresult: {resp.header.eresult}")
        print(f"  body: {str(resp.body)[:500]}")
    else:
        print("  timeout")
except Exception as e:
    print(f"  {type(e).__name__}: {e}")

client.disconnect()
