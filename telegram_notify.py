#!/usr/bin/env python3
"""Send a message via the Telegram Bot API.

Usage:
    python3 telegram_notify.py "Your message here"

Required environment variables:
    TELEGRAM_BOT_TOKEN  - token from @BotFather (format: 123456789:ABC-DEF...)
    TELEGRAM_CHAT_ID    - target chat id

Set both as secrets in the routine/scheduled task that runs this script.
Never hardcode them here or commit them to the repo.
"""

import json
import os
import sys
import urllib.error
import urllib.request


def send_message(token: str, chat_id: str, text: str) -> dict:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Telegram API HTTP {e.code}: {body}") from e


def main() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print(
            "Error: TELEGRAM_BOT_TOKEN and/or TELEGRAM_CHAT_ID are not set.",
            file=sys.stderr,
        )
        return 1

    text = " ".join(sys.argv[1:]) or "Test message from the routine."

    result = send_message(token, chat_id, text)

    if result.get("ok"):
        print("Message sent successfully.")
        return 0
    else:
        print(f"Telegram API returned an error: {result}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
