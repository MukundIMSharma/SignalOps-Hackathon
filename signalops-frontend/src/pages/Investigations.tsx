import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { startInvestigation, useFetch, useInvestigation } from '../api'
import { Timeline, ActionsList, Activity, CrossSystemAnswers, EvidenceList, Findings, Gaps, Impact, Narrative, Priorities } from '../components/report'
import { Card, ErrorNote, InvBadge, Mono, time } from '../components/ui'
import type { InvestigationSummary } from '../types'

const DEMO_PROMPT = 'Investigate all delayed orders. Identify the root cause, which customers are affected, the business impact, and what we should do next.'

export default function Investigations() {
  const { id } = useParams()
  const nav = useNavigate()
  const { data: list, reload } = useFetch<InvestigationSummary[]>('/api/investigations')
  const [request, setRequest] = useState(DEMO_PROMPT)
  const [starting, setStarting] = useState(false)
  const [startErr, setStartErr] = useState<string | null>(null)

  const run = async () => {
    setStarting(true); setStartErr(null)
    try { const inv = await startInvestigation(request); reload(); nav(`/investigations/${inv.id}`) }
    catch (e) { setStartErr(String((e as Error).message)) }
    finally { setStarting(false) }
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[16rem_1fr]">
      <aside className="space-y-3">
        <h1 className="text-xl font-semibold text-zinc-50">Investigations</h1>
        <Card title="History">
          {!list?.length && <p className="text-sm text-zinc-500">No investigations yet.</p>}
          <ul className="-mx-2 space-y-1">
            {list?.map(i => (
              <li key={i.id}>
                <Link to={`/investigations/${i.id}`} className={`block rounded px-2 py-1.5 hover:bg-zinc-800 ${i.id === id ? 'bg-zinc-800' : ''}`}>
                  <div className="flex items-center justify-between gap-2"><Mono>{i.id}</Mono><InvBadge s={i.status} /></div>
                  <div className="text-[11px] text-zinc-500">{time(i.created_at)} UTC</div>
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      </aside>

      <div className="min-w-0 space-y-4">
        <Card title="New investigation">
          <label htmlFor="req" className="sr-only">Investigation request</label>
          <textarea id="req" value={request} onChange={e => setRequest(e.target.value)} rows={2}
            className="w-full resize-none rounded border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-indigo-500" />
          <div className="mt-2 flex items-center justify-between gap-3">
            <p className="text-[11px] text-zinc-500">Runs a fixed, bounded workflow over the Orders and Inventory MCP servers. Your request is recorded with the report.</p>
            <button onClick={run} disabled={starting || !request.trim()}
              className="shrink-0 rounded bg-indigo-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50">
              {starting ? 'Starting…' : 'Run investigation'}
            </button>
          </div>
          {startErr && <div className="mt-2"><ErrorNote>Could not start: {startErr}</ErrorNote></div>}
        </Card>
        {id ? <Workspace id={id} onStatus={reload} /> : <p className="text-sm text-zinc-500">Run an investigation or pick one from the history.</p>}
      </div>
    </div>
  )
}

function Workspace({ id, onStatus }: { id: string; onStatus: () => void }) {
  const { inv, events, error } = useInvestigation(id)
  useEffect(onStatus, [inv?.status, onStatus])  // keep the history badges in sync
  if (error) return <ErrorNote>{error}</ErrorNote>
  if (!inv) return <p className="animate-pulse text-sm text-zinc-500">Loading {id}…</p>
  const r = inv.report
  const calls = events.filter(e => e.type === 'tool_call')
  const servers = new Set(calls.map(e => e.server))
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-lg font-semibold text-zinc-50"><Mono>{inv.id}</Mono></h2>
        <InvBadge s={inv.status} />
        <span className="text-xs text-zinc-500">{calls.length} MCP tool calls across {servers.size} server(s){r && <> · data as of <Mono>{time(r.as_of)}</Mono></>}</span>
        {r && <Link to={`/reports/${inv.id}`} className="ml-auto text-sm text-indigo-300 hover:underline">Open incident report →</Link>}
      </div>
      <p className="text-sm italic text-zinc-400">“{inv.request}”</p>

      <div className="grid gap-4 2xl:grid-cols-[1fr_26rem]">
        <div className="min-w-0 space-y-4">
          {!r && inv.status !== 'failed' && <Card><p className="animate-pulse text-sm text-indigo-300">Investigating — querying both systems…</p></Card>}
          {inv.status === 'failed' && <ErrorNote>The investigation failed before producing a report. Nothing below is inferred. See the activity log.</ErrorNote>}
          {r && <>
            <Gaps gaps={r.gaps} />
            <Narrative n={r.narrative} />
            <Findings r={r} />
            <Timeline r={r} />
            <Impact r={r} />
            <CrossSystemAnswers r={r} />
            <Priorities r={r} limit={10} />
            <ActionsList actions={r.actions} />
            {r.actions.some(a => a.approval_status === 'pending') &&
              <p className="text-sm text-zinc-400">Consequential actions need explicit approval → <Link to="/approvals" className="text-indigo-300 hover:underline">Approvals</Link></p>}
            <EvidenceList items={r.evidence} />
          </>}
        </div>
        <Card title="Live activity" className="2xl:sticky 2xl:top-4 2xl:self-start">
          <div className="max-h-[75vh] overflow-y-auto pr-1"><Activity events={events} /></div>
        </Card>
      </div>
    </div>
  )
}
