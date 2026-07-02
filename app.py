import os
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

API_URL = "https://d2runewizard.com/api/terror-zone"
LOCAL_TZ = ZoneInfo("Europe/Berlin")


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
    r = requests.get(API_URL, timeout=20)
    r.raise_for_status()
    return r.json().get("next", "Unknown")


def next_start_time():
    now = datetime.now(LOCAL_TZ)
    if now.minute < 30:
        start = now.replace(minute=30, second=0, microsecond=0)
    else:
        start = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    return start.strftime("%H:%M")


def main():
    next_zone = fetch_next_zone()

    send_telegram(
        f"🔥 <b>Terror Zone Alarm</b>\n\n"
        f"⏰ Start: {next_start_time()}\n\n"
        f"📍 {next_zone}"
    )


if __name__ == "__main__":
    main()
