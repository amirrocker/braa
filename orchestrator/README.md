# B&R Agentic Automation — Phase 1 orchestrator

Implements the Phase 1 slice of [`../Berisha_Rocker_Agentic_Automation_plan.md`](../Berisha_Rocker_Agentic_Automation_plan.md): one pilot customer (TechKomp Electrical), Galileo + Email Management + Termin Management on Claude Managed Agents, an hourly urgent-check deployment, a daily digest deployment, and Telegram delivery kept deliberately outside the agent loop.

**This is a scaffold, not a running deployment.** It is correct against the Managed Agents API shapes documented in the `claude-api` skill reference as of this writing, but nothing here has been run against live credentials — see "What you need before this can run" below and the plan's Phase 0/Discernment sections for what's still unverified.

## Layout

```
bera_orchestrator/
  config.py           per-customer config (loaded from .env) + on-disk provisioned-resource state
  prompts.py           Galileo / Email Management / Termin Management system prompts
  provisioning.py       one-time setup: environment, 3 agents, vault, 2 scheduled deployments
  roster.py             the core-lock "add a Role -> Subagent pair" operation
  telegram.py           Bot API sendMessage, called from the webhook handler — never from inside a session
  webhook_server.py      Flask endpoint: deployment_run.succeeded/.failed, vault_credential.refresh_failed
  cli.py                 bera-setup / bera-add-role / bera-webhook-server entry points
```

## Verification done so far (and its limits)

All modules were syntax-checked and import-checked, and `config.py`'s loader, `digest_cron()`, `ProvisionedState` save/load, and `roster.py`'s roster-cap guard were exercised with fake data — all pass. **What was not verified**: the `anthropic` package currently on PyPI (0.125.0, at the time this was checked) does not necessarily include the Managed Agents beta surface (`client.beta.agents`, `.environments`, `.vaults`, `.deployments`, `.webhooks`) used throughout `provisioning.py`, `roster.py`, and `webhook_server.py` — that beta launched recently and may need a specific/newer SDK version. Before running this for real: `pip show anthropic` for the installed version, confirm it exposes those methods, and upgrade if not — don't assume today's PyPI default has it.

## What you need before this can run

1. **An Anthropic API key** with Managed Agents (beta) access — `ANTHROPIC_API_KEY`.
2. **A webhook signing secret** — register this service's `/webhook` URL in Console → Manage → Webhooks (subscribed to `deployment_run.succeeded`, `deployment_run.failed`, `vault_credential.refresh_failed`), copy the `whsec_...` secret into `ANTHROPIC_WEBHOOK_SIGNING_KEY`. The webhook endpoint must be a publicly resolvable HTTPS URL — `localhost` won't work; use a tunnel (e.g. ngrok) for local testing.
3. **TechKomp's Gmail/Google Workspace MCP connector** — a hosted MCP server URL for Gmail and Google Calendar, plus Google OAuth credentials. **Unverified**: the plan's Phase 0 explicitly flags that a production-grade Gmail/Google Calendar MCP server hasn't been confirmed to exist. Don't fill in `BERA_MAIL_MCP_URL` / `BERA_CALENDAR_MCP_URL` with a guess.
4. **A Telegram bot** TechKomp creates themselves via BotFather (a few minutes) — bot token + chat ID into `BERA_TELEGRAM_BOT_TOKEN` / `BERA_TELEGRAM_CHAT_ID`.

Copy `.env.example` to `.env` and fill in all of the above before running anything.

## Running it

```bash
pip install -e .
cp .env.example .env   # then fill it in
bera-setup              # one-time: provisions environment/agents/vault/deployments, idempotent
bera-webhook-server      # run continuously (or behind a process manager) to receive deployment_run webhooks
```

To test a deployment before trusting its schedule (per the plan's Verification section), use `client.beta.deployments.run(deployment_id)` — a manual run creates a session immediately and works even while paused. No CLI wrapper for this yet; use the SDK directly or the Console.

To add a customer-requested Role → Subagent pair (Phase 1: run manually; Phase 2: a real customer-facing surface calls `roster.add_role` the same way):

```bash
bera-add-role --name "Invoice Reminder" --description "..." --prompt-file ./invoice_reminder_prompt.txt
```

## What's deliberately NOT here yet

- The BI Warehouse / Dashboard (Phase 2+, see the plan's "Dashboard & BI Warehouse" section) — this is automation-only.
- Session budgets (`budget.max_list_cost`) — add once Phase 1 usage is measured, per the plan.
- Multi-customer / workspace-per-customer isolation — this scaffold assumes one customer's credentials in one `.env`; see the plan's "Multi-tenant isolation model" before generalizing past the pilot.
- Any write-capable connector actions (creating appointments, sending replies) — core connectors here are read-only by design (Mail.Read/Calendars.Read equivalents), matching the plan's least-privilege default.
