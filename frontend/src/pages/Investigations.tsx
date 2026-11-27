import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Badge, Card, Empty, ErrorBox, Loading } from '../components/ui'
import { useInvestigations } from '../hooks/useInvestigations'
import { fmtDate, fmtDur, statusKey } from '../utils/normalize'
const STATUSES = ['pending', 'running', 'recovering', 'awaiting approval', 'approved', 'rejected', 'completed', 'failed']
export default function Investigations() {
  const { data, error, loading, reload } = useInvestigations(); const nav = useNavigate()
  const [q, setQ] = useState(''); const [st, setSt] = useState('')
  if (loading) return <Loading />; if (error) return <ErrorBox msg={error} retry={reload} />
  const rows = (data ?? []).filter(i => (!st || statusKey(i.status) === st) && `${i.id} ${i.stationId}`.toLowerCase().includes(q.toLowerCase()))
  return (<div className="space-y-4">Investigations
    <Card><div className="flex gap-3 mb-4"><input value={q} onChange={e => setQ(e.target.value)} placeholder="Search ID or station…" className="rounded-lg px-3 py-2 text-sm flex-1" />
      <select value={st} onChange={e => setSt(e.target.value)} className="rounded-lg px-3 py-2 text-sm"><option value="">All statuses</option>{STATUSES.map(s => <option key={s}>{s}</option>)}</select></div>
      {!rows.length ? <Empty text="No investigations match." /> : <div className="overflow-x-auto"><table className="w-full text-sm"><thead className="text-left text-zinc-500"><tr>{['Investigation ID', 'Station', 'Created', 'Stage', 'Status', 'Execution time', ''].map(h => <th key={h} className="py-2 font-medium">{h}</th>)}</tr></thead>
        <tbody>{rows.map(i => <tr key={i.id} onClick={() => nav(`/investigations/${i.id}`)} className="border-t border-white/5 hover:bg-white/5 cursor-pointer">
          <td className="py-2.5 font-medium">{i.id}</td><td>{i.stationId}</td><td>{fmtDate(i.createdAt)}</td><td>{i.stage}</td><td><Badge status={i.status} /></td><td>{fmtDur(i.durationSec)}</td><td className="text-teal-300">View →</td></tr>)}</tbody></table></div>}</Card></div>)
}
