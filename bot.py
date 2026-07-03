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


def get_updates():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json().get("result", [])


def answer_callback(callback_id, text=""):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
    requests.post(url, json={"callback_query_id": callback_id, "text": text}, timeout=20)


def build_main_menu():
    return {
        "inline_keyboard": [
            [{"text": "⚔️ Akt I", "callback_data": "act:⚔️ Akt I"}],
            [{"text": "🏜️ Akt II", "callback_data": "act:🏜️ Akt II"}],
            [{"text": "🌴 Akt III", "callback_data": "act:🌴 Akt III"}],
            [{"text": "🔥 Akt IV", "callback_data": "act:🔥 Akt IV"}],
            [{"text": "👑 Akt V", "callback_data": "act:👑 Akt V"}],
            [
                {"text": "🔔 Alle aktiv", "callback_data": "all_on"},
                {"text": "🔕 Alle aus", "callback_data": "all_off"},
            ],
            [{"text": "💾 Speichern", "callback_data": "save"}],
        ]
    }


def build_act_menu(user, act_name):
    favorites = set(user.get("favorites", []))

    keyboard = []

    for code, zone in ZONES.items():
        if zone["act"] != act_name:
            continue

        marker = "✅" if code in favorites else "❌"
        keyboard.append([
            {
                "text": f"{marker} {zone['name']}",
                "callback_data": f"toggle:{code}",
            }
        ])

    keyboard.append([{"text": "⬅️ Zurück", "callback_data": "menu"}])

    return {"inline_keyboard": keyboard}


def handle_menu(chat_id):
    text = (
        f"📋 <b>{APP_NAME}</b>\n\n"
        f"Wähle einen Akt oder ändere alle Terrorzonen:"
    )
    send_message(chat_id, text, reply_markup=build_main_menu())


def handle_act(chat_id, user, act_name):
    text = f"<b>{act_name}</b>\n\nWähle deine Terrorzonen:"
    send_message(chat_id, text, reply_markup=build_act_menu(user, act_name))


def handle_updates():
    users = load_users()
    updates = get_updates()

    for update in updates:
        callback = update.get("callback_query")
        if not callback:
            continue

        callback_id = callback["id"]
        data = callback.get("data")
        chat_id = str(callback["message"]["chat"]["id"])

        user = users.get(chat_id)
        if not user:
            answer_callback(callback_id, "Du bist noch nicht registriert.")
            continue

        if data == "menu":
            answer_callback(callback_id)
            handle_menu(chat_id)

        elif data.startswith("act:"):
            act_name = data.replace("act:", "", 1)
            answer_callback(callback_id)
            handle_act(chat_id, user, act_name)

        elif data.startswith("toggle:"):
            code = data.replace("toggle:", "", 1)
            answer_callback(callback_id, f"{ZONES[code]['name']} ausgewählt.")

        elif data == "all_on":
            answer_callback(callback_id, "Alle aktiv kommt als nächstes.")

        elif data == "all_off":
            answer_callback(callback_id, "Alle aus kommt als nächstes.")

        elif data == "save":
            answer_callback(callback_id, "Speichern kommt als nächstes.")


def handle_start():
    users = load_users()
    for chat_id in users.keys():
        handle_menu(chat_id)


if __name__ == "__main__":
    handle_start()
    handle_updates()
