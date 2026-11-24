# Progress

**Last updated:** 2026-11-24
**Current focus:** Milestone 4 — backend HTTP/SSE API, then frontend MVP
**Last completed:** Milestone 3 — live terminal investigation over both MCP servers; 21/21 backend tests
**Next up:** FastAPI backend (start investigation, SSE events, report, systems/tools); define its contract; then React app

## Milestone 0 — Setup / scope lock
- [x] Create GitHub repo(s) — origin pushed
- [x] Create project directories
- [x] Agree on API schemas (CONTRACTS.md, business APIs locked)
- [ ] Create task board / issue list — using PROGRESS.md for now
- [x] Set up environment and `.env.example` (`.env` itself not created)
- [x] Confirm model/API access — gemini-3.8-flash responds (slow, see KNOWN_ISSUES)
- [x] Confirm Synapse CLI works — v0.1.9, both builds succeeded

## Milestone 1 — Two APIs + seed data
- [x] Orders schema/routes
- [x] Inventory schema/routes
- [x] Deterministic seed data
- [x] OpenAPI docs
- [x] Unit/API tests
- [x] Health endpoints

## Milestone 2 — Synapse/MCP proof
- [x] Generate Orders MCP
- [x] Generate Inventory MCP
- [x] Select endpoints
- [x] Connect both to test client
- [x] Test representative tools
- [x] Save configuration and instructions

## Milestone 3 — Agent investigation
- [x] Orchestrator and investigation state
- [x] Tool calling
- [x] Cross-system correlation
- [x] Evidence collection
- [x] Root cause
- [x] Impact calculations
- [x] Customer prioritization
- [x] Report generation
- [x] Failure/partial result handling

## Milestone 4 — Frontend MVP
- [x] App shell/navigation
- [x] Dashboard
- [x] Investigation screen
- [x] Live activity
- [x] Evidence/findings
- [x] Impact visualizations
- [x] Recommendations
- [x] Connect backend

## Milestone 5 — Approval and audit
- [x] Action preview
- [x] Approve/reject
- [x] Simulated action execution
- [x] Idempotency
- [x] Audit trail

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
