"""Telegram delivery — deliberately kept OUTSIDE the agent loop.

See plan.md "Telegram delivery - kept outside the agent loop, deliberately":
Telegram's Bot API puts the auth token in the URL path
(`/bot<token>/sendMessage`), which Managed Agents vaults cannot substitute
(header/body only — see managed-agents-tools.md). Rather than build a custom
tool to work around that, this module is called directly by the webhook
handler once a session's final digest text is ready — plain, deterministic
backend code, never something a customer's Role/Subagent extension can
reach or alter.
"""

from __future__ import annotations

import httpx

TELEGRAM_API_BASE = "https://api.telegram.org"


def send_message(bot_token: str, chat_id: str, text: str) -> None:
    url = f"{TELEGRAM_API_BASE}/bot{bot_token}/sendMessage"
    response = httpx.post(url, json={"chat_id": chat_id, "text": text}, timeout=10.0)
    response.raise_for_status()


def send_digest(bot_token: str, chat_id: str, digest_text: str) -> None:
    send_message(bot_token, chat_id, digest_text)


def send_error_alert(bot_token: str, chat_id: str, summary: str) -> None:
    send_message(bot_token, chat_id, f"⚠️ {summary}")
