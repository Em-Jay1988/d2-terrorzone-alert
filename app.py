import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

WATCH_ZONES = [
    "Cathedral and Catacombs",
    "Tal Rasha's Tombs",
    "Durance of Hate",
    "The Chaos Sanctuary",
    "Worldstone Keep, Throne of Destruction, and Worldstone Chamber",
]

D2EMU_URL = "https://d2emu.com/tz"


def normalize(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def get_next_terror_zone():
    response = requests.get(D2EMU_URL, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text("\n", strip=True)

    match = re.search(
        r"Next Terror Zone:\s*(.*?)\s*Terror Zone has monsters",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    if not match:
        raise RuntimeError("Konnte die nächste Terror Zone nicht auslesen.")

    return " ".join(match.group(1).split())


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    response = requests.post(
        url,
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        },
        timeout=20,
    )
    response.raise_for_status()


def main():
    next_zone = get_next_terror_zone()
    next_zone_norm = normalize(next_zone)

    watched = any(normalize(zone) in next_zone_norm for zone in WATCH_ZONES)

    manual_test = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"

    if watched:
        send_telegram(
            f"🔥 <b>Terror Zone Alert</b>\n\n"
            f"In ca. 15 Minuten startet:\n"
            f"<b>{next_zone}</b>"
        )
    elif manual_test:
        send_telegram(
            f"✅ <b>Bot-Test erfolgreich</b>\n\n"
            f"Nächste Terror Zone:\n"
            f"<b>{next_zone}</b>\n\n"
            f"Diese Zone ist aktuell nicht auf deiner Boss-Liste."
        )
    else:
        print(f"Keine Wunschzone. Nächste TZ: {next_zone}")


if __name__ == "__main__":
    main()
