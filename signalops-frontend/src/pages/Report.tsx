import { Link, useParams } from 'react-router-dom'
import { useInvestigation } from '../api'
import { Timeline, ActionsList, EvidenceList, Findings, Gaps, Impact, Narrative, Priorities } from '../components/report'
import { Card, ErrorNote, InvBadge, Mono, ServerBadge, time } from '../components/ui'

/** Printable incident report (plan §13). Browser print → PDF. */
export default function ReportPage() {
  const { id } = useParams()
  const { inv, error } = useInvestigation(id)
  if (error) return <ErrorNote>{error}</ErrorNote>
  if (!inv) return <p className="animate-pulse text-sm text-zinc-500">Loading…</p>
  const r = inv.report
  if (!r) return <p className="text-sm text-zinc-500">This investigation has no report yet. <Link className="text-indigo-300" to={`/investigations/${inv.id}`}>Open it</Link></p>
  const unknowns = r.findings.filter(f => f.status !== 'confirmed')
  return (
    <article className="mx-auto max-w-5xl space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold text-zinc-50">Incident report <Mono>{inv.id}</Mono></h1>
        <InvBadge s={inv.status} />
        <button onClick={() => window.print()} className="no-print ml-auto rounded border border-zinc-700 px-3 py-1.5 text-sm text-zinc-300 hover:bg-zinc-800">Print / save PDF</button>
      </div>
      <p className="text-xs text-zinc-500">Request: “{r.request}” · data as of {time(r.as_of)} · started {time(inv.created_at)} UTC · completed {time(inv.completed_at)} UTC</p>
      <Gaps gaps={r.gaps} />
      <Narrative n={r.narrative} />
      <Findings r={r} />
      <Timeline r={r} />
      <Card title="Missing or uncertain information">
        {unknowns.length === 0 && r.gaps.length === 0 ? <p className="text-sm text-zinc-400">None recorded.</p> : (
          <ul className="list-disc space-y-1 pl-5 text-sm text-zinc-300">
            {unknowns.map(f => <li key={f.finding_id}><b>{f.title}</b> ({f.status}): {f.confidence_explanation}</li>)}
            {r.gaps.map(g => <li key={g}>{g}</li>)}
          </ul>
        )}
      </Card>
      <Impact r={r} />
      <Priorities r={r} />
      <ActionsList actions={r.actions} />
      <EvidenceList items={r.evidence} />
      <Card title="Execution trace (audit of tool calls)">
        <table className="w-full text-xs">
          <thead className="text-left text-zinc-500"><tr><th className="py-1">#</th><th>Server</th><th>Tool</th><th>Args</th><th>Result</th><th className="text-right">ms</th></tr></thead>
          <tbody>
            {r.trace.map(t => (
              <tr key={t.seq} className="border-t border-zinc-800/70">
                <td className="py-1 text-zinc-500">{t.seq}</td><td><ServerBadge s={t.server} /></td>
                <td className="font-mono">{t.tool}</td><td className="font-mono text-zinc-400">{JSON.stringify(t.args)}</td>
                <td className={t.ok ? 'text-zinc-400' : 'text-red-300'}>{t.ok ? '✓ ' : '✕ '}{t.summary}</td>
                <td className="text-right tabular-nums text-zinc-500">{t.ms}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </article>
  )
}
