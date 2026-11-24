# SignalOps backend

Controlled investigation workflow over the two Synapse-generated MCP servers.

```bash
python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt
# needs ../.env (SYNAPSE_API_KEY, GEMINI_API_KEY) and both APIs running on 8001/8002
.venv/Scripts/python list_tools.py            # tools on both MCP servers
.venv/Scripts/python investigate.py           # terminal investigation (add --json for the full report)
.venv/Scripts/python -m pytest -q             # unit + MCP integration tests
```

- `agent/orchestrator.py` — fixed stages, bounded tool calls (budget 60, 1 retry, 20s timeout), evidence, findings, actions
- `agent/correlation.py`, `impact.py`, `prioritization.py` — deterministic logic (no LLM)
- `agent/narrative.py` + `prompts/report_writer.md` — Gemini executive summary; labelled template fallback
- `mcp_clients/servers.py` — Synapse MCP stdio sessions (`npx @2ndbrainlabs-ai/synapse-mcp`)
