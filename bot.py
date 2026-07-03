import json
import requests

from config import TELEGRAM_TOKEN, APP_NAME
from zones import ZONES

USERS_FILE = "users.json"


def load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    r = requests.post(url, json=payload, timeout=20)
    r.raise_for_status()


def build_message():
    return (
        f"📋 <b>{APP_NAME}</b>\n\n"
        f"Wähle deine Terrorzonen aus:"
    )


def build_zone_buttons(user):
    favorites = set(user.get("favorites", []))
    keyboard = []

    current_act = None

    for code, zone in ZONES.items():
        act = zone["act"]

        if act != current_act:
            keyboard.append([
                {
                    "text": act,
                    "callback_data": "noop"
                }
            ])
            current_act = act

        marker = "✅" if code in favorites else "❌"

        keyboard.append([
            {
                "text": f"{marker} {zone['name']}",
                "callback_data": f"toggle:{code}",
            }
        ])

    return {"inline_keyboard": keyboard}


def handle_list():
    users = load_users()

    for chat_id, user in users.items():
        send_message(
            chat_id,
            build_message(),
            reply_markup=build_zone_buttons(user),
        )


if __name__ == "__main__":
    handle_list()
