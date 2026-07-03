import os
import re
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

API_URL = "https://d2runewizard.com/api/terror-zone"
LOCAL_TZ = ZoneInfo("Europe/Berlin")

BOSS_ZONES = {
    "cathedral": "🕸️ Katakomben",
    "catacombs": "🕸️ Katakomben",
    "tal rasha": "🏜️ Tal Rashas Gräber",
    "durance of hate": "💀 Kerker des Hasses",
    "chaos sanctuary": "🔥 Chaos Sanktuarium",
    "worldstone": "👑 Weltsteinturm",
    "throne of destruction": "👑 Weltsteinturm",
    "worldstone chamber": "👑 Weltsteinturm",
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


def get_boss_zone_name(zone):
    zone_norm = normalize(zone)

    for keyword, display_name in BOSS_ZONES.items():
        if keyword in zone_norm:
            return display_name

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

    boss_zone = get_boss_zone_name(next_zone)

    if not boss_zone:
        print(f"No boss zone. Next TZ: {next_zone}")
        return

    send_telegram(
        f"🔥 <b>Terror Zone Alarm</b>\n\n"
        f"⏰ Start: {next_start_time()}\n\n"
        f"📍 {boss_zone}"
    )


if __name__ == "__main__":
    main()
