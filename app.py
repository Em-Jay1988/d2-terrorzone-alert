import os
import re
import requests

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

D2EMU_API_URL = "https://d2emu.com/api/v1/tz"

ZONE_MAPPING = {
    33: "Cathedral",
    34: "Catacombs Level 1",
    35: "Catacombs Level 2",
    36: "Catacombs Level 3",
    37: "Catacombs Level 4",
    66: "Tal Rasha's Tomb #1",
    67: "Tal Rasha's Tomb #2",
    68: "Tal Rasha's Tomb #3",
    69: "Tal Rasha's Tomb #4",
    70: "Tal Rasha's Tomb #5",
    71: "Tal Rasha's Tomb #6",
    72: "Tal Rasha's Tomb #7",
    73: "Duriel's Lair",
    100: "Durance Of Hate Level 1",
    101: "Durance Of Hate Level 2",
    102: "Durance Of Hate Level 3",
    108: "Chaos Sanctuary",
    128: "The Worldstone Keep Level 1",
    129: "The Worldstone Keep Level 2",
    130: "The Worldstone Keep Level 3",
    131: "Throne Of Destruction",
    132: "The Worldstone Chamber",
}

WATCH_KEYWORDS = [
    "cathedral",
    "catacombs",
    "tal rasha",
    "duriel",
    "durance of hate",
    "chaos sanctuary",
    "worldstone",
    "throne of destruction",
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


def fetch_tz():
    r = requests.get(D2EMU_API_URL, timeout=20)
    r.raise_for_status()
    data = r.json()

    current_ids = data.get("current", [])
    next_ids = data.get("next", [])

    current_zones = [ZONE_MAPPING.get(int(i), f"Zone ID {i}") for i in current_ids]
    next_zones = [ZONE_MAPPING.get(int(i), f"Zone ID {i}") for i in next_ids]

    return current_zones, next_zones


def is_watched(zones):
    text = normalize(" ".join(zones))
    return any(keyword in text for keyword in WATCH_KEYWORDS)


def main():
    current_zones, next_zones = fetch_tz()
    manual_test = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"

    current_text = ", ".join(current_zones) if current_zones else "Unbekannt"
    next_text = ", ".join(next_zones) if next_zones else "Unbekannt"

    if is_watched(next_zones):
        send_telegram(
            f"🔥 <b>Terror Zone Alert</b>\n\n"
            f"In ca. 15 Minuten startet:\n"
            f"<b>{next_text}</b>\n\n"
            f"Aktuell:\n{current_text}"
        )
    elif manual_test:
        send_telegram(
            f"✅ <b>Bot-Test erfolgreich</b>\n\n"
            f"Aktuelle Terror Zone:\n"
            f"<b>{current_text}</b>\n\n"
            f"Nächste Terror Zone:\n"
            f"<b>{next_text}</b>\n\n"
            f"Diese Zone ist aktuell nicht auf deiner Boss-Liste."
        )
    else:
        print(f"Aktuell: {current_text}")
        print(f"Nächste: {next_text}")


if __name__ == "__main__":
    main()
