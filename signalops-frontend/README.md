# SignalOps frontend

React + TypeScript + Vite + Tailwind v4 + Recharts. Dark operations console.

```bash
npm install
npm run dev      # http://localhost:5173 — proxies /api to the backend on :8000
npm run build    # type-check + production build
```

Pages: Overview · Investigations (live SSE activity, findings, evidence, impact, priorities, cross-system answers, actions) · Incident reports (printable) · Approvals · Systems / MCP (tool inventory, "newly discovered" flag).
Types mirror `docs/CONTRACTS.md` in `src/types.ts`.
