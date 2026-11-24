# SIGNALOPS — Hackathon Project Master Plan
## 2nd Brain Labs × Geek Room Vibe-a-thon | Track 3: A Copilot Across Two Systems

**Plan status:** Working master plan  
**Project:** SignalOps — AI Business Incident Investigator  
**Primary goal:** Build a reliable, polished, end-to-end demo that makes Synapse central to the product.  
**Track:** Track 3 — use Synapse Auto to turn two separate codebases into MCP servers and build an agent that correctly combines both systems.  
**Planning note:** The participant guide specifies two MCP servers, cross-system questions, and a live endpoint addition followed by `synapse build --discover`. This plan is based on that guide and strategic design decisions; it is not an official judging rubric or a verified list of prior winners.

---

# 1. Product Summary

## One-line pitch
**SignalOps connects disconnected business systems, investigates operational incidents, proves likely root causes with source evidence, quantifies impact, and recommends safe actions.**

## Problem
Operational information is spread across separate systems:
- Orders and customer records
- Shipments and delivery status
- Inventory and warehouse stock
- Inventory synchronization status
- Support tickets / customer complaints (simulated as a supporting dataset or optional third system)

People manually cross-check dashboards and APIs to understand an incident, identify affected customers, quantify the impact, and decide what to do. This process is slow and prone to missed connections.

## Solution
SignalOps is an AI operations investigator. It uses Synapse-generated MCP servers to access two existing business systems, correlate their data, generate evidence-backed findings, calculate impact using deterministic code, and propose a resolution plan with human approval before high-impact actions.

## Target demo scenario
A simulated business, **NovaCommerce**, experiences an inventory synchronization failure at Warehouse W1.

Seed data includes:
- 28 delayed orders linked to a product affected by the inventory incident
- 12 orders exceeding their expected dispatch date (can overlap with the 28 affected orders; make exact counts explicit in seed data and report)
- 9 customers with support tickets about delays
- 4 high-priority/VIP customers
- A second warehouse (W2) with stock sufficient to recover a subset of affected orders
- A sync failure with timestamp, affected SKU, and error details

The scenario and counts must be deterministic and internally consistent. Avoid presenting overlapping counts as if they were additive.

## User prompt for the demo
“Investigate all delayed orders. Identify the root cause, which customers are affected, the business impact, and what we should do next.”

## Product principles
1. Synapse must be essential and visible—not a checkbox.
2. Separate existing-system codebases; do not merge them into a single artificial service.
3. Every important finding should cite evidence from the source system.
4. Deterministic calculations should be performed in code, not improvised by the LLM.
5. Distinguish confirmed facts, hypotheses, and unknowns.
6. Partial failures should result in partial, clearly labeled reports—not fabricated answers.
7. Human approval is required before consequential changes.
8. Prioritize a complete reliable flow over feature count.
9. The demo scenario must be repeatable.
10. Build a professional product interface, not a generic chat UI.

---

# 2. Hackathon Track Alignment

## Track 3 — Copilot Across Two Systems
Required demonstration:
- Two separate codebases / business systems
- Synapse Auto generates MCP server(s) for both
- Agent asks questions requiring both systems
- Correct cross-system answers
- Add a new endpoint during demo
- Rebuild/discover using `synapse build --discover`
- Demonstrate agent using the newly discovered capability

## Submission artifacts
- Orders system repository
- Inventory system repository
- Both generated MCP server configurations / setup
- Agent and frontend repository (or clearly organized monorepo)
- README with setup and architecture
- Demo with at least two cross-system questions
- Live endpoint-discovery demonstration
- Short write-up explaining problem, solution, and why Synapse fits
- Demo recording as backup

---

# 3. Project Scope

## Must-have (P0)
- Two independent APIs (Orders and Inventory)
- Deterministic seed data and incident
- Synapse Auto MCP for both systems
- MCP clients / integration that can call both servers
- Cross-system investigation
- Evidence-linked findings
- Deterministic impact calculations
- Root-cause report
- Resolution recommendations
- Approval step for simulated high-impact action
- Audit log
- Basic polished dashboard
- End-to-end demo scenario
- Live discovery of newly added endpoint

## Should-have (P1)
- Streaming/live activity feed
- Customer priority ranking
- Incident timeline
- Revenue/value-at-risk chart
- Evidence cards with source endpoint and entity IDs
- Systems/MCP page showing server health and tool list
- Incident report export (PDF or printable report)
- Retry/timeout handling
- Partial-result status

