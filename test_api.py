"""Test CMsgFSGetFollowerCount via direct CM message"""
import json, os
from steam.client import SteamClient
from steam.enums import EMsg, EResult
from steam.core.msg import MsgProto

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

# --- Find EMsg for FSGetFollowerCount ---
show("EMsg for FS follower count")
try:
    # Search EMsg enum for follower-related values
    for name, val in EMsg.__members__.items():
        if "follow" in name.lower() or "FS" in name:
            print(f"  EMsg.{name} = {val}")
except Exception as e:
    print(f"  error: {e}")

# --- CMsgFSGetFollowerCount ---
show("CMsgFSGetFollowerCount - direct CM message")
try:
    from steam.protobufs.steammessages_clientserver_2_pb2 import (
        CMsgFSGetFollowerCount, CMsgFSGetFollowerCountResponse
    )
    # SteamID for game community: clan type, account_id = ?
    # Try different steam_id formats for the app

    # Method 1: Use appid directly as steamid (wrong but let's see)
    # Method 2: Build a proper clan SteamID
    # Clan SteamID: universe=1, type=7(Clan), instance=0, account_id
    # format: ((1 << 56) | (7 << 52) | (0 << 32) | account_id)
    # For games, their community group often has account_id = appid

    clan_steamid = (1 << 56) | (7 << 52) | (0 << 32) | TEST_APPID
    print(f"  Trying clan steamid: {clan_steamid}")

    # Find EMsg value
    emsg_req = None
    emsg_resp = None
    for name, val in EMsg.__members__.items():
        if "FSGetFollowerCount" in name:
            print(f"  Found EMsg: {name} = {val}")
            if "Response" in name:
                emsg_resp = val
            else:
                emsg_req = val

    if emsg_req is None:
        # Try to find it by searching
        print("  EMsg not found by name, trying common values...")
        # ClientFSGetFollowerCount is around EMsg 796
        for test_emsg in [796, 797, 780, 781]:
            try:
                e = EMsg(test_emsg)
                print(f"  EMsg({test_emsg}) = {e.name}")
            except:
                pass

    # Try with send_job - uses job system
    import gevent

    result_event = gevent.event.AsyncResult()
    def on_response(msg):
        result_event.set(msg)

    # Build and send the message
    msg = MsgProto(EMsg.ClientFSGetFollowerCount if hasattr(EMsg, 'ClientFSGetFollowerCount') else EMsg(796))
    msg.body.steam_id = clan_steamid
    print(f"  Sending with steamid={clan_steamid}...")

    jobid = client.send_job(msg)
    resp = client.wait_event(jobid, timeout=10)
    if resp:
        print(f"  Response: {resp}")
        print(f"  Response type: {type(resp)}")
        if hasattr(resp[0], 'body'):
            print(f"  Body: {resp[0].body}")
    else:
        print("  No response (timeout)")

except Exception as e:
    print(f"  {type(e).__name__}: {e}")
    import traceback; traceback.print_exc()

# --- Also try with appid directly as steam_id ---
show("CMsgFSGetFollowerCount - appid as steamid")
try:
    msg = MsgProto(EMsg.ClientFSGetFollowerCount if hasattr(EMsg, 'ClientFSGetFollowerCount') else EMsg(796))
    msg.body.steam_id = TEST_APPID
    jobid = client.send_job(msg)
    resp = client.wait_event(jobid, timeout=10)
    if resp:
        print(f"  Body: {resp[0].body if hasattr(resp[0], 'body') else resp}")
    else:
        print("  No response (timeout)")
except Exception as e:
    print(f"  {type(e).__name__}: {e}")

client.disconnect()
