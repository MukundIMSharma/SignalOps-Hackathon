# Synapse setup (only commands verified to work)

CLI: `@2ndbrainlabs-ai/synapse-cli` v0.1.9, Node v24.16.0.

```bash
npm install -g @2ndbrainlabs-ai/synapse-cli   # worked 2026-11-24
synapse --version                              # 0.1.9
```

Relevant `synapse build` flags (from `synapse build --help`, v0.1.9):
- `--auto` Auto track (HTTP endpoints via runner) — what Track 3 needs
- `--base-url <url>` deployed base URL of the API
- `--server-name <name>` MCP server name; rebuild with the same name updates it
- `--endpoints "<list>"` choose endpoints without the picker
- `--discover` rescan code instead of reusing last build's endpoints (live demo step)
- `--smart-names` name tools from handler source
- `--local --provider ... --model ...` build on your own model instead of hosted

API key: `synapse config set-key` (prompts, keeps key out of shell history). Not done yet.
