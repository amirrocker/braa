"""One-time provisioning of a customer's Managed Agents resources.

Implements plan.md Phase 1: 3 agents (Galileo coordinator + Email Management
+ Termin Management), 1 vault, 2 scheduled deployments (hourly check, daily
digest). Every function here is a SETUP operation — "Agent ONCE, not every
run" — so each one checks `ProvisionedState` first and reuses an existing
resource instead of creating a duplicate. Run this via `bera-setup` during
onboarding, not from a request path.

NOTE on unverified call shapes: the vault-credential creation call
(`create_customer_vault`) follows the JSON shape documented in
`managed-agents-tools.md` § Vaults, but the skill's Python examples don't
show a literal `vaults.credentials.create(...)` call. If the exact kwarg
names differ from what's below, that's a place to check current SDK docs
(see plan.md Discernment — this whole surface is beta and moves fast), not
a design problem with the approach.
"""

from __future__ import annotations

import anthropic

from .config import CustomerConfig, OAuthCredential, ProvisionedState
from .prompts import (
    EMAIL_MANAGEMENT_SYSTEM_PROMPT,
    GALILEO_SYSTEM_PROMPT,
    TERMIN_MANAGEMENT_SYSTEM_PROMPT,
)

MODEL_COORDINATOR = "claude-sonnet-5"
MODEL_SUBAGENT = "claude-haiku-4-5"  # cheap-worker pattern: read-heavy MCP work, cheaper model


def get_or_create_environment(client: anthropic.Anthropic, state: ProvisionedState) -> str:
    if state.environment_id:
        return state.environment_id
    env = client.beta.environments.create(
        name="bera-core",
        config={"type": "cloud", "networking": {"type": "unrestricted"}},
    )
    state.environment_id = env.id
    return env.id


def get_or_create_subagents(
    client: anthropic.Anthropic, config: CustomerConfig, state: ProvisionedState
) -> tuple[str, str]:
    """Create Email Management and Termin Management, if not already created.

    Returns (email_management_agent_id, termin_management_agent_id).
    """
    if not state.email_management_agent_id:
        email_agent = client.beta.agents.create(
            name="Email Management",
            description="Vitus — reads this business's mailbox, read-only.",
            model=MODEL_SUBAGENT,
            system=EMAIL_MANAGEMENT_SYSTEM_PROMPT,
            mcp_servers=[{"type": "url", "name": "mail", "url": config.mail_mcp_url}],
            tools=[{"type": "mcp_toolset", "mcp_server_name": "mail"}],
        )
        state.email_management_agent_id = email_agent.id

    if not state.termin_management_agent_id:
        termin_agent = client.beta.agents.create(
            name="Termin Management",
            description="Nepomuk — reads this business's calendar, read-only.",
            model=MODEL_SUBAGENT,
            system=TERMIN_MANAGEMENT_SYSTEM_PROMPT,
            mcp_servers=[{"type": "url", "name": "calendar", "url": config.calendar_mcp_url}],
            tools=[{"type": "mcp_toolset", "mcp_server_name": "calendar"}],
        )
        state.termin_management_agent_id = termin_agent.id

    return state.email_management_agent_id, state.termin_management_agent_id


def get_or_create_galileo(
    client: anthropic.Anthropic, state: ProvisionedState
) -> tuple[str, int]:
    """Create the Galileo coordinator, rostering the two subagents already created.

    This is the ONLY place Galileo's `multiagent.agents` roster is set on
    initial creation. After this, the only supported way to grow the roster
    is `roster.add_role()` — the orchestrator-mediated core-lock path from
    plan.md. Nothing else in this codebase calls agents.update() on Galileo.
    """
    if state.galileo_agent_id:
        return state.galileo_agent_id, state.galileo_agent_version or 1

    assert state.email_management_agent_id and state.termin_management_agent_id, (
        "create subagents before Galileo — get_or_create_subagents() first"
    )

    galileo = client.beta.agents.create(
        name="Galileo",
        description="Orchestrator — coordinates Email and Termin Management, "
        "produces the hourly urgent-check result and the morning digest.",
        model=MODEL_COORDINATOR,
        system=GALILEO_SYSTEM_PROMPT,
        multiagent={
            "type": "coordinator",
            "agents": [state.email_management_agent_id, state.termin_management_agent_id],
        },
    )
    state.galileo_agent_id = galileo.id
    state.galileo_agent_version = galileo.version
    return galileo.id, galileo.version


