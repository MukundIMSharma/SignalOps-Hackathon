# Known issues

Format per issue: title, status (open/workaround/fixed), exact error text, what was tried, next step.

## Open
- **Synapse CLI not installed** — status: open. `which synapse` → not found; `npx --no-install synapse` → `npm error could not determine executable to run`. Need the install command from the participant guide (not guessing the package name).
- **No GitHub remote** — status: open. `gh` CLI not installed (`gh: command not found`). Need repo URL from user, or install gh.
- **Starlette deprecation warning in tests** — status: open, harmless. `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`

## Fixed
- **Seed count overlaps undefined** — fixed 2026-11-24, locked in DEMO_STATE.md.
