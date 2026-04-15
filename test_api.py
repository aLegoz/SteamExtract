"""Test: scrape SteamDB for follower/wishlist data"""
import json
import os
import re
import urllib.request
import urllib.parse

KEY = os.environ.get("STEAM_API_KEY", "")
TEST_APPID = 730  # CS2

def get(url, params={}, headers={}):
    full_url = url + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(full_url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        **headers,
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return {"json": json.loads(raw), "raw": None}
            except:
                return {"json": None, "raw": raw}
    except Exception as e:
        return {"error": str(e)}

def show(label, r):
    print(f"\n{'='*50}")
    print(f"=== {label} ===")
    if "error" in r:
        print(f"ERROR: {r['error']}")
    elif r.get("json") is not None:
        print(json.dumps(r["json"], indent=2)[:800])
    elif r.get("raw"):
        # Search for follower-related keywords in HTML
        raw = r["raw"]
        for keyword in ["follower", "wishlist", "subscriber", "following", "followers"]:
            idx = raw.lower().find(keyword)
            if idx != -1:
                print(f"Found '{keyword}' at pos {idx}:")
                print(raw[max(0, idx-100):idx+200])
                print("---")
        print(f"(Full HTML length: {len(raw)} chars)")

# 1. SteamDB app page
r = get(f"https://steamdb.info/app/{TEST_APPID}/")
show("steamdb.info/app page", r)

# 2. SteamDB API endpoint (undocumented)
r = get("https://steamdb.info/api/ExtendedAppDetails/", {"appids": TEST_APPID}, {"Accept": "application/json"})
show("steamdb.info/api/ExtendedAppDetails", r)

# 3. SteamDB instantsearch / search API
r = get("https://steamdb.info/api/instantsearch/", {"query": "counter-strike 2"}, {"Accept": "application/json"})
show("steamdb.info/api/instantsearch", r)
