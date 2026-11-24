import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, useFetch } from '../api'
import { Badge, Card, ErrorNote, Loading, Mono, ServerBadge, SeverityBadge, StatusBadge, time } from '../components/ui'
import type { Action, ApprovalRow, AuditEntry, Simulation } from '../types'

export default function Approvals() {
  const rows = useFetch<ApprovalRow[]>('/api/approvals')
  const sim = useFetch<Simulation>('/api/simulation')
  const log = useFetch<AuditEntry[]>('/api/audit')
  const refresh = () => { rows.reload(); sim.reload(); log.reload() }
  const pending = rows.data?.filter(r => r.approval_status === 'pending') ?? []
  const decided = rows.data?.filter(r => r.approval_status !== 'pending') ?? []

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-zinc-50">Approvals</h1>
        <p className="text-sm text-zinc-500">No consequential action runs without explicit approval. Execution is simulated and re-validated against live data first.</p>
      </div>
      {rows.error && <ErrorNote>{rows.error}</ErrorNote>}
      {rows.loading && !rows.data && <Loading what="approvals" />}

      <Card title={`Pending (${pending.length})`}>
        {rows.data && !pending.length && <p className="text-sm text-zinc-500">Nothing awaiting approval. <Link to="/investigations" className="text-indigo-300 hover:underline">Run an investigation</Link> to get proposals.</p>}
        <div className="space-y-3">{pending.map(r => <PendingAction key={r.investigation_id + r.action_id} r={r} onDone={refresh} />)}</div>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card title="Decided actions">
          {!decided.length && <p className="text-sm text-zinc-500">None yet.</p>}
          <ul className="space-y-2.5">{decided.map(r => <DecidedAction key={r.investigation_id + r.action_id} a={r} inv={r.investigation_id} />)}</ul>
        </Card>
        <SimulatedState s={sim.data} />
      </div>

      <Card title="Audit trail" actions={<span className="text-[11px] text-zinc-500">append-only · newest first</span>}>
        {!log.data?.length && <p className="text-sm text-zinc-500">No audit entries.</p>}
        <div className="max-h-96 overflow-y-auto">
          <table className="w-full text-xs">
            <thead className="sticky top-0 bg-zinc-900 text-left text-zinc-500"><tr><th className="py-1">When (UTC)</th><th>Event</th><th>Investigation</th><th>Action</th><th>By</th><th>Detail</th></tr></thead>
            <tbody>
              {log.data?.map(e => (
                <tr key={e.audit_id} className="border-t border-zinc-800/70 align-top">
                  <td className="whitespace-nowrap py-1 pr-2 font-mono text-zinc-500">{time(e.at)}</td>
                  <td className="pr-2"><EventBadge e={e.event} /></td>
                  <td className="pr-2"><Mono>{e.investigation_id ?? '—'}</Mono></td>
                  <td className="pr-2"><Mono>{e.action_id ? `${e.action_id} ${e.action_type}` : '—'}</Mono></td>
                  <td className="pr-2 text-zinc-400">{e.approver ?? '—'}</td>
                  <td className="text-zinc-400">{e.error ?? (e.result ? summarizeResult(e.result) : e.note || (e.root_cause as string) || '')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}

function PendingAction({ r, onDone }: { r: ApprovalRow; onDone: () => void }) {
  const [confirm, setConfirm] = useState<'approve' | 'reject' | null>(null)
  const [approver, setApprover] = useState('ops-lead')
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  const submit = async () => {
    setBusy(true); setErr(null)
    try {
      await api(`/api/investigations/${r.investigation_id}/actions/${r.action_id}/${confirm}`, {
        method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ approver, note }),
      })
      onDone()
    } catch (e) { setErr(String((e as Error).message)) } finally { setBusy(false) }
  }

  return (
    <div className="rounded border border-zinc-800 bg-zinc-950/40 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <SeverityBadge s={r.risk_level === 'high' ? 'high' : r.risk_level === 'medium' ? 'medium' : 'low'} />
        <span className="font-medium text-zinc-100">{r.description}</span>
        <span className="ml-auto text-xs text-zinc-500"><Link to={`/investigations/${r.investigation_id}`} className="hover:underline"><Mono>{r.investigation_id}</Mono></Link> · <Mono>{r.action_id}</Mono></span>
      </div>
      <div className="mt-2 grid gap-3 text-xs md:grid-cols-3">
        <div>
          <div className="mb-1 font-semibold uppercase tracking-wide text-zinc-500">Preview of change</div>
          <Preview a={r} />
          <p className="mt-1 text-zinc-400">Expected: {r.expected_outcome}</p>
        </div>
        <div>
          <div className="mb-1 font-semibold uppercase tracking-wide text-zinc-500">Affected ({r.affected_entities.length})</div>
          <p className="font-mono text-[11px] leading-relaxed text-zinc-400">{r.affected_entities.slice(0, 18).join(', ')}{r.affected_entities.length > 18 ? ` +${r.affected_entities.length - 18} more` : ''}</p>
        </div>
        <div>
          <div className="mb-1 font-semibold uppercase tracking-wide text-zinc-500">Supporting evidence</div>
          <ul className="space-y-1">
            {r.evidence.map(e => (
              <li key={e.evidence_id} className="text-zinc-300"><Mono>{e.evidence_id}</Mono> <ServerBadge s={e.source_system} /> <StatusBadge s={e.status} /> {e.claim}</li>
            ))}
          </ul>
        </div>
      </div>

      {!confirm ? (
        <div className="mt-3 flex gap-2">
          <button onClick={() => setConfirm('approve')} className="rounded bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-500">Approve…</button>
          <button onClick={() => setConfirm('reject')} className="rounded border border-zinc-600 px-3 py-1.5 text-sm text-zinc-200 hover:bg-zinc-800">Reject…</button>
        </div>
      ) : (
        <div role="dialog" aria-label={`Confirm ${confirm}`} className={`mt-3 rounded border p-3 ${confirm === 'approve' ? 'border-emerald-500/40 bg-emerald-500/5' : 'border-zinc-600 bg-zinc-800/40'}`}>
          <p className="text-sm text-zinc-200">
            {confirm === 'approve'
              ? <>Approve and execute <b>{r.action_id}</b>? It is re-validated against live data, then applied to the <b>simulated</b> ledger. It cannot be executed twice.</>
              : <>Reject <b>{r.action_id}</b>? Nothing will change.</>}
          </p>
          <div className="mt-2 flex flex-wrap items-end gap-2">
            <label className="text-xs text-zinc-400">Approver<input value={approver} onChange={e => setApprover(e.target.value)} className="ml-2 rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-sm text-zinc-100" /></label>
            <label className="min-w-48 flex-1 text-xs text-zinc-400">Note<input value={note} onChange={e => setNote(e.target.value)} className="ml-2 w-3/4 rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-sm text-zinc-100" /></label>
            <button onClick={submit} disabled={busy || !approver.trim()} className={`rounded px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50 ${confirm === 'approve' ? 'bg-emerald-600 hover:bg-emerald-500' : 'bg-zinc-600 hover:bg-zinc-500'}`}>
              {busy ? 'Working…' : `Confirm ${confirm}`}
            </button>
            <button onClick={() => setConfirm(null)} disabled={busy} className="px-2 py-1.5 text-sm text-zinc-400 hover:text-zinc-200">Cancel</button>
          </div>
          {err && <div className="mt-2"><ErrorNote>{err}</ErrorNote></div>}
        </div>
      )}
    </div>
  )
}

function Preview({ a }: { a: Action }) {
  const i = a.inputs as Record<string, unknown>
  switch (a.action_type) {
    case 'inventory_transfer':
      return <p className="text-zinc-200"><Mono>{String(i.product_id)}</Mono>: {String(i.source)} −{String(i.units)} → {String(i.destination)} +{String(i.units)} units</p>
    case 'prioritize_tickets':
      return <p className="text-zinc-200">{(i.ticket_ids as string[]).length} tickets → priority <b>{String(i.priority)}</b></p>
    case 'draft_customer_update':
      return <p className="text-zinc-200">Draft notice for {(i.customer_ids as string[]).length} customers · <b>not sent</b></p>
    default:
      return <pre className="whitespace-pre-wrap text-[11px] text-zinc-300">{JSON.stringify(i, null, 1)}</pre>
  }
}

function DecidedAction({ a, inv }: { a: Action; inv: string }) {
  const ex = a.execution
  return (
    <li className="text-sm">
      <div className="flex flex-wrap items-center gap-2">
        {a.approval_status === 'rejected' ? <Badge t="zinc" icon="✕">rejected</Badge>
          : ex?.status === 'succeeded' ? <Badge t="green" icon="✓">executed</Badge>
          : ex?.status === 'failed' ? <Badge t="red" icon="!">execution failed</Badge>
          : <Badge t="amber" icon="…">approved</Badge>}
        <span className="text-zinc-200">{a.description}</span>
      </div>
      <p className="mt-0.5 text-xs text-zinc-500"><Mono>{inv} · {a.action_id}</Mono> · by {a.approver} at {time(a.decided_at)} UTC{a.decision_note ? ` · “${a.decision_note}”` : ''}</p>
      {ex?.error && <p className="mt-0.5 text-xs text-red-300">{ex.error}</p>}
      {ex?.result && <p className="mt-0.5 text-xs text-zinc-400">{summarizeResult(ex.result)}</p>}
    </li>
  )
}

function SimulatedState({ s }: { s: Simulation | null }) {
  const empty = s && !s.transfers.length && !Object.keys(s.ticket_priorities).length && !s.incidents.length && !s.drafts.length
  return (
    <Card title="Simulated system changes" actions={<Badge t="zinc" icon="⚠">simulated — no real systems changed</Badge>}>
      {empty && <p className="text-sm text-zinc-500">No changes yet.</p>}
      <ul className="space-y-2 text-sm text-zinc-300">
        {s?.transfers.map(t => <li key={t.transfer_id}><Mono>{t.transfer_id}</Mono> moved {t.units} × <Mono>{t.product_id}</Mono> {t.source} → {t.destination}</li>)}
        {s && Object.keys(s.ticket_priorities).length > 0 &&
          <li>Ticket priority raised: <span className="font-mono text-xs text-zinc-400">{Object.entries(s.ticket_priorities).map(([k, v]) => `${k}→${v}`).join(', ')}</span></li>}
        {s?.incidents.map(i => <li key={i.incident_id}><Mono>{i.incident_id}</Mono> opened for {i.owner}: {i.title}</li>)}
        {s?.drafts.map(d => (
          <li key={d.draft_id}>
            <Mono>{d.draft_id}</Mono> draft for {d.recipients} customers <Badge t="amber" icon="✉">not sent</Badge>
            <p className="mt-1 rounded bg-black/30 p-2 text-xs text-zinc-400"><b>{d.subject}</b><br />{d.body}</p>
          </li>
        ))}
      </ul>
    </Card>
  )
}

function EventBadge({ e }: { e: string }) {
  const t = e === 'executed' || e === 'investigation_completed' ? 'green' : e === 'execution_failed' || e === 'investigation_failed' ? 'red'
    : e === 'duplicate_blocked' || e === 'rejected' ? 'amber' : 'zinc'
  return <Badge t={t}>{e.replaceAll('_', ' ')}</Badge>
}

function summarizeResult(r: Record<string, unknown>) {
  if ('transfer_id' in r) return `${r.transfer_id}: ${r.units} units ${r.source}→${r.destination}; ${r.source} left with ${r.source_remaining_after}`
  if ('tickets_updated' in r) return `${(r.tickets_updated as string[]).length} tickets → ${r.priority}`
  if ('draft_id' in r) return `${r.draft_id}: ${r.recipients} recipients, not sent`
  if ('incident_id' in r) return `${r.incident_id} → ${r.owner}`
  return JSON.stringify(r).slice(0, 120)
}
