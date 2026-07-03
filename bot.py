import json
from collections import Counter
import requests

from config import TELEGRAM_TOKEN, APP_NAME, ADMIN_CHAT_ID
from zones import ZONES

USERS_FILE = "users.json"
DEFAULT_FAVORITES = ["kata", "tal", "meph", "chaos", "wsk"]


def load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def real_users(data):
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


def send_message(chat_id, text):
    telegram("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    })


def build_list(user):
    favorites = set(user.get("favorites", []))
    lines = [f"📋 <b>{APP_NAME}</b>", ""]

    current_act = None
    for code, zone in ZONES.items():
        act = zone["act"]
        if act != current_act:
            if current_act is not None:
                lines.append("")
            lines.append(f"<b>{act}</b>")
            current_act = act

        marker = "✅" if code in favorites else "❌"
        lines.append(f"{marker} <code>{code}</code>  {zone['name']}")

    lines.append("")
    lines.append("<b>Befehle:</b>")
    lines.append("<code>/watch chaos</code>")
    lines.append("<code>/unwatch chaos</code>")
    lines.append("<code>/stop</code>")
    return "\n".join(lines)


def build_admin(data):
    users = real_users(data)
    counter = Counter()

    for user in users.values():
        counter.update(user.get("favorites", []))

    lines = ["🛠️ <b>Admin Übersicht</b>", ""]
    lines.append(f"Registrierte Nutzer: <b>{len(users)}</b>")
    lines.append("")
    lines.append("<b>Top Terrorzonen:</b>")

    if not counter:
        lines.append("Noch keine Favoriten.")
    else:
        for i, (code, count) in enumerate(counter.most_common(5), start=1):
            zone_name = ZONES.get(code, {}).get("name", code)
            lines.append(f"{i}. {zone_name} – {count} Nutzer")

    lines.append("")
    lines.append("<code>/users</code> – Nutzerliste anzeigen")
    return "\n".join(lines)


def build_users(data):
    users = real_users(data)
    lines = ["👥 <b>Registrierte Nutzer</b>", ""]

    for chat_id, user in users.items():
        name = user.get("name", "User")
        favorites = user.get("favorites", [])
        lines.append(f"• <b>{name}</b> – {len(favorites)} Favoriten")

    return "\n".join(lines)


def handle_command(chat_id, user, text, data):
    parts = text.strip().split()
    command = parts[0].lower()

    if command in ["/start", "/register"]:
        send_message(
            chat_id,
            f"✅ Willkommen bei <b>{APP_NAME}</b>, {user.get('name', 'User')}!\n\n"
            f"Du wurdest automatisch registriert.\n\n"
            f"Nutze <code>/list</code>, um deine Zonen zu sehen."
        )
        return True

    if command == "/help":
        send_message(
            chat_id,
            f"🎮 <b>{APP_NAME}</b>\n\n"
            f"<code>/list</code> – Favoriten anzeigen\n"
            f"<code>/watch chaos</code> – Zone aktivieren\n"
            f"<code>/unwatch chaos</code> – Zone deaktivieren\n"
            f"<code>/stop</code> – Registrierung löschen"
        )
        return True

    if command == "/list":
        send_message(chat_id, build_list(user))
        return True

    if command == "/stop":
        if chat_id in data:
            name = data[chat_id].get("name", "User")
            del data[chat_id]
            send_message(chat_id, f"🛑 Registrierung gelöscht. Mach's gut, <b>{name}</b>.")
        return True

    if command == "/admin":
        if chat_id != ADMIN_CHAT_ID:
            send_message(chat_id, "Keine Berechtigung.")
            return True
        send_message(chat_id, build_admin(data))
        return True

    if command == "/users":
        if chat_id != ADMIN_CHAT_ID:
            send_message(chat_id, "Keine Berechtigung.")
            return True
        send_message(chat_id, build_users(data))
        return True

    if command in ["/watch", "/unwatch"]:
        if len(parts) < 2:
            send_message(chat_id, "Bitte Kürzel angeben, z. B. <code>/watch chaos</code>.")
            return True

        code = parts[1].lower()

        if code not in ZONES:
            send_message(chat_id, f"Unbekanntes Kürzel: <code>{code}</code>\n\nNutze <code>/list</code>.")
            return True

        favorites = user.setdefault("favorites", [])

        if command == "/watch":
            if code not in favorites:
                favorites.append(code)
            send_message(chat_id, f"✅ Aktiviert: {ZONES[code]['name']}")
            return True

        if command == "/unwatch":
            if code in favorites:
                favorites.remove(code)
            send_message(chat_id, f"❌ Deaktiviert: {ZONES[code]['name']}")
            return True

    return False


def main():
    data = load_users()
    meta = data.setdefault("_meta", {})
    last_update_id = meta.get("last_update_id", 0)

    updates = get_updates(last_update_id + 1)
    changed = False

    for update in updates:
        meta["last_update_id"] = max(meta.get("last_update_id", 0), update["update_id"])

        message = update.get("message")
        if not message:
            continue

        chat_id = str(message["chat"]["id"])
        text = message.get("text", "")

        if chat_id not in data:
            data[chat_id] = {
                "name": message["chat"].get("first_name", "User"),
                "favorites": DEFAULT_FAVORITES.copy(),
            }
            changed = True

        user = data[chat_id]

        if text.startswith("/"):
            if handle_command(chat_id, user, text, data):
                changed = True

    if changed:
        save_users(data)


if __name__ == "__main__":
    main()
