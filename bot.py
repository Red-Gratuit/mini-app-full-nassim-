#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mini app boutique + bot Telegram pour Railway."""

import json
import os

import requests
from flask import Flask, jsonify, request, send_from_directory

BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else ""
CANAL_URL = "https://t.me/+QmM6N0VtnDllYzBk"
CONTACT_URL = "https://snapchat.com/add/El.Doctor59"


def build_mini_app_url():
    mini_app_url = os.environ.get("MINI_APP_URL") or os.environ.get("RAILWAY_PUBLIC_DOMAIN") or ""
    if not mini_app_url:
        return "https://example.com"
    if not mini_app_url.startswith("http://") and not mini_app_url.startswith("https://"):
        return "https://" + mini_app_url
    return mini_app_url.rstrip("/")


MINI_APP_URL = build_mini_app_url()
app = Flask(__name__, static_url_path="", static_folder=".")


def send_message(chat_id, text, reply_markup=None):
    if not BOT_TOKEN:
        return None
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = reply_markup
    try:
        response = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=data, timeout=15)
        return response.json()
    except Exception as exc:
        print(f"Erreur envoi message: {exc}")
        return None


def send_photo(chat_id, caption, reply_markup=None):
    if not BOT_TOKEN:
        return None
    data = {"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = reply_markup

    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")
    if not os.path.exists(logo_path):
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")

    try:
        with open(logo_path, "rb") as photo:
            files = {"photo": photo}
            response = requests.post(f"{TELEGRAM_API_URL}/sendPhoto", files=files, data=data, timeout=15)
            return response.json()
    except FileNotFoundError:
        return send_message(chat_id, caption, reply_markup)
    except Exception as exc:
        print(f"Erreur envoi photo: {exc}")
        return send_message(chat_id, caption, reply_markup)


def handle_start(chat_id):
    caption = """🌟 BIENVENUE CHEZ El Doctor 🌟
NOUS TE LAISSONS NAVIGUER SUR NOTRE MINI-APP 📱
🔥 Produits Premium - 59-62 🔥"""

    reply_markup = {
        "inline_keyboard": [
            [{"text": "📢 CANAL TELEGRAM ↗", "url": CANAL_URL}],
            [{"text": "📸 SNAPCHAT ↗", "url": CONTACT_URL}],
            [{"text": "📱 MENU MINI-APP", "web_app": {"url": MINI_APP_URL}}],
        ]
    }

    result = send_photo(chat_id, caption, json.dumps(reply_markup))
    if not result or not result.get("ok"):
        send_message(chat_id, f"🌟 **BIENVENUE CHEZ El Doctor** 🌟\n\n{caption}", json.dumps(reply_markup))


def handle_message(update):
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if not chat_id or not text:
        return

    if text == "/start":
        handle_start(chat_id)
    else:
        send_message(chat_id, "Utilisez /start pour accéder à la mini-app El Doctor 🌿")


def set_webhook(webhook_url):
    if not BOT_TOKEN:
        print("BOT_TOKEN non défini, webhook non configuré.")
        return False
    try:
        response = requests.post(f"{TELEGRAM_API_URL}/setWebhook", json={"url": webhook_url}, timeout=15)
        result = response.json()
        if result.get("ok"):
            print(f"✅ Webhook configuré: {webhook_url}")
            return True
        print(f"❌ Erreur webhook: {result}")
        return False
    except Exception as exc:
        print(f"Erreur configuration webhook: {exc}")
        return False


@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "mini-app-shop"})


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/<path:path>")
def static_files(path):
    safe_path = os.path.join(app.static_folder, path)
    if os.path.exists(safe_path) and not os.path.isdir(safe_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


@app.post("/webhook")
def webhook():
    payload = request.get_json(silent=True) or {}
    handle_message(payload)
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    webhook_url = os.environ.get("WEBHOOK_URL") or os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    if webhook_url and not webhook_url.startswith("http"):
        webhook_url = "https://" + webhook_url
    if webhook_url:
        set_webhook(f"{webhook_url.rstrip('/')}/webhook")
    app.run(host="0.0.0.0", port=port, debug=False)
