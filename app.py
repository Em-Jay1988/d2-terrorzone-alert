import os
import re
import requests
from datetime import datetime, timedelta, timezone

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
API_URL = "https://d2runewizard.com/api/terror-zone"

WATCH_ZONES = {
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
        json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"},
        timeout=20,
    )
    r.raise_for_status()


def fetch_next_zone():
    r = requests.get(API_URL, timeout=20)
    r.raise_for_status()
    return r.json().get("next", "Unbekannt")


def get_watched_name(zone):
    z = normalize(zone)
    for keyword, german_name in WATCH_ZONES.items():
        if keyword in z:
            return german_name
    return None


def next_start_time_germany():
    now = datetime.now(timezone.utc) + timedelta(hours=1)
    minute = 30 if now.minute < 30 else 0
    hour = now.hour if minute == 30 else (now.hour + 1) % 24
    return f"{hour:02d}:{minute:02d}"


def main():
    next_zone = fetch_next_zone()
    german_name = get_watched_name(next_zone)
    manual_test = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"

    if german_name:
        send_telegram(
            f"🔥 <b>Terror Zone Alarm</b>\n\n"
            f"⏰ Start: {next_start_time_germany()}\n\n"
            f"📍 {german_name}"
        )
    elif manual_test:
        send_telegram(
            f"✅ <b>Bot-Test erfolgreich</b>\n\n"
            f"Nächste TZ: {next_zone}\n"
            f"Kein Alarm, nicht auf deiner Liste."
        )
    else:
        print(f"Keine Wunschzone. Nächste TZ: {next_zone}")


if __name__ == "__main__":
    main()
