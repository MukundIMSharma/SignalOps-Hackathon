import { useState } from 'react'
import type { Action, Evidence, Report, StreamEvent } from '../types'
import { Badge, Card, ErrorNote, Mono, ServerBadge, SeverityBadge, StatusBadge, money } from './ui'

export function Narrative({ n }: { n: Report['narrative'] }) {
  const label = n.source === 'llm' ? `AI summary · ${n.model}` : n.source === 'pending' ? 'Writing AI summary…' : 'Template summary (LLM unavailable)'
  return (
    <Card title="Executive summary" actions={<Badge t={n.source === 'llm' ? 'indigo' : 'zinc'} icon={n.source === 'llm' ? '✦' : '≡'}>{label}</Badge>}>
      {n.source === 'pending'
        ? <p className="animate-pulse text-sm text-zinc-500">The findings below are final; the narrative summary is still being written by the model.</p>
        : <p className="text-[15px] leading-relaxed text-zinc-200">{n.text}</p>}
      {n.error && <p className="mt-2 text-xs text-zinc-500">Model note: {n.error}</p>}
      <p className="mt-2 text-[11px] text-zinc-600">The summary only restates the findings below; all numbers are computed in code.</p>
    </Card>
  )
}

export function Findings({ r }: { r: Report }) {
  const ev = Object.fromEntries(r.evidence.map(e => [e.evidence_id, e]))
  return (
    <Card title="Findings">
      <ol className="space-y-4">
        {r.findings.map(f => (
          <li key={f.finding_id} className="border-l-2 border-zinc-700 pl-3">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge s={f.status} /><SeverityBadge s={f.severity} />
              <span className="font-medium text-zinc-100">{f.title}</span>
            </div>
            <p className="mt-1 text-sm text-zinc-300">{f.summary}</p>
            <p className="mt-1 text-xs text-zinc-500"><span className="text-zinc-400">Why {f.status}:</span> {f.confidence_explanation}</p>
            <div className="mt-1.5 flex flex-wrap gap-1">
              {f.evidence_ids.map(id => (
                <a key={id} href={`#${id}`} title={ev[id]?.claim} className="rounded bg-zinc-800 px-1.5 py-0.5 font-mono text-[11px] text-zinc-300 hover:bg-zinc-700">
                  {id} · {ev[id]?.source_system}
                </a>
              ))}
            </div>
          </li>
        ))}
      </ol>
    </Card>
  )
}

export function EvidenceList({ items }: { items: Evidence[] }) {
  return (
    <Card title={`Evidence (${items.length})`}>
      <div className="grid gap-2 md:grid-cols-2">
        {items.map(e => <EvidenceCard key={e.evidence_id} e={e} />)}
      </div>
    </Card>
  )
}

function EvidenceCard({ e }: { e: Evidence }) {
  const [open, setOpen] = useState(false)
  return (
    <div id={e.evidence_id} className="scroll-mt-4 rounded border border-zinc-800 bg-zinc-950/50 p-3 target:ring-1 target:ring-indigo-400">
      <div className="flex items-center justify-between gap-2">
        <Mono>{e.evidence_id}</Mono>
        <div className="flex gap-1"><ServerBadge s={e.source_system} /><StatusBadge s={e.status} /></div>
      </div>
      <p className="mt-1.5 text-sm text-zinc-200">{e.claim}</p>
      <p className="mt-1 text-[11px] text-zinc-500">
        <Mono>{e.source_tool}</Mono> → <Mono>{e.source_endpoint}</Mono>
      </p>
      {e.entity_ids.length > 0 && <p className="mt-1 truncate text-[11px] text-zinc-500" title={e.entity_ids.join(', ')}>Entities: {e.entity_ids.join(', ')}</p>}
      <button onClick={() => setOpen(!open)} className="no-print mt-1 text-[11px] text-indigo-300 hover:underline">{open ? 'Hide' : 'Show'} source data</button>
      {open && <pre className="mt-1 max-h-48 overflow-auto rounded bg-black/40 p-2 text-[11px] text-zinc-400">{JSON.stringify(e.data, null, 1)}</pre>}
    </div>
  )
}

const METRIC_LABELS: Record<string, string> = {
  delayed_orders_all_causes: 'Delayed orders (all causes)', incident_orders: 'Incident orders', sla_breached_orders: 'Past dispatch date',
  at_risk_orders: 'At risk', affected_customers: 'Affected customers', vip_customers_affected: 'VIP customers',
  customers_with_complaints: 'Customers with complaints', order_value_affected: 'Order value affected', units_affected: 'Units affected',
  stock_shortage_units: 'Stock shortage (units)', transferable_units: 'Transferable units', recoverable_orders: 'Recoverable orders',
  unrecoverable_orders: 'Still blocked after transfer',
}

