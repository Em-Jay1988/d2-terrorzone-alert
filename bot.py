import json
import requests

from config import TELEGRAM_TOKEN, APP_NAME
from zones import ZONES


USERS_FILE = "users.json"


def load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        },
        timeout=20,
    )
    r.raise_for_status()


def build_list_message(user):
    favorites = set(user.get("favorites", []))

    lines = [f"📋 <b>{APP_NAME}</b>", ""]

    current_act = None

    for code, zone in ZONES.items():
        act = zone.get("act", "Sonstige")

        if act != current_act:
            if current_act is not None:
                lines.append("")
            lines.append(f"<b>{act}</b>")
            current_act = act

        marker = "✅" if code in favorites else "❌"
        lines.append(f"{marker} <code>{code}</code>  {zone['name']}")

    lines.append("")
    lines.append("Tippe später auf Buttons, um Favoriten zu ändern.")

    return "\n".join(lines)


def handle_list():
    users = load_users()

    for chat_id, user in users.items():
        send_message(chat_id, build_list_message(user))


if __name__ == "__main__":
    handle_list()