## Stretch (P2)
- Incident replay
- Evidence relationship graph
- Before/after impact
- More than one incident type
- Optional support-ticket API/system
- Downloadable PDF
- Deployment and public demo link
- Search/filter incident history

## Explicitly out of scope unless time remains
- Real ERP integrations
- Real customer communications
- Real money or inventory movement
- Complex authentication / enterprise roles
- Kubernetes, Kafka, microservices proliferation
- Multi-agent framework purely for novelty
- Voice assistant
- Vector database unless a clearly demonstrated requirement arises
- Excessive dashboard pages or animations

---

# 4. Product Workflow

## Normal investigation flow
1. User selects an incident or enters a natural-language investigation request.
2. Backend creates an investigation record and status.
3. Agent retrieves delayed orders from Orders MCP.
4. Agent retrieves relevant order/customer/shipment data from Orders MCP.
5. Agent queries stock availability and warehouse data from Inventory MCP.
6. Agent checks inventory synchronization status.
7. Agent correlates product IDs, order IDs, warehouse IDs, and time ranges.
8. Agent creates root-cause hypotheses.
9. Agent validates hypotheses against available source evidence.
10. Backend computes affected order/customer counts and financial totals.
11. Agent prioritizes customers using explicit business rules.
12. Agent creates a recommended action plan.
13. UI presents findings and evidence.
14. User approves or rejects any consequential action.
15. Approved demo action executes against a simulated endpoint.
16. Audit record captures who/what/when, request, approval, result, and status.

## Investigation status lifecycle
- queued
- investigating
- partial
- awaiting_approval
- completed
- failed
- cancelled

## Root cause classifications
- confirmed: directly supported by reliable source evidence
- likely: supported by multiple pieces of evidence, but not directly proven
- hypothesis: plausible but unverified
- unknown: insufficient information

---

# 5. Architecture

## High-level
Frontend (React + TypeScript)
→ SignalOps backend/orchestrator (FastAPI)
→ Orders MCP server (Synapse Auto)
→ Orders API (FastAPI + SQLite)

and

SignalOps backend/orchestrator (FastAPI)
→ Inventory MCP server (Synapse Auto)
→ Inventory API (FastAPI + SQLite)

## Recommended stack
- Frontend: React + TypeScript + Vite
- UI: Tailwind CSS + shadcn/ui
- Charts: Recharts
- Backend APIs: Python + FastAPI
- Data: SQLite + SQLAlchemy
- Validation: Pydantic
- Agent orchestration: Python, controlled workflow (avoid unnecessary agent framework)
- MCP: Synapse-generated MCP servers
- LLM: available model provider/API
- Streaming: SSE initially (WebSocket only if needed)
- Tests: pytest + API integration tests
- Deployment: frontend on Vercel; backend on Render/Railway or stable local demo if deployment time is limited
- Version control: GitHub

## Architecture constraints
- Keep Orders and Inventory APIs independently runnable.
- Use separate databases or clearly separate data stores.
- The agent accesses business APIs through generated MCP tools for the core demonstration.
- Do not silently bypass MCP using direct HTTP calls for the main workflow; direct API calls may be used for health checks or test setup, and must be clearly separated.
- The agent orchestrator is responsible for workflow, tool error handling, evidence collection, calculations, and action approval.

---

# 6. Repository Layout

Recommended organization (monorepo for hackathon speed, with independently isolated codebases):

```text
signalops/
├── README.md
├── docs/
│   ├── architecture.md
│   ├── demo-script.md
│   ├── judging-checklist.md
│   └── synapse-setup.md
├── nova-orders/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── seed.py
│   │   └── routes/
│   │       ├── orders.py
│   │       ├── customers.py
│   │       ├── shipments.py
│   │       └── analytics.py
│   ├── tests/
│   ├── requirements.txt
│   └── README.md
├── nova-inventory/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── seed.py
│   │   └── routes/
│   │       ├── products.py
│   │       ├── stock.py
│   │       ├── warehouses.py
│   │       ├── sync.py
│   │       └── analytics.py
│   ├── tests/
│   ├── requirements.txt
│   └── README.md
├── signalops-backend/
│   ├── main.py
│   ├── agent/
│   │   ├── orchestrator.py
│   │   ├── investigation.py
│   │   ├── correlation.py
│   │   ├── impact.py
│   │   ├── prioritization.py
│   │   ├── planner.py
│   │   ├── risk.py
│   │   └── schemas.py
│   ├── mcp/
│   │   ├── orders_client.py
│   │   └── inventory_client.py
│   ├── services/
│   │   ├── incidents.py
│   │   ├── approvals.py
│   │   └── audit.py
│   ├── prompts/
│   │   ├── investigator.md
│   │   └── report_writer.md
│   ├── tests/
│   └── requirements.txt
└── signalops-frontend/
    ├── src/
    │   ├── pages/
    │   ├── components/
    │   ├── features/
    │   │   ├── dashboard/
    │   │   ├── investigation/
    │   │   ├── reports/
    │   │   ├── approvals/
    │   │   └── systems/
    │   ├── api/
    │   ├── hooks/
    │   └── types/
    └── package.json
```

