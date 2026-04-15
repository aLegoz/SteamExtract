"""Test: inspect StoreBrowse data_request fields + Store service methods"""
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
    client.anonymous_login()
    print("Anonymous")

def show(label):
    print(f"\n{'='*50}\n=== {label} ===")

# --- Inspect all fields in data_request proto ---
show("data_request available fields")
try:
    from steam.protobufs import steammessages_storebrowse_pb2 as sb
    req_cls = sb.CStoreBrowse_GetItems_Request
    for f in req_cls.DESCRIPTOR.fields:
        print(f"  Request field: {f.name} ({f.type})")
    # Find data_request type
    data_req_field = req_cls.DESCRIPTOR.fields_by_name.get("data_request")
    if data_req_field:
        dr_type = data_req_field.message_type
        print(f"\n  data_request type: {dr_type.name}")
        for f in dr_type.fields:
            print(f"  data_request.{f.name} ({f.type})")
except Exception as e:
    print(f"  error: {e}")

# --- Inspect Store service methods ---
show("Store service methods (steammessages_store_pb2)")
try:
    from steam.protobufs import steammessages_store_pb2 as st
    for svc in st.DESCRIPTOR.services_by_name.values():
        print(f"  Service: {svc.name}")
        for method in svc.methods:
            print(f"    Method: {method.name}  input={method.input_type.name}  output={method.output_type.name}")
            # Show input fields
            for f in method.input_type.fields:
                print(f"      in.{f.name}")
except Exception as e:
    print(f"  error: {e}")

# --- StoreBrowse.GetItems with ALL data_request flags ---
show("StoreBrowse.GetItems - all flags")
try:
    from steam.protobufs import steammessages_storebrowse_pb2 as sb
    dr_field = sb.CStoreBrowse_GetItems_Request.DESCRIPTOR.fields_by_name.get("data_request")
    if dr_field:
        # Build data_request with all bool fields set to True
        dr_kwargs = {}
        for f in dr_field.message_type.fields:
            if f.type == 8:  # TYPE_BOOL = 8
                dr_kwargs[f.name] = True
        print(f"  Setting flags: {list(dr_kwargs.keys())}")

    resp = client.send_um_and_wait("StoreBrowse.GetItems#1", {
        "ids": [{"appid": TEST_APPID}],
        "context": {"language": "english", "country_code": "US", "steam_realm": 1},
        "data_request": dr_kwargs if dr_field else {"include_basic_info": True}
    }, timeout=10)

    if resp:
        print(f"  eresult: {resp.header.eresult}")
        # Print ALL fields of the store_item
        for item in resp.body.store_items:
            print(f"\n  item: {item.name}")
            for field in item.DESCRIPTOR.fields:
                val = getattr(item, field.name)
                # Only print non-default values
                default = field.default_value
                if val != default and str(val) not in ('0', '[]', '{}', ''):
                    print(f"    {field.name} = {str(val)[:200]}")
    else:
        print("  timeout")
except Exception as e:
    print(f"  error: {type(e).__name__}: {e}")
    import traceback; traceback.print_exc()

client.disconnect()
