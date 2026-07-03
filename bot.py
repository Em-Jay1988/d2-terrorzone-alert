import json
import requests

from config import TELEGRAM_TOKEN, APP_NAME
from zones import ZONES

USERS_FILE = "users.json"

ACTS = [
    ("act1", "⚔️ Akt I"),
    ("act2", "🏜️ Akt II"),
    ("act3", "🌴 Akt III"),
    ("act4", "🔥 Akt IV"),
    ("act5", "👑 Akt V"),
]

ACT_BY_KEY = dict(ACTS)


def load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_regular_users(data):
    return {k: v for k, v in data.items() if not k.startswith("_")}


def telegram(method, payload=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}"
    r = requests.post(url, json=payload or {}, timeout=20)
    r.raise_for_status()
    return r.json()


def get_updates(offset):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    r = requests.get(url, params={"offset": offset}, timeout=20)
    r.raise_for_status()
    return r.json().get("result", [])


def answer_callback(callback_id, text=""):
    telegram("answerCallbackQuery", {
        "callback_query_id": callback_id,
        "text": text,
    })


def send_message(chat_id, text, reply_markup):
    telegram("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": reply_markup,
    })


def edit_message(chat_id, message_id, text, reply_markup):
    telegram("editMessageText", {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": reply_markup,
    })


def build_main_text():
    return f"📋 <b>{APP_NAME}</b>\n\nWähle einen Akt oder ändere alle Terrorzonen:"


def build_main_menu():
    keyboard = []

    for act_key, act_name in ACTS:
        keyboard.append([{"text": act_name, "callback_data": f"act:{act_key}"}])

    keyboard.append([
        {"text": "🔔 Alle aktiv", "callback_data": "all_on"},
        {"text": "🔕 Alle aus", "callback_data": "all_off"},
    ])

    keyboard.append([{"text": "💾 Speichern", "callback_data": "save"}])

    return {"inline_keyboard": keyboard}


def build_act_text(act_key):
    return f"<b>{ACT_BY_KEY[act_key]}</b>\n\nWähle deine Terrorzonen:"


def build_act_menu(user, act_key):
    act_name = ACT_BY_KEY[act_key]
    favorites = set(user.get("favorites", []))
    keyboard = []

    for code, zone in ZONES.items():
        if zone["act"] != act_name:
            continue

        marker = "✅" if code in favorites else "❌"
        keyboard.append([{
            "text": f"{marker} {zone['name']}",
            "callback_data": f"toggle:{code}:{act_key}",
        }])

    keyboard.append([{"text": "⬅️ Zurück", "callback_data": "menu"}])
    return {"inline_keyboard": keyboard}


def show_main_menu(data):
    for chat_id in get_regular_users(data).keys():
        send_message(chat_id, build_main_text(), build_main_menu())


def handle_callbacks(data):
    meta = data.setdefault("_meta", {})
    last_update_id = meta.get("last_update_id", 0)

    updates = get_updates(last_update_id + 1)
    changed = False

    for update in updates:
        meta["last_update_id"] = max(meta.get("last_update_id", 0), update["update_id"])

        callback = update.get("callback_query")
        if not callback:
            continue

        callback_id = callback["id"]
        payload = callback.get("data", "")
        message = callback["message"]
        chat_id = str(message["chat"]["id"])
        message_id = message["message_id"]

        user = data.get(chat_id)
        if not user:
            answer_callback(callback_id, "Nicht registriert.")
            continue

        favorites = user.setdefault("favorites", [])

        if payload == "menu":
            answer_callback(callback_id)
            edit_message(chat_id, message_id, build_main_text(), build_main_menu())

        elif payload.startswith("act:"):
            act_key = payload.split(":", 1)[1]
            answer_callback(callback_id)
            edit_message(chat_id, message_id, build_act_text(act_key), build_act_menu(user, act_key))

        elif payload.startswith("toggle:"):
            _, code, act_key = payload.split(":", 2)

            if code in favorites:
                favorites.remove(code)
                answer_callback(callback_id, f"{ZONES[code]['name']} deaktiviert")
            else:
                favorites.append(code)
                answer_callback(callback_id, f"{ZONES[code]['name']} aktiviert")

            changed = True
            edit_message(chat_id, message_id, build_act_text(act_key), build_act_menu(user, act_key))

        elif payload == "all_on":
            user["favorites"] = list(ZONES.keys())
            changed = True
            answer_callback(callback_id, "Alle aktiviert")
            edit_message(chat_id, message_id, build_main_text(), build_main_menu())

        elif payload == "all_off":
            user["favorites"] = []
            changed = True
            answer_callback(callback_id, "Alle deaktiviert")
            edit_message(chat_id, message_id, build_main_text(), build_main_menu())

        elif payload == "save":
            answer_callback(callback_id, "Gespeichert ✅")

    return changed or bool(updates)


if __name__ == "__main__":
    data = load_users()

    # Sendet Menü immer beim manuellen Workflow-Start
    show_main_menu(data)

    # Verarbeitet Button-Klicks seit letztem Lauf
    changed = handle_callbacks(data)

    if changed:
        save_users(data)