If using separate Git repositories is necessary for Synapse scanning or judging clarity, keep the three systems in separate repositories and add a top-level README or demo repository. Avoid restructuring late.

---

# 7. Orders System — Data and API Plan

## Data entities
### Order
- order_id
- customer_id
- product_id / SKU
- quantity
- order_date
- expected_dispatch_date
- status
- priority
- unit_price
- total_amount
- warehouse_id (planned/assigned)
- shipment_id (nullable)

### Customer
- customer_id
- name (fictional)
- tier (standard/VIP)
- contact preference (fictional demo data)
- risk/priority flag
- lifetime value (optional, only if useful to the scenario)

### Shipment
- shipment_id
- order_id
- carrier
- status
- created_at
- expected_delivery
- actual_delivery (nullable)
- tracking status

## API endpoints
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/orders` | List/filter/paginate |
| GET | `/orders/{order_id}` | Order detail |
| GET | `/orders/delayed` | Delayed orders |
| GET | `/orders/at-risk` | Orders likely to breach SLA |
| GET | `/customers/{customer_id}` | Customer details |
| GET | `/customers/{customer_id}/orders` | Customer history |
| GET | `/shipments` | Shipment list/filter |
| GET | `/analytics/order-health` | Summary statistics |

## API requirements
- Typed schemas
- Pagination where sensible
- Filter by status, priority, SKU, date, warehouse
- Consistent errors
- OpenAPI documentation
- Deterministic seed data
- Unit and API tests

---

# 8. Inventory System — Data and API Plan

## Data entities
### Product
- product_id / SKU
- name
- category
- reorder threshold
- unit price (optional; order system remains source for order values)

### Warehouse
- warehouse_id
- name
- location (fictional)
- status

### Stock
- product_id
- warehouse_id
- available_quantity
- reserved_quantity
- last_updated

### SyncStatus
- sync_id
- source
- status
- last_attempt
- last_success
- error_code
- error_message
- affected_products
- severity

## API endpoints
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/products` | Product catalog |
| GET | `/products/{product_id}` | Product details |
| GET | `/stock` | Stock query/filter |
| GET | `/stock/low` | Low stock |
| GET | `/stock/{product_id}` | Stock across warehouses |
| GET | `/warehouses` | Warehouse status |
| GET | `/sync/status` | Sync status |
| GET | `/analytics/stock-health` | Stock metrics |

## Reserved endpoint for live demo
Do not add initially:
`GET /inventory/incidents`

At demo time:
1. Add endpoint and response schema/handler.
2. Restart inventory API.
3. Run `synapse build --discover`.
4. Verify generated MCP tool.
5. Use it in an investigation.
6. Show that agent capability has expanded.

## Live endpoint response shape (illustrative)
```json
{
  "incident_id": "INV-2026-042",
  "severity": "critical",
  "product_id": "SKU-104",
  "warehouse_id": "W1",
  "incident_type": "inventory_sync_failure",
  "occurred_at": "2026-11-23T09:42:00",
  "description": "Inventory synchronization failed; availability may be stale."
}
```
Use demo-local timestamps and keep all seed data consistent.

---

# 9. Synapse Plan

## Before builds
- Confirm Node.js 20+
- Install Synapse CLI according to participant guide
- Create/verify Synapse credentials if hosted build is chosen
- Decide hosted vs local build based on privacy, quota, model availability, and code scanning requirements
- Read the current CLI help/docs and confirm flags for installed version
- Ensure APIs are running and OpenAPI routes are accessible
- Do not expose secrets in repo or prompt

