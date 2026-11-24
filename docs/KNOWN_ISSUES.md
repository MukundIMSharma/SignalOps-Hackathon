# Known issues

Format per issue: title, status (open/workaround/fixed), exact error text, what was tried, next step.

## Open
- **Synapse API key missing** — status: open. `synapse -y init` → `Missing API Key — API key is required to use Synapse.` User must run `synapse config set-key` (interactive). Get key at synapse.2ndbrainlabs.ai.
- **Starlette deprecation warning in tests** — status: open, harmless. `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`

## Fixed
- **Synapse CLI not installed** — fixed 2026-11-24: `npm install -g @2ndbrainlabs-ai/synapse-cli` (v0.1.9).
- **No GitHub remote** — fixed 2026-11-24: origin = https://github.com/MukundIMSharma/SignalOps-Hackathon.git, main pushed.
- **Seed count overlaps undefined** — fixed 2026-11-24, locked in DEMO_STATE.md.
