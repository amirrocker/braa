"""Per-customer configuration.

Matches plan.md's "Parameterization (per customer, no fixed values in code)":
nothing about a specific customer belongs in an agent's system prompt or in
code — it all lives here, loaded from that customer's own .env.

This is deliberately a single-customer config loader for the Phase 1 pilot.
Phase 2's move to one Anthropic workspace per customer (see plan.md's
"Multi-tenant isolation model") will need one of these per customer, not a
shared process-wide .env — don't build Phase-2 multi-tenancy on top of this
without revisiting how config gets loaded.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class OAuthCredential:
    access_token: str
    refresh_token: str
    client_id: str
    token_endpoint: str


@dataclass
class CustomerConfig:
    customer_id: str
    business_name: str

    mail_mcp_url: str
    calendar_mcp_url: str
    mail_oauth: OAuthCredential
    calendar_oauth: OAuthCredential

    telegram_bot_token: str
    telegram_chat_id: str

    digest_time: str  # "HH:MM", 24h, customer-local
    timezone: str  # IANA, e.g. "Europe/Berlin"

    email_criteria: str = "unread"  # "unread" | "flagged" | "all"
    email_sender_filters: list[str] = field(default_factory=list)
    email_lookback_hours: int = 2

    calendar_window_days: int = 7

    state_file: str = "./state/customer.json"

    def digest_cron(self) -> str:
        """Cron expression for the daily digest deployment (schedule.timezone carries the tz)."""
        hour, minute = self.digest_time.split(":")
        return f"{int(minute)} {int(hour)} * * *"


def load_customer_config(env_path: str | Path | None = None) -> CustomerConfig:
    """Load a CustomerConfig from environment variables (optionally from a .env file).

    Raises ValueError listing every missing required variable at once, rather
    than failing on the first one — cheaper to fix in one pass during onboarding.
    """
    if env_path is not None:
        load_dotenv(env_path)
    else:
        load_dotenv()  # picks up ./.env if present

    required = [
        "BERA_CUSTOMER_ID",
        "BERA_BUSINESS_NAME",
        "BERA_MAIL_MCP_URL",
        "BERA_CALENDAR_MCP_URL",
        "BERA_MAIL_OAUTH_ACCESS_TOKEN",
        "BERA_MAIL_OAUTH_REFRESH_TOKEN",
        "BERA_MAIL_OAUTH_CLIENT_ID",
        "BERA_MAIL_OAUTH_TOKEN_ENDPOINT",
        "BERA_CALENDAR_OAUTH_ACCESS_TOKEN",
        "BERA_CALENDAR_OAUTH_REFRESH_TOKEN",
        "BERA_CALENDAR_OAUTH_CLIENT_ID",
        "BERA_CALENDAR_OAUTH_TOKEN_ENDPOINT",
        "BERA_TELEGRAM_BOT_TOKEN",
        "BERA_TELEGRAM_CHAT_ID",
    ]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise ValueError(
            "Missing required config for this customer install: "
            + ", ".join(missing)
            + ". See orchestrator/.env.example — copy it to .env and fill these in "
            "(plan.md Phase 0/1: mailbox/calendar MCP + OAuth, and a Telegram bot "
            "the customer creates themselves via BotFather)."
        )

    sender_filters_raw = os.environ.get("BERA_EMAIL_SENDER_FILTERS", "")
    sender_filters = [s.strip() for s in sender_filters_raw.split(",") if s.strip()]

    return CustomerConfig(
        customer_id=os.environ["BERA_CUSTOMER_ID"],
        business_name=os.environ["BERA_BUSINESS_NAME"],
        mail_mcp_url=os.environ["BERA_MAIL_MCP_URL"],
        calendar_mcp_url=os.environ["BERA_CALENDAR_MCP_URL"],
        mail_oauth=OAuthCredential(
            access_token=os.environ["BERA_MAIL_OAUTH_ACCESS_TOKEN"],
            refresh_token=os.environ["BERA_MAIL_OAUTH_REFRESH_TOKEN"],
            client_id=os.environ["BERA_MAIL_OAUTH_CLIENT_ID"],
            token_endpoint=os.environ["BERA_MAIL_OAUTH_TOKEN_ENDPOINT"],
        ),
        calendar_oauth=OAuthCredential(
            access_token=os.environ["BERA_CALENDAR_OAUTH_ACCESS_TOKEN"],
            refresh_token=os.environ["BERA_CALENDAR_OAUTH_REFRESH_TOKEN"],
            client_id=os.environ["BERA_CALENDAR_OAUTH_CLIENT_ID"],
            token_endpoint=os.environ["BERA_CALENDAR_OAUTH_TOKEN_ENDPOINT"],
        ),
        telegram_bot_token=os.environ["BERA_TELEGRAM_BOT_TOKEN"],
        telegram_chat_id=os.environ["BERA_TELEGRAM_CHAT_ID"],
        digest_time=os.environ.get("BERA_DIGEST_TIME", "09:00"),
        timezone=os.environ.get("BERA_TIMEZONE", "Europe/Berlin"),
        email_criteria=os.environ.get("BERA_EMAIL_CRITERIA", "unread"),
        email_sender_filters=sender_filters,
        email_lookback_hours=int(os.environ.get("BERA_EMAIL_LOOKBACK_HOURS", "2")),
        calendar_window_days=int(os.environ.get("BERA_CALENDAR_WINDOW_DAYS", "7")),
        state_file=os.environ.get("BERA_STATE_FILE", "./state/customer.json"),
    )


# --- Provisioned-resource state (agent/environment/vault/deployment IDs) ---
#
# "Agents are persistent - create once, reference by ID" (claude-api skill,
# Managed Agents). This is the on-disk record of what's already been
# provisioned for one customer, so `bera-setup` is safe to re-run without
# creating duplicate agents/deployments — see provisioning.py.


@dataclass
class ProvisionedState:
    environment_id: str | None = None
    galileo_agent_id: str | None = None
    galileo_agent_version: int | None = None
    email_management_agent_id: str | None = None
    termin_management_agent_id: str | None = None
    vault_id: str | None = None
    hourly_deployment_id: str | None = None
    digest_deployment_id: str | None = None
    # roster entries added via the orchestrator-mediated "add role" path
    # (plan.md "Core-lock enforcement" — this is the only supported way
    # Galileo's roster grows beyond the two built-in subagents).
    custom_roster_agent_ids: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: str | Path) -> "ProvisionedState":
        p = Path(path)
        if not p.exists():
            return cls()
        return cls(**json.loads(p.read_text()))

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(asdict(self), indent=2))
