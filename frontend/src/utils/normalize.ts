import type { Investigation } from '../types'
const n = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, '')
/** Recursively find first value whose key matches any alias. */
export function find(obj: any, aliases: string[], depth = 0): any {
  if (obj == null || typeof obj !== 'object' || depth > 6) return undefined
  const al = aliases.map(n)
  if (!Array.isArray(obj)) for (const k of Object.keys(obj)) if (al.includes(n(k)) && obj[k] != null) return obj[k]
  for (const v of Object.values(obj)) { const r = find(v, aliases, depth + 1); if (r !== undefined) return r }
  return undefined
}
export const toArray = (d: any): any[] => Array.isArray(d) ? d : d?.items ?? d?.investigations ?? d?.results ?? d?.data ?? []
export function normalizeInv(r: any): Investigation {
  const id = String(find(r, ['investigation_id', 'id']) ?? '?')
  return {
    id, raw: r,
    stationId: String(find(r, ['station_id', 'monitoring_station', 'station']) ?? '—'),
    status: String(find(r, ['status']) ?? 'unknown'),
    lat: Number(find(r, ['station_latitude', 'station_lat', 'latitude', 'lat'])),
    lon: Number(find(r, ['station_longitude', 'station_lon', 'longitude', 'lon', 'lng'])),
    stage: String(find(r, ['current_stage', 'stage']) ?? '—'),
    createdAt: find(r, ['created_at', 'created', 'timestamp']),
    durationSec: Number(find(r, ['execution_time', 'duration_seconds', 'duration', 'execution_duration'])) || undefined,
  }
}
export const statusKey = (s: string) => s.toLowerCase().replace(/[_-]/g, ' ').trim()
export const isLive = (s: string) => ['pending', 'running', 'recovering'].includes(statusKey(s))
export const fmtDate = (d?: string) => { if (!d) return '—'; const x = new Date(d); return isNaN(+x) ? String(d) : x.toLocaleString() }
export const fmtDur = (s?: number) => s == null ? '—' : s < 60 ? `${s.toFixed(1)}s` : `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`
export const show = (v: any) => v == null ? '—' : typeof v === 'object' ? JSON.stringify(v) : String(v)