export function Impact({ r }: { r: Report }) {
  if (!r.impact) return null
  const m = r.impact
  const rec = m.recoverable_orders.value, unrec = m.unrecoverable_orders.value, total = rec + unrec
  return (
    <Card title="Impact (computed in code)">
      <dl className="grid grid-cols-2 gap-x-4 gap-y-3 sm:grid-cols-3 xl:grid-cols-4">
        {Object.entries(m).map(([k, v]) => (
          <div key={k} title={v.definition}>
            <dt className="text-[11px] text-zinc-500">{METRIC_LABELS[k] ?? k}</dt>
            <dd className="text-lg font-semibold tabular-nums text-zinc-100">{k === 'order_value_affected' ? money(v.value) : v.value}</dd>
            <dd className="text-[10px] leading-snug text-zinc-600">{v.definition}</dd>
          </div>
        ))}
      </dl>
      {total > 0 && r.transfer_plan && (
        <div className="mt-5">
          <div className="mb-1.5 text-xs text-zinc-400">
            Transfer {r.transfer_plan.units} × <Mono>{r.transfer_plan.product_id}</Mono> {r.transfer_plan.source} → {r.transfer_plan.destination}: incident orders covered
          </div>
          {/* status split: good/critical with icon + text labels; 2px surface gap between segments */}
          <div className="flex h-7 gap-[2px] overflow-hidden rounded text-[12px] font-medium" role="img" aria-label={`${rec} recoverable, ${unrec} still blocked`}>
            <div className="flex items-center rounded-l bg-good/80 px-2 text-black" style={{ width: `${(rec / total) * 100}%` }} title={`${rec} orders recoverable by transfer`}>✓ {rec} recoverable</div>
            {unrec > 0 && <div className="flex items-center rounded-r bg-critical/80 px-2 text-white" style={{ width: `${(unrec / total) * 100}%` }} title={`${unrec} orders still blocked`}>✕ {unrec} blocked</div>}
          </div>
        </div>
      )}
      <p className="mt-3 text-[11px] text-zinc-600">Overlapping counts (VIP, complaints, breached) are subsets of the incident and are never added together.</p>
    </Card>
  )
}

