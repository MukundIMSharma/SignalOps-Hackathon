# Judging checklist (plan §21) — with evidence

Status as of 2026-11-24. ✅ verified (how) · 🟡 ready, needs the live demo · ⬜ to do (human).

## Track 3
| Item | Status | Evidence |
|---|---|---|
| Two independent systems | ✅ | `nova-orders/`, `nova-inventory/`: separate apps, venvs, SQLite, seeds, tests |
| Both Synapse-generated MCP servers | ✅ | server_ids in `docs/synapse-setup.md`; `signalops-backend/tests/test_mcp_tools.py` calls all 17 tools |
| ≥2 cross-system questions | ✅ | UI "Cross-system questions" A/B/C from one report; evidence from both systems (`rehearse.py` checks) |
| New endpoint added live | 🟡 | rehearsed (DEMO_STATE rehearsal #1); paste-ready `docs/live-endpoint.md` |
| `synapse build --discover` shown | 🟡 | rehearsed: 3.7 s, same server_id |
| Agent uses new tool | 🟡 | rehearsed: "★ New capability in use" + evidence INV-2026-042 (`docs/demo-backup/m6-*.png`); unit test `test_uses_incidents_tool_only_when_discovered` |

## Product
| Item | Status | Evidence |
|---|---|---|
| Dashboard opens, incident visible | ✅ | `docs/demo-backup/overview.png` |
| Investigation starts, live activity | ✅ | SSE events; browser-verified |
| Agent uses Orders MCP and Inventory MCP | ✅ | trace shows both servers on every run (`rehearse.py`) |
| Findings backed by evidence | ✅ | `test_normal_incident` (no dangling evidence refs, both systems) |
| Impact calculations verified | ✅ | `test_impact_matches_demo_state`, `rehearse.py` (5/5 runs identical) |
| Recommendations displayed | ✅ | Recommended actions + Approvals page |
| Approval / rejection works | ✅ | `tests/test_approvals.py` (8 tests), browser e2e |
| Simulated action works | ✅ | simulated ledger; drafts never sent |
| Audit trail visible | ✅ | Approvals → Audit trail; `audit.jsonl` |
| Live Synapse discovery works | 🟡 | rehearsed |

## Repository
| Item | Status | Evidence |
|---|---|---|
| README, setup, demo instructions | ✅ | `README.md`, `docs/demo-script.md` |
| Architecture diagram | ✅ | Mermaid in `README.md`, `docs/architecture.md` |
| Environment example | ✅ | `.env.example` |
| No secrets | ✅ | `git grep` + full-history scan for key patterns: 0 hits; `.env`, `.synapse/config.json` ignored |
| Tests | ✅ | 12 + 9 + 37 automated; `scripts/rehearse.py` |
| License | ✅ | MIT, `LICENSE` |

## Presentation (human)
| Item | Status |
|---|---|
| 3-minute demo script | ✅ `docs/demo-script.md` |
| 60–90 s pitch | ⬜ |
| Backup recording | ⬜ |
| Demo rehearsed 5× (by presenter) | ⬜ (5 automated runs passed; presenter run-throughs still needed) |
| Claims accurate / no fake live integrations | ✅ Template summary labelled; simulated actions labelled; screenshots only as backup |
