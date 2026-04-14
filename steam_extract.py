import json
import os
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SEEN_FILE = os.path.join(SCRIPT_DIR, "seen_games.json")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "new_releases.txt")

FEATURED_URL = "https://store.steampowered.com/api/featuredcategories/"
DETAILS_URL = "https://store.steampowered.com/api/appdetails"

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")


def get_json(url, params):
    full_url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(full_url, headers={"User-Agent": "SteamExtract/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(seen, f, indent=2, ensure_ascii=False)


def fetch_new_releases():
    data = get_json(FEATURED_URL, {"cc": "us", "l": "english"})
    return data.get("new_releases", {}).get("items", [])


def fetch_app_details(app_id):
    try:
        data = get_json(DETAILS_URL, {"appids": app_id, "cc": "us", "l": "english"})
        app_data = data.get(str(app_id), {})
        if app_data.get("success"):
            return app_data["data"]
    except Exception as e:
        print(f"  Warning: failed to fetch details for {app_id}: {e}")
    return None


def format_price(item):
    if item.get("discount_percent", 0) > 0:
        original = item.get("original_price", 0) / 100
        final = item.get("final_price", 0) / 100
        discount = item["discount_percent"]
        return f"${final:.2f} (-{discount}%, was ${original:.2f})"
    final = item.get("final_price", 0)
    if final == 0:
        return "Free to Play"
    return f"${final / 100:.2f}"


def send_discord(games):
    if not DISCORD_WEBHOOK_URL:
        return

    for g in games:
        embed = {
            "title": g["name"],
            "url": f"https://store.steampowered.com/app/{g['app_id']}",
            "color": 0x1b2838,
            "fields": [
                {"name": "Release Date", "value": g["release_date"], "inline": True},
                {"name": "Price",        "value": g["price"],        "inline": True},
                {"name": "Genres",       "value": g["genres"],       "inline": False},
            ],
            "footer": {"text": "SteamExtract"},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        payload = json.dumps({"embeds": [embed]}).encode("utf-8")
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "SteamExtract/1.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                pass
        except Exception as e:
            print(f"  Warning: Discord notification failed: {e}")
        time.sleep(0.5)


def main():
    print("SteamExtract - fetching new releases...")

    seen = load_seen()

    try:
        items = fetch_new_releases()
    except Exception as e:
        print(f"Error fetching from Steam: {e}")
        sys.exit(1)

    if not items:
        print("No releases found from Steam API.")
        sys.exit(0)

    new_items = [item for item in items if str(item["id"]) not in seen]

    if not new_items:
        print(f"No new games found ({len(items)} already tracked).")
        today = datetime.now().strftime("%Y-%m-%d")
        for item in items:
            seen.setdefault(str(item["id"]), today)
        save_seen(seen)
        sys.exit(0)

    print(f"Found {len(new_items)} new game(s). Fetching details...")

    games = []
    for item in new_items:
        app_id = item["id"]
        details = fetch_app_details(app_id)
        time.sleep(1.5)

        release_date = "Unknown"
        genres = "Unknown"
        if details:
            release_date = details.get("release_date", {}).get("date", "Unknown")
            genre_list = details.get("genres", [])
            if genre_list:
                genres = ", ".join(g["description"] for g in genre_list)

        games.append({
            "name": item.get("name", "Unknown"),
            "app_id": app_id,
            "release_date": release_date,
            "price": format_price(item),
            "genres": genres,
        })

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n--- Run: {now} --- ({len(games)} new game(s) found)\n\n")
        for g in games:
            f.write("=" * 50 + "\n")
            f.write(f"Name: {g['name']}\n")
            f.write(f"Release Date: {g['release_date']}\n")
            f.write(f"Price: {g['price']}\n")
            f.write(f"Genres: {g['genres']}\n")
            f.write(f"Link: https://store.steampowered.com/app/{g['app_id']}\n")
            f.write("=" * 50 + "\n\n")

    today = datetime.now().strftime("%Y-%m-%d")
    for item in items:
        seen.setdefault(str(item["id"]), today)
    save_seen(seen)

    send_discord(games)

    print(f"Done! {len(games)} game(s) added to {OUTPUT_FILE}")
    for g in games:
        name = g['name'].encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8', errors='replace')
        print(f"  + {name}")


if __name__ == "__main__":
    main()
    input("\nНажмите Enter для выхода...")
