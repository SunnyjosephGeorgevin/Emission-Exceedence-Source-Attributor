import { FormEvent, useState } from 'react'
import { Link } from 'react-router-dom'
import { Badge, Card, ErrorBox, Json } from '../components/ui'
import { api } from '../services/api'
import { useApi } from '../hooks/useApi'
import { find, isLive, normalizeInv } from '../utils/normalize'
export default function NewInvestigation() {
  const [f, setF] = useState({ stationId: '', latitude: '', longitude: '' })
  const [busy, setBusy] = useState(false); const [err, setErr] = useState<string | null>(null); const [created, setCreated] = useState<any>(null)
  const id = created ? String(find(created, ['investigation_id', 'id']) ?? '') : ''
  const live = useApi(async () => (id ? normalizeInv(await api.get(id)) : null), [id], d => d && isLive(d.status) ? 3000 : 0)
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setBusy(true); setErr(null)
    try { setCreated(await api.create({ stationId: f.stationId.trim(), latitude: Number(f.latitude), longitude: Number(f.longitude) })) } catch (x: any) { setErr(x.message) } finally { setBusy(false) }
  }
  const inp = 'rounded-lg px-3 py-2 w-full text-sm'
  return (<div className="space-y-4 max-w-2xl">
    <Card><form onSubmit={submit} className="space-y-4">
      <label className="block text-sm">Monitoring Station ID<input required className={inp} value={f.stationId} onChange={e => setF({ ...f, stationId: e.target.value })} /></label>
      <div className="grid grid-cols-2 gap-4"><label className="block text-sm">Station Latitude<input required type="number" step="any" min={-90} max={90} className={inp} value={f.latitude} onChange={e => setF({ ...f, latitude: e.target.value })} /></label>
        <label className="block text-sm">Station Longitude<input required type="number" step="any" min={-180} max={180} className={inp} value={f.longitude} onChange={e => setF({ ...f, longitude: e.target.value })} /></label></div>
      <button disabled={busy} className="bg-brand hover:bg-brand-dark disabled:opacity-50 text-white px-5 py-2 rounded-lg text-sm">{busy ? 'Submitting…' : 'Start investigation'}</button></form></Card>
    {err && <ErrorBox msg={err} />}
    {created && <Card title="Submission confirmed"><div className="text-sm space-y-2"><div>Investigation ID: <b>{id || '(not returned)'}</b></div>
      <div>Status: {live.data ? <Badge status={live.data.status} /> : '…'} <span className="text-zinc-500 ml-2">Stage: {live.data?.stage ?? '—'} (auto-refreshing)</span></div>
      {id && <Link className="text-teal-300 underline" to={`/investigations/${id}`}>Open investigation →</Link>}<Json data={created} /></div></Card>}</div>)
}