## Orders MCP
Use Auto mode. Select only useful endpoints. Proposed tools:
- get_delayed_orders
- get_order_details
- get_customer_details
- get_customer_orders
- get_shipment_status
- get_order_health

## Inventory MCP
Use Auto mode. Proposed tools:
- get_product_stock
- get_low_stock_products
- get_warehouse_inventory
- get_warehouse_status
- get_inventory_sync_status
- get_stock_health

## Tool design guidelines
- Expose the minimum useful endpoint set.
- Prefer clear names and descriptions.
- Keep read-only tools for the investigation.
- Isolate write/action tools.
- Test every generated tool with representative parameters.
- Confirm tool schemas and error behavior.
- Keep generated configuration and instructions in the repo, but never commit keys.
- Confirm Synapse-generated MCP is the route used in the demo.

## Live discovery acceptance
- New endpoint appears in code and OpenAPI.
- Synapse discovery is run against the changed system.
- New tool is available in agent tool inventory.
- Agent calls it in a follow-up investigation.
- UI shows new capability or tool list update.
- Have terminal output/screenshots/video backup.

---

# 10. Agent Design

## Recommended approach
Use a controlled workflow, not unrestricted autonomous loops.

### Orchestrator stages
1. Parse request / select investigation type.
2. Plan required queries.
3. Retrieve data from Orders MCP.
4. Retrieve data from Inventory MCP.
5. Validate tool outputs and required fields.
6. Correlate IDs and evidence.
7. Generate root cause hypotheses.
8. Verify hypotheses with additional tools when possible.
9. Calculate impact deterministically.
10. Rank affected customers deterministically.
11. Ask LLM to explain findings using supplied evidence only.
12. Generate resolution plan.
13. Create approval request for action(s).
14. Execute only approved simulated action.
15. Write audit record.
16. Return structured report and UI events.

## Use deterministic code for
- Counts
- Totals and revenue-at-risk
- Customer/order matching
- SLA breach calculation
- Stock availability
- Transfer quantity
- Customer ranking rules
- Action validation
- Idempotency
- Approval state

## Use LLM for
- User intent interpretation
- Query-plan suggestions (bounded by allowed tools)
- Root-cause hypothesis explanation
- Evidence synthesis
- Report narrative
- Natural-language recommendations
- Follow-up question interpretation

## Evidence schema
```json
{
  "evidence_id": "E-001",
  "claim": "SKU-104 has insufficient available stock in W1",
  "status": "confirmed",
  "source_system": "inventory",
  "source_tool": "get_product_stock",
  "source_endpoint": "/stock/SKU-104",
  "entity_ids": ["SKU-104", "W1"],
  "observed_at": "2026-11-23T09:42:00",
  "data": {
    "available_quantity": 0
  }
}
```

## Finding schema
- finding_id
- title
- summary
- severity
- status (confirmed / likely / hypothesis / unknown)
- evidence_ids
- confidence explanation (avoid uncalibrated pseudo-precision)
- impact metrics

## Reliability rules
- Source data is authoritative over model assumptions.
- If data is missing, state that.
- If sources disagree, show disagreement.
- Never fabricate tool results.
- Never claim a root cause is confirmed unless evidence supports it.
- Timeouts and errors should be captured in the investigation.
- Return partial reports when appropriate.
- Retry only safe read-only calls and limit retry count.
- Prevent tool-call loops.
- Keep an execution trace for judges.

---

# 11. Impact and Customer Prioritization

## Deterministic metrics
- Delayed order count
- Affected customer count
- Order value affected
- VIP/high-priority customer count
- Complaints count among affected customers
- Stock shortage quantity
- Recoverable order count from alternative warehouse stock
- Orders still unrecoverable after recommended transfer

Make metric definitions visible in the report. If metrics overlap, do not add them together.

## Prioritization rules (prototype)
A transparent score can use:
- VIP/tier
- SLA breach severity
- Complaint present
- Order value (optional; avoid unfairly deprioritizing low-value customers without explicit business policy)
- Days delayed

Document score weights and show reason tags. Prefer simple rules and avoid presenting the score as an objective truth.

---

# 12. Resolution Planning and Safety

## Suggested actions
- Draft internal incident record
- Prioritize customer tickets
- Recommend inventory transfer from W2 to W1
- Draft customer update
- Recommend escalation to inventory operations
- Monitor remaining delayed orders

## Approval policy
No consequential action runs without explicit user approval.

