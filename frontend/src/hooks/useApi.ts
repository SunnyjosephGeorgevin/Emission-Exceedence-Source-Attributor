import { useCallback, useEffect, useRef, useState } from 'react'
/** Fetch + optional polling. `pollMs` maps latest data -> ms (0 = stop). */
export function useApi<T>(fn: () => Promise<T>, deps: any[] = [], pollMs?: (d: T | null) => number) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const fnRef = useRef(fn); fnRef.current = fn
  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)
    try { setData(await fnRef.current()); setError(null) } catch (e: any) { setError(e.message) } finally { setLoading(false) }
  }, [])
  useEffect(() => { load() }, deps) // eslint-disable-line
  useEffect(() => {
    const ms = pollMs?.(data) ?? 0
    if (!ms) return
    const t = setTimeout(() => load(true), ms); return () => clearTimeout(t)
  }, [data]) // eslint-disable-line
  return { data, error, loading, reload: () => load(true) }
}
