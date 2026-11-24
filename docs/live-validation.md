# Live validation and deployment checklist

Local API/demo mode must remain loopback-only; cloud deployment requires Entra mode. Never use employer credentials or real customer data for this personal lab. The following are procedures, not completed cloud integrations.

## Docker runtime
Stop any existing listener on port 8000. Run `docker compose up --build -d`, `docker compose ps`, `python scripts/evaluate.py`, then `docker compose down`. CI also runs the HTTP acceptance script against a disposable container. The data volume remains unless explicitly deleted.

## OpenAI and Claude
Use personal provider accounts with authorized API billing and model access. Set `OPENAI_API_KEY` / `OPENAI_MODEL` or `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` as server environment variables, not source files. Set `ENABLE_PROVIDER_CHAT=true` for browser chat in loopback demo mode. Ask a synthetic VPN question with consent enabled and inspect the actual tool evidence. Test both providers separately, record model ID and result, and test a missing-evidence question. Never paste keys into chat, commit them, or enable provider chat on a publicly reachable demo instance. Direct provider APIs are not enterprise workspace deployments.

## Entra and HTTPS
Follow `docs/microsoft.md` using a dedicated authorized tenant. Register API and connector client separately; record tenant and API client IDs, not secret values. Configure v2 delegated scope and reviewer role. Deploy the Docker image as one instance behind managed TLS with durable storage mounted at /data, nonroot write permissions, and environment secrets managed by the host. Set AUTH_MODE=entra, ENTRA_TENANT_ID, ENTRA_AUDIENCE, APPROVAL_SIGNING_KEY and LAB_DB=/data/lab.db. Do not use the demo Compose file for public hosting. Leave provider chat disabled. Do not enable public ingress until auth settings and HTTPS are verified. Verify anonymous requests fail, demo tokens fail, invalid audiences fail, and actual delegated tokens succeed. Restrict ingress where compatible with the connector and configure request limits, operational monitoring and backups. A public URL alone is not a successful secure deployment.

## Power Platform
Generate the custom connector using the real HTTPS hostname and tenant scope. Import into an authorized development environment and configure OAuth, exact redirect URI and user-owned connections. Test two ordinary users and a separate reviewer. Configure the flow recipes in `integrations/power-automate/README.md`, then create the agent and add its knowledge and actions. Keep approval decisions outside the ordinary agent. Verify no duplicate tickets on retry and no cross-user reads; record actual connector and flow run identifiers and screenshots with secrets removed. Publish only to a test audience. Export a solution after the environment is configured; the repository does not contain a validated export.

## Evidence
Record commit, environment, timestamp, model IDs, HTTP outcomes, test accounts (pseudonyms), connector and flow results, and known limitations. Do not label mocked tests or a local API demo as live Microsoft deployment.