export function Priorities({ r, limit }: { r: Report; limit?: number }) {
  const [all, setAll] = useState(false)
  if (!r.priorities) return null
  const rows = all || !limit ? r.priorities : r.priorities.slice(0, limit)
  const w = r.prioritization_weights
  return (
    <Card title="Customer priority" actions={<span className="text-[11px] text-zinc-500">Rule-based score, not an objective truth</span>}>
      <p className="mb-2 text-[11px] text-zinc-500">
        Weights: VIP +{w.vip} · SLA breached +{w.sla_breached} (+{w.per_day_overdue}/day, max 3) · open complaint +{w.open_complaint} · at risk +{w.at_risk}. Order value is not scored.
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-left text-[11px] uppercase tracking-wide text-zinc-500">
            <tr><th className="py-1 pr-2">#</th><th className="pr-2">Order</th><th className="pr-2">Customer</th><th className="pr-2 text-right">Score</th><th className="pr-2">Reasons</th><th className="text-right">Value</th><th className="pl-2">Transfer</th></tr>
          </thead>
          <tbody>
            {rows.map(p => (
              <tr key={p.order_id} className="border-t border-zinc-800/70">
                <td className="py-1.5 pr-2 tabular-nums text-zinc-500">{p.rank}</td>
                <td className="pr-2"><Mono>{p.order_id}</Mono></td>
                <td className="pr-2">{p.customer_name} {p.tier === 'vip' && <Badge t="indigo">VIP</Badge>}</td>
                <td className="pr-2 text-right tabular-nums font-medium">{p.score}</td>
                <td className="pr-2 text-xs text-zinc-400">{p.reasons.join(' · ')}</td>
                <td className="text-right tabular-nums text-zinc-400">{money(p.total_amount)}</td>
                <td className="pl-2">{p.recoverable_by_transfer ? <Badge t="green" icon="✓">covered</Badge> : <Badge t="red" icon="✕">blocked</Badge>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {limit && r.priorities.length > limit &&
        <button onClick={() => setAll(!all)} className="no-print mt-2 text-xs text-indigo-300 hover:underline">{all ? 'Show top ' + limit : `Show all ${r.priorities.length}`}</button>}
    </Card>
  )
}

/** Track 3 cross-system questions, answered from the same report (Orders × Inventory). */
export function CrossSystemAnswers({ r }: { r: Report }) {
  if (!r.priorities || !r.impact) return null
  const byCustomer = new Map<string, { name: string; complaint: boolean; vip: boolean }>()
  r.priorities.forEach(p => byCustomer.set(p.customer_id, { name: p.customer_name, complaint: p.has_open_complaint, vip: p.tier === 'vip' }))
  const withTickets = [...byCustomer.values()].filter(c => c.complaint)
  const rec = r.priorities.filter(p => p.recoverable_by_transfer)
  return (
    <Card title="Cross-system questions">
      <div className="space-y-4 text-sm">
        <div>
          <div className="font-medium text-zinc-100">A · Which customers are affected by delays caused by low stock, and have they raised tickets?</div>
          <p className="mt-1 text-zinc-300">
            {byCustomer.size} customers have orders blocked by the {r.transfer_plan?.product_id ?? 'affected SKU'} stock failure (Inventory). {withTickets.length} of them have open delay tickets (Orders):{' '}
            <span className="text-zinc-400">{withTickets.map(c => c.name + (c.vip ? ' (VIP)' : '')).join(', ')}</span>.
          </p>
        </div>
        <div>
          <div className="font-medium text-zinc-100">B · Which delayed orders can be fulfilled from another warehouse, and how many?</div>
          <p className="mt-1 text-zinc-300">
            {r.transfer_plan ? <>{r.transfer_plan.source} can spare {r.transfer_plan.units} units (Inventory), covering <b>{rec.length}</b> of {r.priorities.length} orders in priority order (Orders): </> : 'No warehouse has spare stock. '}
            <span className="font-mono text-xs text-zinc-400">{rec.map(p => p.order_id).join(', ')}</span>
          </p>
        </div>
        <div>
          <div className="font-medium text-zinc-100">C · Prioritize by SLA breach, tier and complaints, with reasons</div>
          <p className="mt-1 text-zinc-300">See the customer priority table: top is {r.priorities[0].customer_name} ({r.priorities[0].reasons.join('; ')}).</p>
        </div>
      </div>
    </Card>
  )
}

export function ActionsList({ actions }: { actions: Action[] }) {
  if (!actions.length) return null
  return (
    <Card title="Recommended actions">
      <ul className="space-y-3">
        {actions.map(a => (
          <li key={a.action_id} className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <Mono>{a.action_id}</Mono><SeverityBadge s={a.risk_level === 'high' ? 'high' : a.risk_level === 'medium' ? 'medium' : 'low'} />
                <span className="text-sm text-zinc-100">{a.description}</span>
              </div>
              <p className="mt-0.5 text-xs text-zinc-500">Expected: {a.expected_outcome} · evidence {a.evidence_ids.join(', ')}</p>
            </div>
            <ActionStatus a={a} />
          </li>
        ))}
      </ul>
    </Card>
  )
}

export function Gaps({ gaps }: { gaps: string[] }) {
  if (!gaps.length) return null
  return (
    <ErrorNote>
      <div className="font-medium">Partial report — some data could not be retrieved:</div>
      <ul className="mt-1 list-disc pl-5 text-xs">{gaps.map(g => <li key={g}>{g}</li>)}</ul>
    </ErrorNote>
  )
}

export function Activity({ events }: { events: StreamEvent[] }) {
  return (
    <ol className="space-y-1 text-[12px]">
      {events.map((e, i) => (
        <li key={i} className="flex items-start gap-2">
          {e.type === 'tool_call' ? (
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className={e.ok ? 'text-emerald-400' : 'text-red-400'} aria-label={e.ok ? 'ok' : 'error'}>{e.ok ? '✓' : '✕'}</span>
                <ServerBadge s={String(e.server)} />
                <span className="truncate font-mono text-zinc-200">{String(e.tool)}{Object.keys(e.args as object).length ? `(${Object.values(e.args as object).join(', ')})` : ''}</span>
                <span className="ml-auto shrink-0 tabular-nums text-zinc-500">{String(e.ms)}ms</span>
              </div>
              <div className="truncate pl-5 text-[11px] text-zinc-500">{String(e.summary)}</div>
            </div>
          ) : e.type === 'capability' ? (
            <span className="rounded bg-emerald-500/10 px-1.5 py-0.5 text-emerald-300 ring-1 ring-emerald-500/40">★ New capability in use: <span className="font-mono">{String(e.tool)}</span> ({String(e.server)} MCP)</span>
          ) : e.type === 'stage' ? (
            <span className="mt-1 text-[11px] font-semibold uppercase tracking-wide text-indigo-300">▸ {String(e.stage)}</span>
          ) : e.type === 'evidence' ? (
            <span className="text-zinc-400"><span className="font-mono text-zinc-500">{String(e.evidence_id)}</span> evidence: {String(e.claim)}</span>
          ) : e.type === 'status' && e.status === 'failed' ? (
            <span className="text-red-300">Investigation failed: {String(e.error)}</span>
          ) : e.type === 'narrative' ? (
            <span className="text-zinc-400">Summary ready ({String(e.source)})</span>
          ) : e.type === 'report' ? (
            <span className="text-zinc-300">Report ready — status {String(e.status).replace('_', ' ')}</span>
          ) : null}
        </li>
      ))}
    </ol>
  )
}

function ActionStatus({ a }: { a: Action }) {
  if (a.execution?.status === 'failed') return <Badge t="red" icon="!">execution failed</Badge>
  if (a.execution?.status === 'succeeded') return <Badge t="green" icon="✓">executed (simulated)</Badge>
  if (a.approval_status === 'rejected') return <Badge t="zinc" icon="✕">rejected</Badge>
  if (a.approval_status === 'pending') return <Badge t="amber" icon="⏸">pending approval</Badge>
  return <Badge t="zinc" icon="–">{a.approval_status === 'not_required' ? 'no approval needed' : a.approval_status}</Badge>
}