## Approval payload
- Action ID
- Action type
- Description
- Inputs and quantities
- Affected entities
- Risk level
- Supporting evidence
- Expected outcome
- Approval status
- Approver identifier (demo)
- Timestamp
- Execution result

## Demo-safe actions
Use simulated actions only:
- Simulated inventory transfer
- Simulated ticket priority change
- Draft-only customer communication (never send externally)
- Simulated internal incident creation

## Safeguards
- Reject action if requested quantity exceeds available stock.
- Validate order/product/warehouse IDs.
- Use idempotency key to prevent duplicate execution.
- Record approval and execution.
- Rejection leaves systems unchanged.
- Show preview of changes.
- Action status must not be falsely marked successful if backend execution fails.

---

# 13. Frontend Product Design

## Design direction
- Dark graphite/neutral background
- Slate surfaces and clear hierarchy
- Emerald for healthy
- Amber for warning
- Red for critical
- Restrained blue/indigo for agent activity
- Professional typography
- Avoid excessive gradients, noisy animation, and generic chatbot layout
- Responsive layout with desktop demo as primary target

## Navigation
1. Overview
2. Investigations
3. Incident reports
4. Approvals
5. Systems / MCP

## Overview page
Metric cards:
- Delayed orders
- Affected customers
- Open complaints
- Order value affected

Sections:
- Active incidents
- Recent investigations
- Inventory alerts
- Order-health chart
- System status

## Investigation workspace
- Prompt/incident selector
- Investigation history
- Live activity / tool-call timeline
- Evidence cards
- Root-cause summary
- Impact panel
- Customer priority list
- Recommended actions
- Approval status

## Incident report
- Executive summary
- Timeline
- Root cause and confidence rationale
- Confirmed evidence
- Affected products/orders/customers
- Impact metrics
- Recommended actions
- Missing/contradictory information
- Audit trail
- Export/print

## Approval center
- Pending actions
- Action preview
- Risk label
- Supporting evidence
- Affected entities
- Approve / reject
- Execution status and audit history

## Systems/MCP page
For each system:
- Connected/disconnected state
- API health
- MCP server status
- Tool count
- Tool names/descriptions
- Last discovery timestamp
- Endpoint count
- Newly discovered tool indicator

## UI priorities
P0: dashboard, investigation action, live status, findings/evidence, impact, recommendation  
P1: approvals, reports, systems page  
P2: graph visualization, replay, extra animation, export polish

---

# 14. AI Tool Collaboration Workflow

Use AI coding tools as role-based teammates. Avoid overlapping edits to the same files.

## Suggested roles
### Primary coding agent (Cursor or equivalent)
- Own repository implementation
- Implement APIs and integrations
- Run tests and fix errors
- Maintain project structure

### Architect/reviewer (Claude or equivalent)
- Review architecture and contracts
- Inspect backend/agent reliability
- Review security, edge cases, and code quality
- Provide critique, not duplicate implementation

### UI-focused agent (Gemini or equivalent)
- Create design concepts and frontend components
- Work against agreed API contracts/mock data
- Avoid modifying backend architecture

### Product/QA partner (ChatGPT)
- Maintain plan and scope
- Write focused prompts
- Review outputs
- Debug integration
- Design test scenarios
- Evaluate project against judging criteria
- Maintain demo narrative and submission checklist

## Shared AI instructions
- Read existing code before changing.
- Do not overwrite working features without explanation.
- Work only on assigned files/modules.
- Follow shared schema/API contracts.
- Make small incremental changes.
- Run tests and report output.
- Avoid inventing package versions, endpoints, or successful tests.
- Do not commit secrets.
- If blocked, report exact error and attempted fix.
- Every task includes acceptance criteria.

## Task prompt template
```text
Task:
Context:
Files/modules allowed to modify:
Existing interfaces:
Requirements:
Do not:
Acceptance criteria:
Test commands:
Report:
```

## Integration strategy
1. Establish API contracts first.
2. One agent owns backend system APIs.
3. One agent owns frontend.
4. One agent reviews architecture and tests.
5. Integrate in small PRs/commits.
6. Avoid simultaneous edits to the same files.
7. Use Git branches for independent tasks.
8. Merge and test frequently.

---

# 15. Milestones and Time Plan

The event guide and current schedule may leave a compressed window. Recalculate against the official deadline and your actual team availability. This is a task-based schedule, not a promise that every phase fits.

