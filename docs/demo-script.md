# Demo script (~3 minutes)

**Before going on stage**
1. `powershell -File scripts\start-demo.ps1 -Reset` → all four "up".
2. `python scripts\rehearse.py 1`, then **restart the backend window** (see below; clears the rehearsal's transfer), then open **Systems / MCP** once (sets the "newly discovered" baseline: 9 + 8 tools).
3. Run one investigation in the UI to warm Gemini (optional), then restart the backend again for a clean history.
4. Open `docs/live-endpoint.md` in an editor; have a terminal in `nova-inventory/` and the inventory API window ready.
5. Backup: `docs/demo-backup/*.png` + recorded video.

**Restarting a service window** (the windows opened by `start-demo.ps1` have no ↑ history for their command, and ↑ shows commands from other windows; type it):

| Window title | Ctrl+C, then type |
|---|---|
| `signalops-backend :8000` | `.venv\Scripts\python -m uvicorn main:app --port 8000` |
| `nova-inventory :8002` | `.venv\Scripts\python -m uvicorn app.main:app --port 8002` |

Each window already opens in its own folder; no `cd` needed. Ready when it prints `Application startup complete`.

Actions are in `<angle brackets>`; do them as you say the words around them. Button names match the UI exactly.

| Time | Screen | Say and do |
|---|---|---|
| 0:00–0:20 | **Overview** | `<Overview is already open in the sidebar>` "This is NovaCommerce. `<point at the Delayed orders tile>` 30 orders are delayed, `<point at Open complaints>` 9 customers have complained, and `<point at Active incidents>` there's a critical inventory sync failure at warehouse W1. Orders know about customers, inventory knows about stock, support knows who's unhappy. Nobody sees all three. SignalOps connects the dots." |
| 0:20–0:45 | **Investigations** | `<click Investigations in the sidebar>` "I'll ask it what an operations manager would ask." `<point at the pre-filled request box>` "Investigate all delayed orders: root cause, who's affected, business impact, and what to do next." `<click Run investigation>` |
| 0:45–1:15 | **Live activity** (right panel) | `<point at Live activity as lines appear>` "Every line is an MCP tool call. `<point at an Orders line>` Orders MCP for delayed orders, tickets and shipments. `<point at an Inventory line>` Inventory MCP for sync status, warehouses and stock. Synapse generated both servers from the existing APIs. We didn't rewrite them." `<wait for the status badge to change from running, about 4 s>` `<point at the header: "30 MCP tool calls across 2 server(s)">` |
| 1:15–1:45 | **Findings, Impact, Cross-system questions** | `<scroll to Findings>` "Root cause: the W1 sync failure left SKU-104 stuck at zero, which blocked 28 orders. `<point at the likely badge>` It's marked *likely*, not confirmed: each fact is confirmed at the source, but the causal link is inferred. `<point at the evidence references on the finding>` Every finding cites evidence from both systems. The other 2 delays are unrelated carrier exceptions, kept separate." `<scroll to Impact (computed in code)>` "24 customers, $7,224, 4 VIPs, 9 complaints, all computed in code, not by the AI." `<scroll to Cross-system questions and point at A, then B>` |
| 1:45–2:15 | **Customer priority, Recommended actions** | `<scroll to Customer priority>` "The ranking uses transparent rules, `<point at the Reasons column>` and each customer shows why." `<scroll to Recommended actions, point at the transfer action>` "W2 can spare 40 units without dropping below its reorder threshold. That recovers 20 of the 28 orders." `<point at pending approval>` "Nothing runs on its own." |
| 2:15–2:35 | **Approvals** | `<click Approvals in the sidebar>` `<on the transfer card A-001, point at Preview of change and Supporting evidence>` "This is exactly what will change and why." `<click Approve…>` `<click Confirm approve>` "It re-checks stock live through MCP, runs in a simulated ledger, and can't be executed twice." `<scroll to Audit trail, point at the new entry>` "Every decision goes into an append-only audit log." |
| 2:35–3:00 | **Live discovery** | "Now the business adds a new API." `<in your editor: create nova-inventory/app/routes/incidents.py from docs/live-endpoint.md and make the two edits in main.py>` `<in the nova-inventory :8002 window: Ctrl+C, then type the restart command from the table above>` `<in the terminal in nova-inventory/: paste the synapse build --discover command from docs/live-endpoint.md step 3>` "Synapse rediscovers the API in about 4 seconds." `<click Systems / MCP, then Refresh tools, point at ★ get_inventory_incidents newly discovered>` `<click Investigations, then Run investigation>` `<point at ★ New capability in use>` "The agent picked up the new tool with no code change and no restart. The root cause now cites incident INV-2026-042." Close: **"We didn't rewrite these business systems. We made them agent-ready."** |

**If something breaks:** Gemini slow → the summary shows "Template summary (LLM unavailable)"; say so, since all facts are computed in code. Discovery fails → show `docs/demo-backup/m6-*.png`. Never present a screenshot as live.
