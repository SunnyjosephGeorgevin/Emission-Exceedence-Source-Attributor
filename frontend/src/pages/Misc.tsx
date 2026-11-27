import { Link } from 'react-router-dom'
import { Badge, Card, Empty, ErrorBox, Loading } from '../components/ui'
import { useInvestigations } from '../hooks/useInvestigations'
export function Picker({ title }: { title: string }) {
  const { data, error, loading, reload } = useInvestigations()
  if (loading) return <Loading />; if (error) return <ErrorBox msg={error} retry={reload} />
  return (<div className="space-y-4">{title}
    <Card title="Analysis is per investigation — choose one">{!data?.length ? <Empty text="No investigations yet." /> : <ul className="divide-y">{data.map(i => (
      <li key={i.id} className="py-2 flex justify-between text-sm"><Link className="text-teal-300" to={`/investigations/${i.id}`}>{i.id} · {i.stationId}</Link><Badge status={i.status} /></li>))}</ul>}</Card></div>)
}
export const Settings = () => (<div className="space-y-4">Settings
  <Card title="Backend connection"><div className="text-sm space-y-1"><div>Requests go to <code>/investigations…</code>, proxied by Vite to <code>http://127.0.0.1:8000</code></div><div>Override with <code>VITE_API_BASE</code> in <code>.env</code>.</div>
    <div>Swagger: <a className="text-teal-300 underline" href="http://127.0.0.1:8000/docs" target="_blank">http://127.0.0.1:8000/docs</a></div></div></Card></div>)
