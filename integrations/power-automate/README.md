# Power Automate build recipes

Manual configuration recipes, not deployable flow exports. Actual connector and environment IDs are tenant-specific.

## Flow A: create support ticket
1. Create an agent flow in the development environment with the agent trigger and response action (When an agent calls the flow / Respond to the agent, or equivalent in the current authoring experience).
2. Define text inputs category, summary, request_id. Collect and confirm category and summary in a deterministic agent topic. Generate a stable request ID for each new confirmed operation; preserve it for retries. `guid()` may initialize a new request, but must not be regenerated after an ambiguous failure.
3. Validate category against vpn/access/hardware and summary length against 5–500 characters. Invoke the custom connector createTicket operation, mapping request_id to Idempotency-Key. Verify the connection represents the requesting user. If not, do not deploy the user-specific tool.
4. Use Try and Catch scopes with Configure run after for failed and timed-out actions. Return ticket_id, status, approval_id (empty if null), error. 409 means conflict; 401/403 require sign-in or permission correction. Never blindly retry with a new key.
5. Return promptly; access requests return pending_approval, not a granted access request. Do not wait synchronously for a human reviewer.

## Flow B: status lookup
Agent trigger receives ticket_id; invoke getTicket using the user's delegated connection; return id, status and summary when permitted. Treat 404 as unavailable, without exposing another user's data. Never accept a user identity argument from the model as an authentication override.

## Flow C: human review
Separate reviewer-owned process reads the approval record and shows its exact category, summary and expiry. A reviewer calls the protected decision API using their own delegated token and Ticket.Reviewer role. If automating this process, create a separate reviewer connector and verify actual human identity reaches the backend; flow-owner credentials are not a substitute. The ordinary agent connector excludes the decision operation. Keep approvals outside Flow A; notify requester only via an authorized notification channel, or poll Flow B. Notifications are not implemented in the local lab.

## Acceptance checks
VPN success; pending access request; unauthorized approval; reviewer approve/reject; expired/repeated approval; idempotent retry; changed input with same key; cross-user denial; unavailable API; missing scope; expired token. Capture redacted run history. Validate every case in a licensed test tenant before asserting production readiness.
