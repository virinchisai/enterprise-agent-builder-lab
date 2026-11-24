# Microsoft integration: tenant setup and acceptance

This is a configuration guide, not an exported/import-tested Power Platform solution. You need an authorized Power Platform development environment, appropriate licensing, Entra app registration rights or administrator help, and a reachable HTTPS API. Never tunnel the demo API to the public internet. Deploy a dedicated synthetic-data instance in Entra mode behind TLS, restrict ingress and configure a managed secret store before making the endpoint reachable.

1. Register a single-tenant API application in Entra. Set the API to accept v2 access tokens (the app manifest setting is `api.requestedAccessTokenVersion`), expose delegated scope `Tickets.Access`, and define user app role `Ticket.Reviewer`. Assign the reviewer role only to designated reviewers. Review consent requirements with the tenant administrator.
2. Configure `AUTH_MODE=entra`, `ENTRA_TENANT_ID` (tenant GUID), `ENTRA_AUDIENCE` (expected v2 token audience, generally API client ID), and a strong unique `APPROVAL_SIGNING_KEY` from a secret manager. Set LAB_DB to durable storage. Do not use demo mode or its tokens on the public instance. Do not run multiple replicas against separate SQLite volumes.
3. Register a separate OAuth client for the connector. Grant delegated access to the API scope. Configure OAuth 2.0 for the custom connector with tenant-specific authorization and token URLs, client ID and a secret if the connector configuration requires it. Add the exact redirect URI displayed by Power Platform to the client app registration. Use delegated user credentials rather than a shared maker connection for user-specific records. This lab does not support app-only access tokens.
4. Generate Swagger 2.0 (replace all example values with tenant-approved values):

```sh
python scripts/connector.py --host support-lab.example.com --tenant YOUR_TENANT_GUID --scope api://YOUR_API_CLIENT_ID/Tickets.Access --output connector.json
```

5. In your development environment, create a custom connector from the generated OpenAPI file. Inspect General, Security and Definition; configure the OAuth provider/client/secret, scope, refresh URL if required, and redirect URI. Create a test connection with a test user. Test search, ticket creation, ticket read and approval status. Check the actual token audience/scope in the API without logging raw tokens. If OBO is supported by your environment and configured, validate actual user identity; otherwise require a user-owned connection. Do not assume every channel supports SSO.
6. In Copilot Studio create an IT support agent, enable appropriate Microsoft user authentication, add the synthetic policy file as a knowledge source, and add the connector tools. Paste instructions from `integrations/copilot-instructions.md`. For write actions use a deterministic topic/agent flow that explicitly asks for confirmation before invoking createTicket. Remove direct generative access to the write tool if you cannot enforce confirmation. The backend enforces identity and approval status, not proof of UI confirmation.
7. Configure the Power Automate recipes separately. Use environment variables and connection references; do not hardcode secrets. Keep reviewer decisions outside the ordinary agent. For a manual reviewer process, reviewer uses authorized API with their own delegated token. Do not use a flow owner's privileged identity to impersonate the requesting user.
8. Test the agent in the development channel, then use a solution to move components through test and production. Rebind environment values/connections, run smoke tests as two users and a reviewer, then publish only to the approved test audience. Record actual test results and rollback steps. No live import/publish was performed during generation of this repository.

Reference docs:
- https://learn.microsoft.com/en-us/microsoft-copilot-studio/copilot-ai-plugins
- https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-connections
- https://learn.microsoft.com/en-us/microsoft-copilot-studio/advanced-custom-connector-on-behalf-of
- https://learn.microsoft.com/en-us/microsoft-copilot-studio/configuration-fundamentals
- https://learn.microsoft.com/en-us/connectors/custom-connectors/
