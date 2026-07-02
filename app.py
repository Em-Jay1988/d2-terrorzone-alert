import os
import re
import requests

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

API_URL = "https://d2runewizard.com/api/terror-zone"

WATCH_KEYWORDS = [
    "catacombs",
    "tal rasha",
    "durance of hate",
    "chaos sanctuary",
    "worldstone keep",
    "throne of destruction",
    "worldstone chamber",
]


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


def fetch_terror_zone():
    r = requests.get(API_URL, timeout=20)
    r.raise_for_status()
    data = r.json()

    current_zone = data.get("current", "Unbekannt")
    next_zone = data.get("next", "Unbekannt")

    return current_zone, next_zone


def is_watched(zone):
    zone_norm = normalize(zone)
    return any(keyword in zone_norm for keyword in WATCH_KEYWORDS)


def main():
    current_zone, next_zone = fetch_terror_zone()
    manual_test = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"

    if is_watched(next_zone):
        send_telegram(
            f"🔥 <b>Terror Zone Alert</b>\n\n"
            f"In ca. 15 Minuten startet:\n"
            f"<b>{next_zone}</b>\n\n"
            f"Aktuell:\n"
            f"{current_zone}"
        )
    elif manual_test:
        send_telegram(
            f"✅ <b>Bot-Test erfolgreich</b>\n\n"
            f"Aktuelle Terror Zone:\n"
            f"<b>{current_zone}</b>\n\n"
            f"Nächste Terror Zone:\n"
            f"<b>{next_zone}</b>\n\n"
            f"Diese Zone ist aktuell nicht auf deiner Boss-Liste."
        )
    else:
        print(f"Aktuelle TZ: {current_zone}")
        print(f"Nächste TZ: {next_zone}")
        print("Keine Wunschzone.")


if __name__ == "__main__":
    main()
