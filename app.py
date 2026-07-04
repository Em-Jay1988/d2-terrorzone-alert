import os
import re
import json
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from zones import ZONES


TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]

API_URL = "https://d2runewizard.com/api/terror-zone"
LOCAL_TZ = ZoneInfo("Europe/Berlin")




def normalize(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def load_users():
    with open("users.json", "r", encoding="utf-8") as f:
        return json.load(f)


def send_telegram(chat_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(
        url,
        json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
        timeout=20,
    )
    r.raise_for_status()


def fetch_next_zone():
    r = requests.get(
        API_URL,
        headers={"User-Agent": "D2-Companion/1.0"},
        timeout=20,
    )
    r.raise_for_status()

    try:
        data = r.json()
    except Exception:
        print("API returned non-JSON response:")
        print(r.text[:500])
        return None

    return data.get("next")


def match_favorite_zone(next_zone, favorites):
    zone_norm = normalize(next_zone)

    for code in favorites:
        zone = ZONES.get(code)
        if not zone:
            continue

        for keyword in zone["keywords"]:
            if keyword in zone_norm:
                return zone["name"]

    return None


def next_start_time():
    now = datetime.now(LOCAL_TZ)

    if now.minute < 30:
        start = now.replace(minute=30, second=0, microsecond=0)
    else:
        start = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

    return start.strftime("%H:%M")


def main():
    users = load_users()
    next_zone = fetch_next_zone()

    if not next_zone:
        print("No valid next zone received. Skipping.")
        return

    for chat_id, user in users.items():
        if chat_id.startswith("_"):
            continue
        favorites = user.get("favorites", [])
        matched_zone = match_favorite_zone(next_zone, favorites)

        if not matched_zone:
            print(f"No match for {user.get('name', chat_id)}. Next TZ: {next_zone}")
            continue

        send_telegram(
            chat_id,
            f"🔥 <b>Terror Zone Alarm</b>\n"
            f"⏰ Start: {next_start_time()}\n"
            f"📍 {matched_zone}"
        )


if __name__ == "__main__":
    main()
