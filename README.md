# Enterprise Agent Builder Lab

A portfolio-grade integration lab for a synthetic employee IT support agent. FastAPI, SQLite, local knowledge retrieval, bounded OpenAI and Claude tool calling, approval gating, Microsoft Entra delegated authentication, and Power Platform integration assets.

## Status and boundaries

- Implemented and locally tested: API, demo identity, ownership, idempotency, approval decisions, keyword retrieval, audit counts, mocked provider protocol round trips, connector generation.
- Integration-ready but not live-tested: Entra token validation, custom connector import, Copilot Studio agent, Power Automate configuration, live OpenAI/Claude models. No claim of ChatGPT Enterprise or Claude Enterprise workspace administration.
- Docker and CI definitions included; container build and hosted CI not verified here.
- Synthetic training data only. Demo bearer tokens are public and must never be exposed externally. This lab does not grant actual system access or create real enterprise tickets.

## Quick start (macOS/Linux)

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs. Authorize using `demo-alice` (Swagger adds Bearer). In a second terminal activate the same virtual environment:

```sh
python agent.py 'How do I troubleshoot VPN?'
python agent.py --create vpn --summary 'VPN connection fails' --idempotency-key demo-request-001
python agent.py --create access --summary 'Request access to finance workspace' --idempotency-key demo-request-002
```

Type YES to confirm a create. For access, copy the returned approval ID. In Swagger, authorize as `demo-reviewer`, GET `/approvals/{approval_id}` to review the request, and POST `/approvals/{approval_id}/decision` with `{ "decision": "approve" }`. Reauthorize as `demo-alice` and GET the ticket. The state changes from pending_approval to open. Replaying the decision returns 409. A normal user cannot decide an approval. The approval does not grant real access.

For Docker: `docker compose up --build` (binds host loopback; stop with `docker compose down`). The named volume preserves synthetic tickets.

## Architecture

```text
Local CLI / optional Copilot Studio agent
    -> per-user delegated connector / read-only provider tools
    -> FastAPI identity + ownership checks
    -> knowledge lookup OR validated ticket creation
    -> access request pending reviewer decision
    -> SQLite transactional state + audit events
```

Cloud model calls are optional, transmit selected content to the provider, and require explicit `--allow-provider-egress`. Only use fictional data. Set `OPENAI_API_KEY` and `OPENAI_MODEL` or `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` securely in your shell (choose a model available to your account). Do not commit secrets. Example: `python agent.py --provider openai --allow-provider-egress 'What is the VPN policy?'`. For Claude use `--provider claude`. Model outputs are not trusted authorization decisions. Provider keys and API bearer tokens are separate; only the backend receives its bearer token. Model tools are read-only and bounded; no automatic model-driven write.

## Microsoft integration

Follow [Microsoft setup](docs/microsoft.md), [workflow recipes](integrations/power-automate/README.md), and [agent instructions](integrations/copilot-instructions.md). Generate the connector from `scripts/connector.py`. Do not import the example.invalid template unchanged. The reviewer decision is deliberately excluded from the agent connector.

## Operations and handover

See [operations](docs/operations.md) for deployment, testing, recovery, threat model and acceptance checklist. GitHub Actions runs tests, validates connector generation and builds the image when configured on GitHub.
