import { useCallback, useEffect, useState } from 'react'
import type { Investigation, StreamEvent } from './types'

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(path, init)
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}: ${(await r.text()).slice(0, 200)}`)
  return r.json() as Promise<T>
}

export const startInvestigation = (request?: string) =>
  api<Investigation>('/api/investigations', {
    method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(request ? { request } : {}),
  })

/** Fetch once; returns {data, error, loading, reload}. */
export function useFetch<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const reload = useCallback(() => {
    if (!path) return
    setLoading(true)
    api<T>(path).then(d => { setData(d); setError(null) }).catch(e => setError(String(e.message ?? e))).finally(() => setLoading(false))
  }, [path])
  useEffect(reload, [reload])
  return { data, error, loading, reload }
}

/** Investigation detail + live SSE events. Refetches the full record when the report or summary lands. */
export function useInvestigation(id: string | undefined) {
  const [inv, setInv] = useState<Investigation | null>(null)
  const [live, setLive] = useState<StreamEvent[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    let closed = false
    setInv(null); setLive([]); setError(null)
    const load = () => api<Investigation>(`/api/investigations/${id}`).then(d => !closed && setInv(d)).catch(e => setError(String(e.message)))
    load()
    const es = new EventSource(`/api/investigations/${id}/events`)
    es.onmessage = m => {
      const e = JSON.parse(m.data) as StreamEvent
      setLive(prev => [...prev, e])
      if (['report', 'narrative', 'done'].includes(e.type) || (e.type === 'status' && e.status === 'failed')) load()
      if (e.type === 'done' || (e.type === 'status' && e.status === 'failed')) es.close()
    }
    es.onerror = () => { es.close(); load() }  // stream ended or backend down: show last known state
    return () => { closed = true; es.close() }
  }, [id])

  return { inv, events: live.length ? live : inv?.events ?? [], error }
}
