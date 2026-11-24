import { Link } from 'react-router-dom'
import { useFetch } from '../api'
import { Card, ErrorNote, InvBadge, Mono, time } from '../components/ui'
import type { InvestigationSummary } from '../types'

export default function Reports() {
  const { data, error } = useFetch<InvestigationSummary[]>('/api/investigations')
  const done = data?.filter(i => i.headline !== undefined) ?? []
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-zinc-50">Incident reports</h1>
      {error && <ErrorNote>{error}</ErrorNote>}
      <Card>
        {!done.length && <p className="text-sm text-zinc-500">No reports yet. Run an investigation first.</p>}
        <ul className="divide-y divide-zinc-800">
          {done.map(i => (
            <li key={i.id}>
              <Link to={`/reports/${i.id}`} className="flex items-center gap-3 py-2.5 hover:bg-zinc-800/40">
                <Mono>{i.id}</Mono><InvBadge s={i.status} />
                <span className="min-w-0 flex-1 truncate text-sm text-zinc-200">{i.headline}</span>
                <span className="text-xs text-zinc-500">{time(i.created_at)} UTC</span>
              </Link>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  )
}