def _oauth_credential_body(cred: OAuthCredential, mcp_server_url: str) -> dict:
    return {
        "type": "mcp_oauth",
        "mcp_server_url": mcp_server_url,
        "access_token": cred.access_token,
        "refresh": {
            "refresh_token": cred.refresh_token,
            "client_id": cred.client_id,
            "token_endpoint": cred.token_endpoint,
            "token_endpoint_auth": {"type": "none"},
        },
    }


def get_or_create_vault(
    client: anthropic.Anthropic, config: CustomerConfig, state: ProvisionedState
) -> str:
    """One vault per customer (plan.md: per-customer credential isolation),
    holding both the mail and calendar MCP OAuth credentials."""
    if state.vault_id:
        return state.vault_id

    vault = client.beta.vaults.create(name=f"{config.customer_id}-vault")
    client.beta.vaults.credentials.create(
        vault_id=vault.id,
        display_name=f"{config.customer_id} mail",
        auth=_oauth_credential_body(config.mail_oauth, config.mail_mcp_url),
    )
    client.beta.vaults.credentials.create(
        vault_id=vault.id,
        display_name=f"{config.customer_id} calendar",
        auth=_oauth_credential_body(config.calendar_oauth, config.calendar_mcp_url),
    )
    state.vault_id = vault.id
    return vault.id


def get_or_create_deployments(
    client: anthropic.Anthropic,
    config: CustomerConfig,
    state: ProvisionedState,
    *,
    hourly_minute: int = 17,
) -> tuple[str, str]:
    """Hourly-check + morning-digest scheduled deployments.

    `hourly_minute` defaults off :00 — not required by the platform (jitter
    already spreads execution, see plan.md Discernment), but avoids this
    customer's runs clustering with everyone else's if BERA_TIMEZONE-naive
    defaults get copy-pasted across many customers.
    """
    assert state.galileo_agent_id and state.environment_id and state.vault_id

    if not state.hourly_deployment_id:
        hourly = client.beta.deployments.create(
            name=f"{config.customer_id} - hourly check",
            agent=state.galileo_agent_id,
            environment_id=state.environment_id,
            vault_ids=[state.vault_id],
            initial_events=[
                {
                    "type": "user.message",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "MODE: hourly. Check for anything urgent since "
                                f"the last check (lookback {config.email_lookback_hours}h "
                                "for mail; next few hours for calendar)."
                            ),
                        }
                    ],
                }
            ],
            schedule={
                "type": "cron",
                "expression": f"{hourly_minute} * * * *",
                "timezone": config.timezone,
            },
        )
        state.hourly_deployment_id = hourly.id

    if not state.digest_deployment_id:
        digest = client.beta.deployments.create(
            name=f"{config.customer_id} - morning digest",
            agent=state.galileo_agent_id,
            environment_id=state.environment_id,
            vault_ids=[state.vault_id],
            initial_events=[
                {
                    "type": "user.message",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "MODE: digest. business_name="
                                f"{config.business_name}. This digest covers "
                                f"the period since yesterday's {config.digest_time} "
                                "digest — compute that window yourself from the "
                                "current date and the digest time given."
                            ),
                        }
                    ],
                }
            ],
            schedule={
                "type": "cron",
                "expression": config.digest_cron(),
                "timezone": config.timezone,
            },
        )
        state.digest_deployment_id = digest.id

    return state.hourly_deployment_id, state.digest_deployment_id


def provision_customer(client: anthropic.Anthropic, config: CustomerConfig) -> ProvisionedState:
    """Idempotent end-to-end setup for one customer. Safe to re-run — each
    step reuses whatever ProvisionedState already has on disk."""
    state = ProvisionedState.load(config.state_file)

    get_or_create_environment(client, state)
    state.save(config.state_file)  # save after every step: partial progress survives a crash

    get_or_create_subagents(client, config, state)
    state.save(config.state_file)

    get_or_create_galileo(client, state)
    state.save(config.state_file)

    get_or_create_vault(client, config, state)
    state.save(config.state_file)

    get_or_create_deployments(client, config, state)
    state.save(config.state_file)

    return state
