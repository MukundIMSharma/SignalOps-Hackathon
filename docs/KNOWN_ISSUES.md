# Known issues

Format per issue: title, status (open/workaround/fixed), exact error text, what was tried, next step.

## Open
- **Synapse Auto exposes no query params** — status: workaround. All non-path tools have empty input schema; `get_delayed_orders {"delay_reason": "carrier_exception"}` returned all 30. Tried `--smart-names` rebuild: no change. Workaround: default limit 200, agent filters in code and checks `total == len(items)`. Limit: breaks if any list grows past 200.
- **Starlette deprecation warning in tests** — status: open, harmless. `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`

## Fixed
- **MCP runner needs key in env** — fixed 2026-11-24, SYNAPSE_API_KEY in .env.
- **Synapse API key missing** — fixed 2026-11-24 via `synapse config set-key --global`.
- **Synapse detected wrong paths (router prefix ignored)** — fixed 2026-11-24, full paths in decorators.
- **Synapse CLI not installed** — fixed 2026-11-24: `npm install -g @2ndbrainlabs-ai/synapse-cli` (v0.1.9).
- **No GitHub remote** — fixed 2026-11-24: origin = https://github.com/MukundIMSharma/SignalOps-Hackathon.git, main pushed.
- **Seed count overlaps undefined** — fixed 2026-11-24, locked in DEMO_STATE.md.
