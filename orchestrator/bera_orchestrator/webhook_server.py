"""Webhook receiver: Anthropic -> this service, for deployment_run and
vault-credential events. This is the piece of B&R's orchestrator that turns
"a scheduled session finished" into "a Telegram message got sent" — see
plan.md's Telegram-delivery design.

Register this endpoint's URL in Console -> Manage -> Webhooks, subscribed to
at least: deployment_run.succeeded, deployment_run.failed,
vault_credential.refresh_failed. (Endpoint registration has no API yet —
Console only, per managed-agents-webhooks.md.)

Payloads are thin by design (event type + resource ID only) — every handler
below re-fetches the resource before acting on it, per Anthropic's own
guidance, rather than trusting anything beyond IDs in the payload.
"""

from __future__ import annotations

import logging

import anthropic
from flask import Flask, request

from .config import CustomerConfig, ProvisionedState, load_customer_config
from .telegram import send_digest, send_error_alert

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bera_orchestrator.webhook_server")

# Dedupe by webhook event id — deliveries can repeat (see managed-agents-webhooks.md
# "Duplicates"). A process-local set is fine for Phase 1's single pilot customer;
# Phase 2's multi-instance orchestrator needs a shared store (Redis/DB) instead.
_seen_event_ids: set[str] = set()


def _get_last_agent_message_text(client: anthropic.Anthropic, session_id: str) -> str:
    """Concatenate the text blocks of the LAST agent.message on the primary
    thread — this is Galileo's final report (the digest text, or the hourly
    urgent-check verdict), per how prompts.py instructs it to respond.

    NOTE: assumes the session's event history fits in one page. A very long
    session (shouldn't happen for this workload) would need pagination —
    not handled here.
    """
    events = client.beta.sessions.events.list(session_id=session_id)
    last_text = ""
    for event in events.data:
        if event.type == "agent.message":
            text = "".join(
                block.text for block in event.content if getattr(block, "type", None) == "text"
            )
            if text:
                last_text = text
    return last_text


def _handle_deployment_run_succeeded(
    client: anthropic.Anthropic, config: CustomerConfig, state: ProvisionedState, run_id: str
) -> None:
    run = client.beta.deployment_runs.retrieve(run_id)
    if run.session_id is None:
        logger.warning("deployment_run %s succeeded with no session_id — unexpected", run_id)
        return

    session = client.beta.sessions.retrieve(run.session_id)
    if session.status != "terminated":
        # Not done yet (e.g. this webhook can arrive before status_terminated
        # in rare orderings — see "No ordering guarantee"). Nothing to send yet.
        logger.info("session %s not terminated yet (status=%s), skipping", session.id, session.status)
        return

    final_text = _get_last_agent_message_text(client, run.session_id)

    if run.deployment_id == state.digest_deployment_id:
        if final_text:
            send_digest(config.telegram_bot_token, config.telegram_chat_id, final_text)
        else:
            send_error_alert(
                config.telegram_bot_token,
                config.telegram_chat_id,
                "Morning digest session finished but produced no output — check the session in Console.",
            )
    elif run.deployment_id == state.hourly_deployment_id:
        if final_text and final_text.strip() != "NO_URGENT_FINDINGS":
            send_message_for_hourly_alert(config, final_text)
    else:
        logger.warning("deployment_run %s for unknown deployment %s", run_id, run.deployment_id)


def send_message_for_hourly_alert(config: CustomerConfig, text: str) -> None:
    from .telegram import send_message

    send_message(config.telegram_bot_token, config.telegram_chat_id, f"⏱️ {text}")


def _handle_deployment_run_failed(client: anthropic.Anthropic, config: CustomerConfig, run_id: str) -> None:
    run = client.beta.deployment_runs.retrieve(run_id)
    send_error_alert(
        config.telegram_bot_token,
        config.telegram_chat_id,
        f"An automated check failed to start: {run.error.type if run.error else 'unknown error'}. "
        "This needs attention — it won't retry on its own.",
    )


def _handle_vault_credential_refresh_failed(config: CustomerConfig, credential_id: str) -> None:
    send_error_alert(
        config.telegram_bot_token,
        config.telegram_chat_id,
        "Your mailbox/calendar connection needs to be reconnected — the stored "
        "access has expired or was revoked. Automated checks are paused until this is fixed.",
    )


def create_app(config: CustomerConfig | None = None) -> Flask:
    config = config or load_customer_config()
    state = ProvisionedState.load(config.state_file)
    client = anthropic.Anthropic()  # reads ANTHROPIC_WEBHOOK_SIGNING_KEY + ANTHROPIC_API_KEY from env

    app = Flask(__name__)

    @app.route("/webhook", methods=["POST"])
    def webhook():
        try:
            event = client.beta.webhooks.unwrap(
                request.get_data(as_text=True),
                headers=dict(request.headers),
            )
        except Exception:
            logger.exception("webhook signature verification failed")
            return "invalid signature", 400

        if event.id in _seen_event_ids:
            return "", 204
        _seen_event_ids.add(event.id)

        try:
            event_type = event.data.type
            if event_type == "deployment_run.succeeded":
                _handle_deployment_run_succeeded(client, config, state, event.data.id)
            elif event_type == "deployment_run.failed":
                _handle_deployment_run_failed(client, config, event.data.id)
            elif event_type == "vault_credential.refresh_failed":
                _handle_vault_credential_refresh_failed(config, event.data.id)
            # else: not subscribed to / not relevant
        except Exception:
            # Never let a handler exception surface as a 5xx that Anthropic
            # will retry into a repeat Telegram alert — log and ack.
            logger.exception("error handling webhook event %s (%s)", event.id, event.data.type)

        return "", 204

    return app
