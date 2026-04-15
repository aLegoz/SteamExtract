"""Test: explore all sections of Steam CM product info"""
import json
from steam.client import SteamClient

TEST_APPID = 3041230

client = SteamClient()
print("Logging in anonymously...")
client.anonymous_login()

resp = client.get_product_info(apps=[TEST_APPID])

if resp and "apps" in resp:
    app = resp["apps"].get(TEST_APPID, {})

    print(f"\n=== All top-level sections ===")
    print(list(app.keys()))

    for section, data in app.items():
        print(f"\n{'='*50}")
        print(f"[{section}]")
        try:
            print(json.dumps(dict(data), indent=2, default=str)[:1500])
        except:
            print(str(data)[:1000])
else:
    print("No response")

client.disconnect()
