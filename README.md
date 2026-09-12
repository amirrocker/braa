# techkomp — Telegram routine notifier

Small script used by a scheduled Claude routine to send a Telegram message. Background/history: [TECHKOMP_ROUTINE_TEST.md](TECHKOMP_ROUTINE_TEST.md).

## Before doing anything else: rotate the old bot token

The token that was used during testing was pasted in plaintext in a chat and sat in a local `telegram_credentials` file (excluded from git via `.gitignore`, but do not commit it manually either). Treat it as burned:

1. Telegram: message `@BotFather` → `/mybots` → select the bot → **API Token** → **Revoke current token** → copy the new one.
2. Delete or overwrite the local `telegram_credentials` file once you've saved the new token somewhere safe (password manager, not this repo).

## Files

- `telegram_notify.py` — sends one Telegram message. Reads the token and chat id from environment variables, takes the message text as CLI arguments.
- `.env.example` — names the two required environment variables. Copy to `.env` for local testing only; `.env` is gitignored and must never be committed.

## Local test

```bash
TELEGRAM_BOT_TOKEN="<new token>" TELEGRAM_CHAT_ID="5651884705" python3 telegram_notify.py "Test"
```

## Wiring up the routine (Claude app UI)

When creating the scheduled routine and pointing it at this repo:

1. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as the routine's secrets/environment variables — not in the prompt text.
2. Routine prompt should just run:
   ```bash
   python3 telegram_notify.py "Routine läuft ✅ (stündlicher Test)"
   ```
3. Delete the old cloud trigger (`trig_019bky4wn9XEU4dVenf6fiYU` from the prior test) once this repo-backed routine is confirmed working, to stop the duplicate hourly pings.
