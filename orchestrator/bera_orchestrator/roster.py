"""The orchestrator-mediated "add a Role -> Subagent pair" operation.

This is the core-lock mechanism from plan.md ("Core-lock enforcement,
rebuilt on a capability boundary"): the customer-facing extension surface
(whatever UI calls `add_role` below — a chat command or small form, per
Phase 2) never receives an Anthropic API key. Only this function, running
as B&R's own backend code, ever calls `agents.update()` on a customer's
Galileo instance — and it does exactly one thing: append one roster entry.
It has no parameter and no code path that could touch Galileo's `system`,
`model`, `tools`, or any existing roster entry.

Hard limit (documented, not a bug): a coordinator's roster caps at 20
entries, one level of delegation only. With the 2 built-in subagents, a
customer has room for up to 18 self-added roles — `add_role` raises before
attempting the API call if that cap would be exceeded, so the failure is
a clear local error rather than an opaque 400 from the platform.
"""

from __future__ import annotations

import anthropic

from .config import ProvisionedState

MAX_ROSTER_SIZE = 20
BUILT_IN_ROSTER_SIZE = 2  # Email Management + Termin Management


class RosterFullError(RuntimeError):
    pass


def add_role(
    client: anthropic.Anthropic,
    state: ProvisionedState,
    *,
    role_name: str,
    role_description: str,
    role_system_prompt: str,
    mcp_server: dict | None = None,
    model: str = "claude-haiku-4-5",
) -> str:
    """Create a new roster subagent and append it to Galileo's roster.

    `mcp_server`, if given, is `{"type": "url", "name": ..., "url": ...}` —
    the caller (the customer-facing extension surface) is responsible for
    collecting that from the customer and getting a vault credential added
    for it separately; this function only wires the agent + roster entry.

    Returns the new subagent's agent ID.
    """
    current_size = BUILT_IN_ROSTER_SIZE + len(state.custom_roster_agent_ids)
    if current_size >= MAX_ROSTER_SIZE:
        raise RosterFullError(
            f"Galileo's roster is at the platform limit ({MAX_ROSTER_SIZE} entries, "
            f"one level of delegation only). Remove an existing custom role before "
            f"adding '{role_name}'."
        )

    agent_kwargs: dict = {
        "name": role_name,
        "description": role_description,
        "model": model,
        "system": role_system_prompt,
    }
    if mcp_server is not None:
        agent_kwargs["mcp_servers"] = [mcp_server]
        agent_kwargs["tools"] = [{"type": "mcp_toolset", "mcp_server_name": mcp_server["name"]}]

    new_agent = client.beta.agents.create(**agent_kwargs)

    # The ONE agents.update() call this module ever makes on Galileo, and it
    # only ever appends — never touches system/model/tools/existing roster.
    galileo = client.beta.agents.retrieve(state.galileo_agent_id)
    current_roster = list(galileo.multiagent.agents) if galileo.multiagent else []
    client.beta.agents.update(
        state.galileo_agent_id,
        multiagent={"type": "coordinator", "agents": [*current_roster, new_agent.id]},
    )

    state.custom_roster_agent_ids.append(new_agent.id)
    return new_agent.id