## Milestone 0 — Setup / scope lock (1–2 hours)
- [ ] Create GitHub repo(s)
- [ ] Create project directories
- [ ] Agree on API schemas
- [ ] Create task board / issue list
- [ ] Set up environment and `.env.example`
- [ ] Confirm model/API access
- [ ] Confirm Synapse CLI works
**Exit criteria:** repo, contracts, tools and environment are ready.

## Milestone 1 — Two APIs + seed data (4–7 hours)
- [ ] Orders schema/routes
- [ ] Inventory schema/routes
- [ ] Deterministic seed data
- [ ] OpenAPI docs
- [ ] Unit/API tests
- [ ] Health endpoints
**Exit criteria:** both APIs independently run and data is internally consistent.

## Milestone 2 — Synapse/MCP proof (2–4 hours)
- [ ] Generate Orders MCP
- [ ] Generate Inventory MCP
- [ ] Select endpoints
- [ ] Connect both to test client
- [ ] Test representative tools
- [ ] Save configuration and instructions
**Exit criteria:** agent/test script can call both systems through MCP.

## Milestone 3 — Agent investigation (4–7 hours)
- [ ] Orchestrator and investigation state
- [ ] Tool calling
- [ ] Cross-system correlation
- [ ] Evidence collection
- [ ] Root cause
- [ ] Impact calculations
- [ ] Customer prioritization
- [ ] Report generation
- [ ] Failure/partial result handling
**Exit criteria:** terminal-based investigation completes end-to-end and is repeatable.

## Milestone 4 — Frontend MVP (5–8 hours)
- [ ] App shell/navigation
- [ ] Dashboard
- [ ] Investigation screen
- [ ] Live activity
- [ ] Evidence/findings
- [ ] Impact visualizations
- [ ] Recommendations
- [ ] Connect backend
**Exit criteria:** judge can run investigation and understand findings without reading terminal logs.

## Milestone 5 — Approval and audit (2–3 hours)
- [ ] Action preview
- [ ] Approve/reject
- [ ] Simulated action execution
- [ ] Idempotency
- [ ] Audit trail
**Exit criteria:** approval/rejection reliably changes demo state as expected.

## Milestone 6 — Synapse live discovery (1–2 hours)
- [ ] Add `/inventory/incidents`
- [ ] Restart API
- [ ] `synapse build --discover`
- [ ] Verify new tool
- [ ] Agent calls new tool
- [ ] UI shows updated tools
**Exit criteria:** live capability expansion is demonstrated successfully.

## Milestone 7 — Polish, testing, submission (3–5 hours)
- [ ] Run full test suite
- [ ] Run 5 demo rehearsals
- [ ] Fix P0 bugs
- [ ] Prepare README
- [ ] Prepare architecture image
- [ ] Record backup video
- [ ] Prepare pitch
- [ ] Check repository and secrets
**Exit criteria:** submission is complete and demo is stable.

---

# 16. Prompt Library

## Prompt 1 — Orders API
Build the Nova Orders API for SignalOps using FastAPI, SQLAlchemy, and SQLite. Implement Order, Customer, and Shipment models; GET /orders with filters and pagination; GET /orders/{id}; GET /orders/delayed; GET /orders/at-risk; GET /customers/{id}; GET /customers/{id}/orders; GET /shipments; GET /analytics/order-health. Seed deterministic fictional data linked to the inventory incident. Use clear schemas, validation, errors, docs, and tests. Do not build frontend or agent. Run tests and report changed files/results.

## Prompt 2 — Inventory API
Build the Nova Inventory API using FastAPI, SQLAlchemy, and SQLite. Implement Product, Warehouse, Stock, and SyncStatus. Add GET /products; GET /products/{id}; GET /stock; GET /stock/low; GET /stock/{product_id}; GET /warehouses; GET /sync/status; GET /analytics/stock-health. Seed deterministic data: SKU-104 shortage at W1, available recovery stock at W2, and failed sync with timestamp/reason. Do not implement `/inventory/incidents` initially; reserve it for the live Synapse discovery demo. Add tests and report results.

## Prompt 3 — Agent architecture
Act as a senior AI-agent engineer. Design a controlled investigation pipeline using two Synapse MCP servers (Orders and Inventory). It must retrieve delayed orders, customer/shipment data, stock and warehouse availability, sync status; correlate IDs; verify root-cause hypotheses; calculate impact deterministically; rank affected customers with documented rules; generate an evidence-backed plan; and require approval for consequential actions. Define schemas, interfaces, error handling, tests, and implementation order before coding. No fabricated evidence, no unbounded agent loop, and partial results on tool failures.

