import os
from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 156340449
API = f"https://api.telegram.org/bot{TOKEN}"

# Likes are stored here temporarily.
# We will add permanent storage in the next step.
likes = {}


def telegram(method, data=None):
    return requests.post(
        f"{API}/{method}",
        json=data or {},
        timeout=15
    ).json()


@app.route("/", methods=["GET"])
def home():
    return "Nasim Music Bot is running ❤️", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}

    # Someone pressed the Like button
    if "callback_query" in update:
        query = update["callback_query"]
        user = query["from"]
        message = query.get("message", {})
        data = query.get("data", "")

        if data.startswith("like:"):
            post_id = data.split(":", 1)[1]

            if post_id not in likes:
                likes[post_id] = {}

            user_id = str(user["id"])

            # Pressing again removes the like
            if user_id in likes[post_id]:
                del likes[post_id][user_id]
                status = "Like removed 🤍"
            else:
                likes[post_id][user_id] = {
                    "first_name": user.get("first_name", ""),
                    "last_name": user.get("last_name", ""),
                    "username": user.get("username", "")
                }
                status = "Liked ❤️"

            count = len(likes[post_id])

            # Update the number shown on the button
            if message:
                telegram("editMessageReplyMarkup", {
                    "chat_id": message["chat"]["id"],
                    "message_id": message["message_id"],
                    "reply_markup": {
                        "inline_keyboard": [[
                            {
                                "text": f"❤️ I Like It · {count}",
                                "callback_data": f"like:{post_id}"
                            }
                        ]]
                    }
                })

            # Small popup shown to the person who pressed the button
            telegram("answerCallbackQuery", {
                "callback_query_id": query["id"],
                "text": status
            })

        return "ok", 200

    # Private messages sent to the bot
    message = update.get("message")

    if message:
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        text = message.get("text", "")

        # Only Nasim can see the list of people who liked a post
        if user_id == ADMIN_ID and text.startswith("/likes"):
            parts = text.split()

            if len(parts) < 2:
                telegram("sendMessage", {
                    "chat_id": chat_id,
                    "text": "برای دیدن لایک‌ها بنویس:\n/likes شماره‌پست"
                })
                return "ok", 200

            post_id = parts[1]
            people = likes.get(post_id, {})

            if not people:
                result = "هنوز کسی این پست را لایک نکرده ❤️"

            else:
                rows = []

                for person in people.values():
                    name = (
                        person["first_name"] + " " +
                        person["last_name"]
                    ).strip()

                    username = person["username"]

                    if username:
                        rows.append(
                            f"❤️ {name} — @{username}"
                        )
                    else:
                        rows.append(
                            f"❤️ {name}"
                        )

                result = "\n".join(rows)

            telegram("sendMessage", {
                "chat_id": chat_id,
                "text": result
            })

        elif user_id == ADMIN_ID and text == "/start":
            telegram("sendMessage", {
                "chat_id": chat_id,
                "text": "NASIMISMBOT is ready ❤️"
            })

    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
