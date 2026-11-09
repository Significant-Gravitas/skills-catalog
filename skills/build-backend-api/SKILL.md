---
name: build-backend-api
description: Use when a service, endpoint, data model, or integration needs designing and building at the implementation level.
version: '1'
---

# Build a backend API

Inputs: the API contract or user story, data shape, auth and rate-limit needs, and the repo's existing service patterns. Output: endpoints with validation, auth, idempotency where writes occur, migrations if needed, and tests. Fallbacks: if the contract is undefined, draft it and get the owner's yes before building; match the repo's framework (TypeScript/Node, FastAPI/Python, Go) rather than importing a new one.

1. Name the domain data shape first: resources, fields, and invariants. Then design endpoints around it.
2. Mirror the existing service path — same module layout, error types, and response shapes as sibling endpoints.
3. Implement: validation at the boundary, auth on every route, idempotency keys and safe retries on writes, pagination on lists.
4. Data: model in Postgres or the repo's store; migrations are forward-only and reviewed like code. Never run one on real data without the owner's yes.
5. Add observability basics: structured logs with request IDs, and RED metrics (rate, errors, duration) hooks where the repo already has them.
6. Test: contract tests per endpoint plus failure cases — bad input, empty, large payload, permissions, concurrency.
7. Deliver the four-part contract with example requests and real test output.

<!-- Reuse: reuse reports found no local backend/API builder; framework choice follows the repo, per JD stack evidence (Go, Python, TypeScript). -->
