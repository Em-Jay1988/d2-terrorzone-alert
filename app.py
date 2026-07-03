import os
import re
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

API_URL = "https://d2runewizard.com/api/terror-zone"
LOCAL_TZ = ZoneInfo("Europe/Berlin")

# HIER steuerst du deine aktiven Favoriten:
ACTIVE_FAVORITES = [
    "kata",
    "tal",
    "meph",
    "chaos",
    "wsk",
]

ZONES = {
    "kata": {
        "name": "🕸️ Katakomben",
        "keywords": ["cathedral", "catacombs"],
    },
    "tal": {
        "name": "🏜️ Tal Rashas Gräber",
        "keywords": ["tal rasha"],
    },
    "meph": {
        "name": "💀 Kerker des Hasses",
        "keywords": ["durance of hate"],
    },
    "chaos": {
        "name": "🔥 Chaos Sanktuarium",
        "keywords": ["chaos sanctuary"],
    },
    "wsk": {
        "name": "👑 Weltsteinturm",
        "keywords": ["worldstone", "throne of destruction", "worldstone chamber"],
    },
    "at": {
        "name": "🧊 Alte Tunnel",
        "keywords": ["ancient tunnels"],
    },
    "cows": {
        "name": "🐄 Kuhlevel",
        "keywords": ["moo moo farm"],
    },
    "pit": {
        "name": "🕳️ Grube",
        "keywords": ["pit"],
    },
    "andy": {
        "name": "🕷️ Andariel-Zone",
        "keywords": ["cathedral", "catacombs"],
    },
}


def normalize(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(
        url,
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        },
        timeout=20,
    )
    r.raise_for_status()


def fetch_next_zone():
    r = requests.get(
        API_URL,
        headers={"User-Agent": "D2-Terrorzone-Telegram-Bot/1.0"},
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


def get_active_zone_name(next_zone):
    zone_norm = normalize(next_zone)

    for code in ACTIVE_FAVORITES:
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
    next_zone = fetch_next_zone()

    if not next_zone:
        print("No valid next zone received. Skipping.")
        return

    active_zone_name = get_active_zone_name(next_zone)

    if not active_zone_name:
        print(f"No active favorite. Next TZ: {next_zone}")
        return

    send_telegram(
        f"🔥 <b>Terror Zone Alarm</b>\n\n"
        f"⏰ Start: {next_start_time()}\n\n"
        f"📍 {active_zone_name}"
    )


if __name__ == "__main__":
    main()
