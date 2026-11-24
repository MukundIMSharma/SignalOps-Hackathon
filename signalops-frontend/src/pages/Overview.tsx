import { useNavigate } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { startInvestigation, useFetch } from '../api'
import { Badge, Card, ErrorNote, InvBadge, Loading, Mono, SeverityBadge, Stat, money, time } from '../components/ui'
import type { InvestigationSummary, Overview as O } from '../types'

export default function Overview() {
  const { data, error, loading, reload } = useFetch<O>('/api/overview')
  const { data: invs } = useFetch<InvestigationSummary[]>('/api/investigations')
  const nav = useNavigate()
  const run = async () => nav(`/investigations/${(await startInvestigation()).id}`)

  const o = data?.orders
  const impact = data?.latest_investigation?.impact
  const failed = data?.sync?.filter(s => s.status === 'failed') ?? []
  const statusRows = o ? Object.entries(o.by_status).map(([status, n]) => ({ status, n })).sort((a, b) => b.n - a.n) : []

  return (
    <div className="space-y-5">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-zinc-50">Operations overview</h1>
          <p className="text-sm text-zinc-500">As of <Mono>{time(o?.as_of)}</Mono> (fixed demo clock) · live from Orders + Inventory MCP</p>
        </div>
        <div className="flex gap-2">
          <button onClick={reload} className="rounded border border-zinc-700 px-3 py-1.5 text-sm text-zinc-300 hover:bg-zinc-800">Refresh</button>
          <button onClick={run} className="rounded bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-500">Investigate delayed orders</button>
        </div>
      </div>

      {error && <ErrorNote>Overview unavailable: {error}</ErrorNote>}
      {data?.errors.map(e => <ErrorNote key={e}>Partial data — {e}</ErrorNote>)}
      {loading && !data && <Loading what="overview (connecting to MCP servers)" />}

      {o && (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Stat label="Delayed orders" value={o.delayed_orders} t="red"
            sub={`${o.sla_breached_orders} past dispatch date · ${o.at_risk_orders} at risk`} />
          <Stat label="Affected customers" value={impact ? impact.affected_customers.value : o.delayed_customers} t="amber"
            sub={impact ? 'Linked to the incident (latest investigation)' : 'Customers with any delayed order — run an investigation to link causes'} />
          <Stat label="Open complaints" value={o.open_delay_tickets} t="amber" sub={`Open delivery-delay tickets (${o.open_tickets} open tickets total)`} />
          <Stat label="Order value affected" value={money(impact ? impact.order_value_affected.value : o.delayed_order_value)}
            sub={impact ? 'Incident orders only (latest investigation)' : 'All delayed orders, any cause'} />
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="Active incidents" className="lg:col-span-2">
          {failed.length === 0 && data && <p className="text-sm text-zinc-500">No failing inventory syncs.</p>}
          {failed.map(s => (
            <div key={s.sync_id} className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2"><SeverityBadge s={s.severity} /><span className="font-medium text-zinc-100">{s.source} inventory sync failing</span></div>
                <p className="mt-1 text-sm text-zinc-400">{s.error_message}</p>
                <p className="mt-1 text-xs text-zinc-500">Since <Mono>{time(s.failing_since)}</Mono> · warehouse <Mono>{s.warehouse_id}</Mono> · SKUs <Mono>{s.affected_products.join(', ')}</Mono> · <Mono>{s.error_code}</Mono></p>
              </div>
              <button onClick={run} className="rounded border border-indigo-500/50 px-3 py-1.5 text-sm text-indigo-300 hover:bg-indigo-500/10">Investigate</button>
            </div>
          ))}
          {o && <p className="mt-3 border-t border-zinc-800 pt-3 text-xs text-zinc-500">
            Delays by recorded reason: {Object.entries(o.delayed_by_reason).map(([r, n]) => `${n} ${r.replaceAll('_', ' ')}`).join(' · ')}
          </p>}
        </Card>

        <Card title="Recent investigations">
          {!invs?.length && <p className="text-sm text-zinc-500">None yet.</p>}
          <ul className="space-y-2">
            {invs?.slice(0, 5).map(i => (
              <li key={i.id}>
                <button onClick={() => nav(`/investigations/${i.id}`)} className="w-full rounded px-2 py-1.5 text-left hover:bg-zinc-800">
                  <div className="flex items-center justify-between gap-2"><Mono>{i.id}</Mono><InvBadge s={i.status} /></div>
                  <div className="truncate text-xs text-zinc-400">{i.headline ?? i.request}</div>
                </button>
              </li>
            ))}
          </ul>
        </Card>

        <Card title="Orders by status" className="lg:col-span-2">
          {o && (
            <div className="h-56" role="img" aria-label={`Orders by status: ${statusRows.map(r => `${r.status} ${r.n}`).join(', ')}`}>
              <ResponsiveContainer>
                <BarChart data={statusRows} margin={{ top: 16, right: 8, bottom: 0, left: -16 }} barCategoryGap={8}>
                  <CartesianGrid vertical={false} stroke="#27272a" />
                  <XAxis dataKey="status" tick={{ fill: '#a1a1aa', fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis allowDecimals={false} tick={{ fill: '#71717a', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip cursor={{ fill: '#ffffff08' }} contentStyle={{ background: '#18181b', border: '1px solid #3f3f46', fontSize: 12 }}
                    labelStyle={{ color: '#e4e4e7' }} itemStyle={{ color: '#e4e4e7' }} formatter={(v) => [v, 'orders']} />
                  <Bar dataKey="n" fill="var(--color-series-1)" radius={[4, 4, 0, 0]} maxBarSize={56}>
                    <LabelList dataKey="n" position="top" fill="#d4d4d8" fontSize={12} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          {o && <p className="text-xs text-zinc-500">{o.total_orders} orders total.</p>}
        </Card>

        <Card title="Inventory alerts">
          {data?.low_stock?.length === 0 && <p className="text-sm text-zinc-500">No low stock.</p>}
          <ul className="space-y-2 text-sm">
            {data?.low_stock?.map(l => (
              <li key={l.product_id + l.warehouse_id} className="flex items-center justify-between gap-2">
                <span><Mono>{l.product_id}</Mono> @ <Mono>{l.warehouse_id}</Mono></span>
                <span className="flex items-center gap-2 text-xs text-zinc-400">
                  {l.available_quantity} / {l.reorder_threshold}
                  {l.available_quantity === 0 ? <Badge t="red" icon="▲">out</Badge> : <Badge t="amber" icon="•">low</Badge>}
                </span>
              </li>
            ))}
          </ul>
          {data?.stock && <p className="mt-3 border-t border-zinc-800 pt-3 text-xs text-zinc-500">
            Available / reorder threshold · {data.stock.failed_syncs} failing sync(s) · warehouses: {Object.entries(data.stock.warehouses_by_status).map(([s, n]) => `${n} ${s}`).join(', ')}
          </p>}
        </Card>
      </div>
    </div>
  )
}
