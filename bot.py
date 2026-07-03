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


def build_main_menu():
    return {
        "inline_keyboard": [
            [{"text": "⚔️ Akt I", "callback_data": "act:Akt I"}],
            [{"text": "🏜️ Akt II", "callback_data": "act:Akt II"}],
            [{"text": "🌴 Akt III", "callback_data": "act:Akt III"}],
            [{"text": "🔥 Akt IV", "callback_data": "act:Akt IV"}],
            [{"text": "👑 Akt V", "callback_data": "act:Akt V"}],
            [
                {"text": "🔔 Alle aktiv", "callback_data": "all_on"},
                {"text": "🔕 Alle aus", "callback_data": "all_off"},
            ],
            [{"text": "💾 Speichern", "callback_data": "save"}],
        ]
    }


def handle_menu():
    users = load_users()

    text = (
        f"📋 <b>{APP_NAME}</b>\n\n"
        f"Wähle einen Akt oder ändere alle Terrorzonen:"
    )

    for chat_id in users.keys():
        send_message(chat_id, text, reply_markup=build_main_menu())


if __name__ == "__main__":
    handle_menu()
