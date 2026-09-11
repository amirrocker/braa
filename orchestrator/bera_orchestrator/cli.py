"""Command-line entry points (see pyproject.toml [project.scripts]).

These are the only places a human runs this code directly — everything else
is either one-time setup or the webhook server. Matches plan.md Phase 1's
"Acceptance" bullet: onboarding must work without the customer ever touching
an Anthropic API key. These commands are run by B&R's own staff (or an
onboarding script acting on the customer's behalf), never by the customer.
"""

from __future__ import annotations

import sys

import anthropic

from .config import ProvisionedState, load_customer_config
from .provisioning import provision_customer
from .roster import add_role as _add_role


def setup_customer() -> None:
    """`bera-setup` — idempotent Phase 1 provisioning for one customer.

    Usage: BERA_* env vars set (or a .env file in cwd), then `bera-setup`.
    """
    config = load_customer_config()
    client = anthropic.Anthropic()

    print(f"Provisioning Managed Agents resources for {config.business_name} "
          f"({config.customer_id})...")
    state = provision_customer(client, config)

    print("Done. Provisioned resource IDs (saved to "
          f"{config.state_file}):")
    print(f"  environment:            {state.environment_id}")
    print(f"  galileo agent:          {state.galileo_agent_id} (v{state.galileo_agent_version})")
    print(f"  email management agent: {state.email_management_agent_id}")
    print(f"  termin management agent:{state.termin_management_agent_id}")
    print(f"  vault:                  {state.vault_id}")
    print(f"  hourly deployment:      {state.hourly_deployment_id}")
    print(f"  digest deployment:      {state.digest_deployment_id}")
    print()
    print("Next: register this service's /webhook URL in Console -> Manage -> "
          "Webhooks (subscribe to deployment_run.succeeded, "
          "deployment_run.failed, vault_credential.refresh_failed), then run "
          "a manual deployment fire to test before trusting the schedule — "
          "see plan.md Verification.")


def add_role() -> None:
    """`bera-add-role --name ... --description ... --prompt-file ...`

    Minimal CLI wrapper around roster.add_role for manual/Phase-1 use.
    Phase 2 replaces this with the real customer-facing extension surface —
    a chat command or small form — that calls the same function.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Add a Role -> Subagent pair to Galileo's roster")
    parser.add_argument("--name", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--prompt-file", required=True, help="Path to the new subagent's system prompt")
    parser.add_argument("--model", default="claude-haiku-4-5")
    args = parser.parse_args()

    config = load_customer_config()
    client = anthropic.Anthropic()
    state = ProvisionedState.load(config.state_file)

    if not state.galileo_agent_id:
        print("Galileo hasn't been provisioned yet for this customer — run `bera-setup` first.", file=sys.stderr)
        sys.exit(1)

    with open(args.prompt_file) as f:
        system_prompt = f.read()

    new_agent_id = _add_role(
        client,
        state,
        role_name=args.name,
        role_description=args.description,
        role_system_prompt=system_prompt,
        model=args.model,
    )
    state.save(config.state_file)
    print(f"Added role '{args.name}' as agent {new_agent_id}. Galileo's roster now includes it.")


def run_webhook_server() -> None:
    """`bera-webhook-server` — runs the Flask app from webhook_server.py."""
    from .webhook_server import create_app

    config = load_customer_config()
    app = create_app(config)
    import os

    port = int(os.environ.get("BERA_WEBHOOK_PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
