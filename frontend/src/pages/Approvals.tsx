import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, Empty, ErrorBox, Json, Loading } from '../components/ui'
import { useInvestigations } from '../hooks/useInvestigations'
import { api } from '../services/api'
import { useApi } from '../hooks/useApi'
import { Facilities, Interpretation } from './Details'
import { statusKey } from '../utils/normalize'
function Review({ id, onDone }: { id: string; onDone: () => void }) {
  const { data, error, loading } = useApi(async () => ({ inv: await api.get(id), appr: await api.approval(id).catch(() => null) }), [id])
  const [name, setName] = useState(''); const [com, setCom] = useState(''); const [busy, setBusy] = useState(false); const [err, setErr] = useState<string | null>(null)
  if (loading) return <Loading />; if (error) return <ErrorBox msg={error} />
  const decide = async (kind: 'approve' | 'reject') => {
    if (!name.trim()) return setErr('Reviewer name is required.')
    if (!window.confirm(`Confirm: ${kind.toUpperCase()} investigation ${id} as "${name}"? This is a recorded human decision.`)) return
    setBusy(true); setErr(null)
    try { await api[kind](id, { reviewer: name.trim(), comments: com }); onDone() } catch (e: any) { setErr(e.message) } finally { setBusy(false) }
  }
  return (<div className="space-y-4 mt-4"><div className="text-xs font-semibold uppercase text-zinc-500">Screened facilities (candidates only)</div><Facilities raw={data!.inv} />
    <div className="text-xs font-semibold uppercase text-zinc-500">AI interpretation</div><Interpretation raw={data!.inv} />
    {data!.appr && <Json data={data!.appr} />}
    <div className="grid md:grid-cols-2 gap-3"><input placeholder="Reviewer name *" value={name} onChange={e => setName(e.target.value)} className="rounded-lg px-3 py-2 text-sm" />
      <input placeholder="Comments" value={com} onChange={e => setCom(e.target.value)} className="rounded-lg px-3 py-2 text-sm" /></div>
    {err && <ErrorBox msg={err} />}
    <div className="flex gap-3"><button disabled={busy} onClick={() => decide('approve')} className="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm disabled:opacity-50">Approve</button>
      <button disabled={busy} onClick={() => decide('reject')} className="bg-rose-600 text-white px-4 py-2 rounded-lg text-sm disabled:opacity-50">Reject</button></div></div>)
}
export default function Approvals() {
  const { data, error, loading, reload } = useInvestigations(); const [open, setOpen] = useState<string | null>(null)
  if (loading) return <Loading />; if (error) return <ErrorBox msg={error} retry={reload} />
  const rows = (data ?? []).filter(i => statusKey(i.status) === 'awaiting approval')
  return (<div className="space-y-4">Approval Center
    {!rows.length ? <Card><Empty text="No investigations are awaiting approval." /></Card> : rows.map(i => (
      <Card key={i.id} title={`Investigation ${i.id} · Station ${i.stationId}`} right={<div className="space-x-3 text-sm"><Link className="text-teal-300" to={`/investigations/${i.id}`}>Full details</Link>
        <button className="underline" onClick={() => setOpen(open === i.id ? null : i.id)}>{open === i.id ? 'Close' : 'Review'}</button></div>}>
        {open === i.id && <Review id={i.id} onDone={() => { setOpen(null); reload() }} />}</Card>))}</div>)
}
