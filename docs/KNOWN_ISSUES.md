# Known issues

Format per issue: title, status (open/workaround/fixed), exact error text, what was tried, next step.

## Open
- **Synapse Auto exposes no query params** — status: workaround. All non-path tools have empty input schema; `get_delayed_orders {"delay_reason": "carrier_exception"}` returned all 30. Tried `--smart-names` rebuild: no change. Workaround: default limit 200, agent filters in code and checks `total == len(items)`. Limit: breaks if any list grows past 200.
- **Starlette deprecation warning in tests** — status: open, harmless. `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`

- **Gemini free tier slow / 503** — status: open. gemini-3.8-flash: `503 UNAVAILABLE ... experiencing high demand` once; then "Reply ok" took 155s (3.7-flash 75s, 3.5-flash 19s; 2.5-flash 404 retired). Demo risk. Next: try minimal thinking; keep LLM to one narrative call; deterministic report must work with LLM down.

## Fixed
- **MCP runner needs key in env** — fixed 2026-11-24, SYNAPSE_API_KEY in .env.
- **Synapse API key missing** — fixed 2026-11-24 via `synapse config set-key --global`.
- **Synapse detected wrong paths (router prefix ignored)** — fixed 2026-11-24, full paths in decorators.
- **Synapse CLI not installed** — fixed 2026-11-24: `npm install -g @2ndbrainlabs-ai/synapse-cli` (v0.1.9).
- **No GitHub remote** — fixed 2026-11-24: origin = https://github.com/MukundIMSharma/SignalOps-Hackathon.git, main pushed.
- **Seed count overlaps undefined** — fixed 2026-11-24, locked in DEMO_STATE.md.
