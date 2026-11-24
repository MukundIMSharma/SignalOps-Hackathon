# SignalOps — Claude Code instructions

AI business incident investigator for the 2nd Brain Labs × Geek Room Vibe-a-thon, Track 3 (copilot across two systems via Synapse Auto MCP). Full plan: `docs/MASTER_PLAN.md`.

## Every session
1. Read `docs/PROGRESS.md` and `docs/CONTRACTS.md` before starting any task.
2. After each task, update `docs/PROGRESS.md` (checkboxes, Current focus, Last completed, Next up, date).
3. Record any API schema, endpoint, MCP tool name, or evidence/finding schema change in `docs/CONTRACTS.md` in the same change.
4. Record non-obvious choices in `docs/DECISIONS.md` (`date — decision — reason`).
5. Record bugs/blockers in `docs/KNOWN_ISSUES.md` with exact error text and what was tried.
6. Keep `docs/DEMO_STATE.md` in sync with seed data and rehearsal status.
7. Exact Synapse commands/flags that worked go in `docs/synapse-setup.md` (create it when the first one works).
8. Never mark something done without running its tests and seeing them pass.
9. Plans written by Superpowers skills go under `docs/plans/`, nowhere else.

## Shared AI instructions (plan §14)
- Read existing code before changing.
- Do not overwrite working features without explanation.
- Work only on assigned files/modules.
- Follow shared schema/API contracts (`docs/CONTRACTS.md`).
- Make small incremental changes.
- Run tests and report output.
- Avoid inventing package versions, endpoints, or successful tests.
- Do not commit secrets (`.env` stays local; only `.env.example` is committed).
- If blocked, report exact error and attempted fix.
- Every task includes acceptance criteria.

## Non-negotiables (plan §1, §5, §10, §12)
- Orders and Inventory stay separate, independently runnable codebases with separate SQLite DBs.
- The main agent workflow reaches business data only through Synapse-generated MCP tools. Direct HTTP only for health checks/test setup, clearly separated.
- Counts, totals, SLA breaches, stock math, rankings, idempotency, approval state: deterministic code, never the LLM.
- Never fabricate tool results; never mark a root cause `confirmed` without evidence; tool failures produce a labeled partial report.
- No consequential action without explicit approval. All actions are simulated.
- Do not add `GET /inventory/incidents` until the live-discovery demo (Milestone 6).

## Stack
- Backend APIs: Python + FastAPI, SQLite + SQLAlchemy, Pydantic, pytest
- Agent: Python controlled workflow (no agent framework), FastAPI orchestrator, SSE streaming
- MCP: Synapse Auto-generated servers (Node.js 20+ for the CLI)
- Frontend: React + TypeScript + Vite, Tailwind + shadcn/ui, Recharts

## Repo layout
```text
signalops/
├── CLAUDE.md
├── docs/                 # MASTER_PLAN, PROGRESS, CONTRACTS, DECISIONS, KNOWN_ISSUES, DEMO_STATE, plans/
├── nova-orders/          # Orders API (FastAPI + SQLite)
├── nova-inventory/       # Inventory API (FastAPI + SQLite)
├── signalops-backend/    # main.py (API), agent/, mcp_clients/, services/, prompts/
├── signalops-frontend/   # React app
└── scripts/              # start-demo.ps1, reset-demo.ps1, rehearse.py
```
Details per module: `docs/MASTER_PLAN.md` §6.

## Task template
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
