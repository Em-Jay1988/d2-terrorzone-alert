import os
import re
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

SOURCE_URL = "https://diablo2.io/tzonetracker.php"

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


def get_tracker_text():
    headers = {
        "User-Agent": "Mozilla/5.0 D2-TerrorZone-Telegram-Bot"
    }
    r = requests.get(SOURCE_URL, headers=headers, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    return soup.get_text("\n", strip=True)


def extract_next_zone(text):
    # Bereich nach "Next" nehmen
    parts = re.split(r"\bNext\b", text, flags=re.IGNORECASE)
    if len(parts) < 2:
        return ""

    next_part = parts[1]

    # Vor History abschneiden
    next_part = re.split(
        r"Online terror zones over the last|History|Current",
        next_part,
        flags=re.IGNORECASE,
    )[0]

    lines = [line.strip() for line in next_part.splitlines() if line.strip()]

    junk = [
        "timestamp",
        "automatically converted",
        "format is",
        "browser time",
        "immunities",
        "current",
        "next",
        "upcoming",
        "terror zones",
        "time zones",
    ]

    zone_lines = []
    for line in lines:
        low = line.lower()
        if any(j in low for j in junk):
            continue
        if re.match(r"^\d{4}-\d{2}-\d{2}", line):
            continue
        if len(line) < 3:
            continue
        zone_lines.append(line)

    return " / ".join(zone_lines[:5]).strip()


def is_watched(zone):
    z = normalize(zone)
    return any(keyword in z for keyword in WATCH_KEYWORDS)


def main():
    text = get_tracker_text()
    next_zone = extract_next_zone(text)

    manual_test = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"

    if not next_zone:
        msg = (
            "⚠️ <b>Bot läuft, aber konnte die nächste TZ nicht lesen.</b>\n\n"
            "Datenquelle hat vermutlich gerade keine Next-Zone veröffentlicht "
            "oder das Seitenformat hat sich geändert."
        )
        if manual_test:
            send_telegram(msg)
        raise RuntimeError("Next Terror Zone konnte nicht gelesen werden.")

    if is_watched(next_zone):
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
