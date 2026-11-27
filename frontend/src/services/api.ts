// Centralized API layer. ALL backend field names live here + utils/normalize.ts.
// Request bodies match the backend contract. Paths have no prefix; Vite proxies them to 127.0.0.1:8000.
import type { ReviewPayload } from '../types'
const BASE = (import.meta as any).env?.VITE_API_BASE ?? ''

export class ApiError extends Error { constructor(msg: string, public status = 0) { super(msg) } }

async function req<T = any>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(BASE + path, { headers: { 'Content-Type': 'application/json' }, ...init })
  } catch {
    throw new ApiError('Cannot reach the backend at http://127.0.0.1:8000. Is FastAPI running?')
  }
  const text = await res.text()
  let body: any = text
  try { body = text ? JSON.parse(text) : null } catch { /* keep text */ }
  if (!res.ok) throw new ApiError(typeof body === 'string' ? body : JSON.stringify(body?.detail ?? body), res.status)
  return body as T
}

export const api = {
  list: () => req('/investigations'),
  get: (id: string) => req(`/investigations/${encodeURIComponent(id)}`),
  approval: (id: string) => req(`/investigations/${encodeURIComponent(id)}/approval`),
  create: (p: { stationId: string; latitude: number; longitude: number }) =>
    req('/investigations', { method: 'POST', body: JSON.stringify({ station_id: p.stationId, station_latitude: p.latitude, station_longitude: p.longitude }) }),
  approve: (id: string, p: ReviewPayload) =>
    req(`/investigations/${encodeURIComponent(id)}/approve`, { method: 'POST', body: JSON.stringify({ reviewer: p.reviewer, comments: p.comments }) }),
  reject: (id: string, p: ReviewPayload) =>
    req(`/investigations/${encodeURIComponent(id)}/reject`, { method: 'POST', body: JSON.stringify({ reviewer: p.reviewer, comments: p.comments }) }),
}
