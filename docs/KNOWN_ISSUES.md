# Known issues

Format per issue: title, status (open/workaround/fixed), exact error text, what was tried, next step.

## Open
- **MCP runner needs key in env** — status: open. `[synapse-mcp-runner] SYNAPSE_API_KEY and SYNAPSE_SERVER_ID environment variables are required.` User adds SYNAPSE_API_KEY to .env.
- **Starlette deprecation warning in tests** — status: open, harmless. `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`

## Fixed
- **Synapse API key missing** — fixed 2026-11-24 via `synapse config set-key --global`.
- **Synapse detected wrong paths (router prefix ignored)** — fixed 2026-11-24, full paths in decorators.
- **Synapse CLI not installed** — fixed 2026-11-24: `npm install -g @2ndbrainlabs-ai/synapse-cli` (v0.1.9).
- **No GitHub remote** — fixed 2026-11-24: origin = https://github.com/MukundIMSharma/SignalOps-Hackathon.git, main pushed.
- **Seed count overlaps undefined** — fixed 2026-11-24, locked in DEMO_STATE.md.
