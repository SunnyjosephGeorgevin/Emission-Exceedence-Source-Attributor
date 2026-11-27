import { ReactNode } from 'react'
import { statusKey } from '../utils/normalize'
const colors: Record<string, string> = {
  pending: 'bg-zinc-500/20 text-zinc-300', running: 'bg-sky-500/15 text-sky-300', recovering: 'bg-amber-500/15 text-amber-300',
  'awaiting approval': 'bg-amber-500/15 text-amber-300', approved: 'bg-emerald-500/15 text-emerald-300', rejected: 'bg-rose-500/15 text-rose-300',
  completed: 'bg-teal-500/15 text-teal-300', failed: 'bg-red-500/15 text-red-300',
}
export const statusHex: Record<string, string> = { pending: '#71717a', running: '#38bdf8', recovering: '#f59e0b', 'awaiting approval': '#f59e0b', approved: '#34d399', rejected: '#fb7185', completed: '#2dd4bf', failed: '#ef4444' }
export const Badge = ({ status }: { status: string }) => (
  <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium capitalize whitespace-nowrap ${colors[statusKey(status)] ?? 'bg-zinc-500/20 text-zinc-300'}`}>{statusKey(status)}</span>)
export const Tag = ({ children, tone = 'zinc' }: { children: ReactNode; tone?: 'zinc' | 'teal' | 'amber' | 'violet' | 'sky' }) => {
  const t = { zinc: 'bg-white/5 text-zinc-400', teal: 'bg-teal-500/15 text-teal-300', amber: 'bg-amber-500/15 text-amber-300', violet: 'bg-violet-500/15 text-violet-300', sky: 'bg-sky-500/15 text-sky-300' }[tone]
  return <span className={`px-2 py-0.5 rounded text-[10px] uppercase tracking-wide ${t}`}>{children}</span>
}
export const Card = ({ title, children, right, className = '' }: { title?: string; children: ReactNode; right?: ReactNode; className?: string }) => (
  <section className={`bg-panel rounded-2xl border border-white/10 p-5 ${className}`}>
    {title && <div className="flex justify-between items-center mb-4 gap-2"><h3 className="font-medium text-zinc-100 text-[15px]">{title}</h3>{right}</div>}{children}</section>)
export const Kpi = ({ label, value, accent = 'text-white' }: { label: string; value: ReactNode; accent?: string }) => (
  <div className="rounded-xl border border-white/10 bg-white/[.03] p-4"><div className="text-[11px] uppercase tracking-wide text-zinc-500">{label}</div><div className={`text-2xl font-semibold mt-1 ${accent}`}>{value}</div></div>)
export const Loading = () => <div className="p-8 text-zinc-500 animate-pulse">Loading…</div>
export const ErrorBox = ({ msg, retry }: { msg: string; retry?: () => void }) => (
  <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl p-4 text-sm">{msg}{retry && <button onClick={retry} className="ml-3 underline">Retry</button>}</div>)
export const Empty = ({ text }: { text: string }) => <div className="p-6 text-center text-zinc-500 text-sm">{text}</div>
export const Missing = ({ what }: { what: string }) => (
  <div className="border border-dashed border-amber-500/30 bg-amber-500/5 text-amber-300/90 rounded-xl p-3 text-xs">Not available from the API: {what}. Nothing is fabricated.</div>)
export const Json = ({ data }: { data: any }) => (
  <details className="text-xs"><summary className="cursor-pointer text-zinc-500">Raw backend response</summary>
    <pre className="mt-2 bg-black text-zinc-300 p-3 rounded-lg overflow-auto max-h-96">{JSON.stringify(data, null, 2)}</pre></details>)
export const Bar = ({ label, value, max, color = '#2fb5a0' }: { label: string; value: number; max: number; color?: string }) => (
  <div className="flex items-center gap-3 text-sm"><span className="w-32 capitalize text-zinc-400">{label}</span>
    <div className="flex-1 h-2 bg-white/5 rounded"><div className="h-full rounded transition-all" style={{ width: `${max ? (value / max) * 100 : 0}%`, background: color }} /></div><span className="w-6 text-right">{value}</span></div>)
export const Disclaimer = () => (
  <div className="text-xs text-zinc-400 bg-white/5 border border-white/10 rounded-xl px-3 py-2">Facility screening scores are heuristic prioritization scores and do not establish causation or legal responsibility.</div>)
