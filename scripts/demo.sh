#!/usr/bin/env bash
set -euo pipefail
base="${LAB_API:-http://127.0.0.1:8000}"
key="demo-$(python -c 'import uuid; print(uuid.uuid4().hex)')"
curl -fsS "$base/health"; echo
curl -fsS -H 'Authorization: Bearer demo-alice' "$base/knowledge?q=vpn"; echo
for _ in 1 2; do
curl -fsS -X POST "$base/tickets" -H 'Authorization: Bearer demo-alice' -H "Idempotency-Key: $key" -H 'Content-Type: application/json' -d '{"category":"vpn","summary":"Synthetic VPN problem"}'; echo
done
