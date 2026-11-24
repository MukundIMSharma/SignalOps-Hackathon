# Progress

**Last updated:** 2026-11-24
**Current focus:** Milestone 2 — Synapse/MCP proof (blocked: Synapse CLI install command needed)
**Last completed:** Milestone 1 — both APIs built, seeded, 21/21 tests passing, run live on 8001/8002
**Next up:** install Synapse, generate both MCP servers; GitHub remote; confirm LLM API key

## Milestone 0 — Setup / scope lock
- [ ] Create GitHub repo(s) — local git done (branch main); remote pending
- [x] Create project directories
- [x] Agree on API schemas (CONTRACTS.md, business APIs locked)
- [ ] Create task board / issue list — using PROGRESS.md for now
- [x] Set up environment and `.env.example` (`.env` itself not created)
- [ ] Confirm model/API access
- [ ] Confirm Synapse CLI works

## Milestone 1 — Two APIs + seed data
- [x] Orders schema/routes
- [x] Inventory schema/routes
- [x] Deterministic seed data
- [x] OpenAPI docs
- [x] Unit/API tests
- [x] Health endpoints

## Milestone 2 — Synapse/MCP proof
- [ ] Generate Orders MCP
- [ ] Generate Inventory MCP
- [ ] Select endpoints
- [ ] Connect both to test client
- [ ] Test representative tools
- [ ] Save configuration and instructions

## Milestone 3 — Agent investigation
- [ ] Orchestrator and investigation state
- [ ] Tool calling
- [ ] Cross-system correlation
- [ ] Evidence collection
- [ ] Root cause
- [ ] Impact calculations
- [ ] Customer prioritization
- [ ] Report generation
- [ ] Failure/partial result handling

## Milestone 4 — Frontend MVP
- [ ] App shell/navigation
- [ ] Dashboard
- [ ] Investigation screen
- [ ] Live activity
- [ ] Evidence/findings
- [ ] Impact visualizations
- [ ] Recommendations
- [ ] Connect backend

## Milestone 5 — Approval and audit
- [ ] Action preview
- [ ] Approve/reject
- [ ] Simulated action execution
- [ ] Idempotency
- [ ] Audit trail

## Milestone 6 — Synapse live discovery
- [ ] Add `/inventory/incidents`
- [ ] Restart API
- [ ] `synapse build --discover`
- [ ] Verify new tool
- [ ] Agent calls new tool
- [ ] UI shows updated tools

## Milestone 7 — Polish, testing, submission
- [ ] Run full test suite
- [ ] Run 5 demo rehearsals
- [ ] Fix P0 bugs
- [ ] Prepare README
- [ ] Prepare architecture image
- [ ] Record backup video
- [ ] Prepare pitch
- [ ] Check repository and secrets