## Prompt 4 — Frontend
Build SignalOps in React + TypeScript + Tailwind + shadcn/ui + Recharts. Premium dark operations command-center style, not a generic chat app. Pages: Overview, Investigations, Reports, Approvals, Systems/MCP. Dashboard metrics include delayed orders, affected customers, open complaints, order value at risk. Investigation workspace includes request, live tool activity, evidence cards, root cause, impact, customer prioritization and actions. Use mock data initially and reusable components. Keep responsive and focus on polish. Do not change backend code.

## Prompt 5 — Reviewer
Review SignalOps as a hackathon judge and senior engineer. Check Track 3 compliance, Synapse centrality, separate systems, MCP calls, cross-system correctness, evidence quality, deterministic calculations, failure handling, approval safety, UI clarity, originality, and demo reliability. Refer to concrete code/features. List critical issues first and prioritize fixes by impact/time.

## Prompt 6 — Demo QA
Act as QA. Run the planned SignalOps scenarios and verify expected outcomes: normal incident, no delays, Orders MCP unavailable, Inventory MCP unavailable, conflicting data, missing support data, approval rejection, approval success, duplicate action prevention, and live endpoint discovery. Do not claim a test passed unless you ran it. Report reproducible bugs with steps and expected/actual results.

---

# 17. Test Plan

## API tests
- [ ] Health endpoint
- [ ] Orders list/filter/pagination
- [ ] Delayed orders
- [ ] Customer lookup/history
- [ ] Shipment lookup
- [ ] Inventory by product/warehouse
- [ ] Low-stock query
- [ ] Sync status
- [ ] Incident endpoint after live addition

## Agent tests
- [ ] Normal incident gives correct root cause and evidence
- [ ] No delayed orders returns no incident (no hallucination)
- [ ] Orders MCP failure produces partial report
- [ ] Inventory MCP failure produces partial report
- [ ] Missing fields are handled
- [ ] Conflicting data is flagged
- [ ] Empty ticket/complaint set doesn't break analysis
- [ ] Calculations match known seeded values
- [ ] No unbounded tool loops
- [ ] Unknown root cause remains unknown
- [ ] Recommendation matches stock constraints

## Action safety tests
- [ ] Rejection causes no state change
- [ ] Approval executes only requested action
- [ ] Quantity cannot exceed available stock
- [ ] IDs are validated
- [ ] Duplicate execution blocked
- [ ] Failed execution not marked successful
- [ ] Audit log created

## Frontend tests / QA
- [ ] Loading states
- [ ] Error states
- [ ] Partial investigation state
- [ ] Responsive desktop/mobile
- [ ] Evidence/source labels visible
- [ ] Approval dialog clear
- [ ] No fake “success” states
- [ ] Tool list refresh after Synapse discovery
- [ ] Dashboard numbers match backend

---

# 18. Demo Script (approximately 3 minutes)

## 0:00–0:20 — Hook
Show NovaCommerce dashboard: delayed orders, complaints, VIP customers, incident.
Say: “Orders know about customers. Inventory knows about stock. Support knows who's unhappy. SignalOps connects the dots.”

## 0:20–0:45 — Investigation prompt
Run: “Investigate all delayed orders. Identify root cause, affected customers, business impact, and recommended actions.”

## 0:45–1:15 — Synapse proof
Show activity:
- Orders MCP: delayed orders retrieved
- Orders MCP: shipment/customer information retrieved
- Inventory MCP: stock retrieved
- Inventory MCP: sync status retrieved
- Cross-system correlation completed

Explain briefly that these are existing APIs exposed as MCP tools using Synapse.

## 1:15–1:45 — Root cause and evidence
Show root cause and source-backed evidence. Show confirmed vs hypothesis. Show impact and customer ranking.

## 1:45–2:15 — Resolution
Show proposed transfer/reprioritization/draft communication. Preview the action and approval requirement.

## 2:15–2:35 — Approval
Approve simulated action. Show changed state and audit record.

## 2:35–3:00 — Synapse live discovery
Add the new `/inventory/incidents` endpoint. Run `synapse build --discover`. Show new tool and agent use. Close with: “We didn't rewrite these business systems. We made them agent-ready.”

## Demo reliability
- Use deterministic seed data.
- Warm the API/model if necessary.
- Prepare exact prompt.
- Avoid slow/unpredictable calls where possible.
- Record a backup video.
- Keep terminal commands ready.
- Have a backup screenshot/result for the live discovery stage.
- Never present a mocked result as a live tool call.

---

# 19. Additional Demo Questions (Track 3 requirement)

Prepare at least two questions that clearly require both systems:

### Question A
“Which customers are affected by delayed orders caused by low stock, and have they raised support tickets?”

### Question B
“Which delayed orders can be fulfilled using inventory from another warehouse, and how many can we recover?”

### Question C (optional)
“Prioritize the delayed orders based on SLA breach, customer tier, and complaints. Explain why each customer is prioritized.”

For each question, show the source-system evidence and cross-system correlation.

---

# 20. Judge-facing Explanation

## Why this problem?
Businesses often need to investigate operational incidents across systems. SignalOps reduces manual investigation and makes findings traceable.

## Why Synapse?
The business APIs already exist. Synapse exposes selected capabilities as MCP tools without rewriting those systems. The copilot relies on those generated tools to investigate across systems. Live discovery demonstrates that a newly added API capability can become agent-accessible.

## What is technically meaningful?
- Two separate business systems
- Two MCP servers generated using Synapse
- Cross-system data correlation
- Evidence-based root cause
- Deterministic impact analysis
- Safe action approval
- Audit trail
- Live capability discovery

## What is novel about the product?
Not the chat interface. The workflow: cross-system investigation, evidence, impact, recommendation, approval, and system action.

---

# 21. Final Submission Checklist

## Product
- [ ] Dashboard opens
- [ ] Incident visible
- [ ] Investigation starts
- [ ] Live activity visible
- [ ] Agent uses Orders MCP
- [ ] Agent uses Inventory MCP
- [ ] Findings backed by evidence
- [ ] Impact calculations verified
- [ ] Recommendations displayed
- [ ] Approval/rejection works
- [ ] Simulated action works
- [ ] Audit trail visible
- [ ] Live Synapse discovery works

## Track 3
- [ ] Two independent systems
- [ ] Both Synapse-generated MCP servers
- [ ] Two cross-system questions demonstrated
- [ ] New endpoint added live
- [ ] `synapse build --discover` shown
- [ ] Agent uses new tool

## Repository
- [ ] README
- [ ] Setup instructions
- [ ] Architecture diagram
- [ ] Environment example
- [ ] No secrets
- [ ] Tests
- [ ] Demo instructions
- [ ] License if appropriate
- [ ] Clear repository names and commit history

## Presentation
- [ ] 3-minute demo script
- [ ] 60–90-second pitch (if required)
- [ ] Backup recording
- [ ] Demo rehearsed at least 5 times
- [ ] Claims are accurate
- [ ] No fake live integrations
- [ ] Judges can understand the value quickly

---

# 22. Risk Register

| Risk | Mitigation |
|---|---|
| Synapse integration takes too long | Test Synapse on minimal API immediately; do not postpone |
| Generated MCP tools are poorly named/selected | Carefully select endpoints and descriptions; test each tool |
| LLM invents root cause | Evidence schema, structured output, verification, explicit unknowns |
| API seed data inconsistent | Deterministic seed script; consistency checks |
| Demo model is slow | Prewarm; simplify workflow; prepare recording |
| MCP server fails live | Rehearsal, logs, backup video, fallback results clearly labeled |
| UI consumes too much time | Mock UI in parallel; backend contracts first |
| Multiple AI tools create conflicting code | Assign ownership, define interfaces, use branches |
| Action causes unintended change | Simulated environment, approval, validation, idempotency |
| Counts overlap and confuse judges | Explicit metric definitions; do not add overlapping counts |
| Deadline approaches with unfinished features | Freeze P0 scope; cut stretch features |

---

# 23. Definition of Done

SignalOps is ready to submit when a judge can:

1. Open the dashboard and immediately understand the incident.
2. Start an investigation with natural language.
3. See the agent call tools from both Synapse MCP servers.
4. See correct cross-system findings.
5. Inspect evidence supporting the root cause.
6. See deterministic impact calculations and customer prioritization.
7. Review a resolution plan.
8. Approve or reject an action safely.
9. See an audit record.
10. Watch a new endpoint added and discovered through Synapse.
11. Ask the agent a question that uses the new tool.
12. Understand why Synapse is central to the product.

**Winning principle:** Build a smaller, reliable, complete product with a powerful demonstration—not a large unfinished feature set.
