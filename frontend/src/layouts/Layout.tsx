import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useInvestigations } from '../hooks/useInvestigations'
import { statusKey } from '../utils/normalize'
const I = (d: string) => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d={d} /></svg>
const nav: [string, string, string, string, string][] = [
  ['/', 'Overview', 'M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z', 'Overview', 'AI-assisted emission investigation and source attribution support'],
  ['/investigations', 'Investigations', 'M9 3h6l4 4v14H5V3h4zM9 13h6M9 17h6', 'Investigations', 'All investigations from the backend'],
  ['/new', 'New Investigation', 'M12 5v14M5 12h14', 'New Investigation', 'Start an exceedance source-attribution investigation'],
  ['/air-quality', 'Air Quality', 'M3 20V10M9 20V4M15 20v-8M21 20v-5', 'Air Quality', 'Ambient evidence per investigation'],
  ['/facilities', 'Facility Analysis', 'M3 21V9l6 4V9l6 4V4h6v17zM7 21v-3', 'Facility Analysis', 'Screening candidates per investigation'],
  ['/approvals', 'Approval Center', 'M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6zM9 12l2 2 4-4', 'Approval Center', 'Human review is mandatory'],
  ['/system', 'System Monitoring', 'M3 12h4l3-8 4 16 3-8h4', 'System Monitoring', 'Workflow and operational status'],
  ['/settings', 'Settings', 'M12 15a3 3 0 100-6 3 3 0 000 6zM19 12l2-1-2-4-2 1-2-1-1-2h-4l-1 2-2 1-2-1-2 4 2 1v2l-2 1 2 4 2-1 2 1 1 2h4l1-2 2-1 2 1 2-4-2-1z', 'Settings', 'Backend connection']]
export default function Layout() {
  const { pathname } = useLocation(); const { data } = useInvestigations()
  const waiting = (data ?? []).filter(i => statusKey(i.status) === 'awaiting approval').length
  const cur = nav.find(n => n[0] === '/' ? pathname === '/' : pathname.startsWith(n[0])) ?? (pathname.startsWith('/investigations/') ? nav[1] : nav[0])
  return (
    <div className="flex min-h-screen">
      <aside className="w-[68px] shrink-0 bg-[#0b0b0c] border-r border-white/10 flex flex-col items-center py-4 gap-2 sticky top-0 h-screen">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-400 to-emerald-700 flex items-center justify-center text-black font-bold mb-4" title="ECOINTEL">E</div>
        {nav.map(([to, label, d]) => (
          <NavLink key={to} to={to} end={to === '/'} title={label} aria-label={label} className={({ isActive }) => `group relative w-11 h-11 rounded-xl flex items-center justify-center transition ${isActive ? 'bg-white/10 text-teal-300 ring-1 ring-teal-400/40' : 'text-zinc-500 hover:text-zinc-200 hover:bg-white/5'}`}>
            {I(d)}<span className="pointer-events-none absolute left-14 z-50 whitespace-nowrap rounded-md bg-zinc-800 px-2 py-1 text-xs text-zinc-100 opacity-0 group-hover:opacity-100 transition">{label}</span></NavLink>))}
      </aside>
      <div className="flex-1 min-w-0">
        <header className="flex items-center justify-between px-6 lg:px-8 py-5">
          <div><div className="flex items-center gap-3"><h1 className="text-2xl font-semibold text-white">{cur[3]}</h1><span className="hidden md:inline text-[11px] tracking-widest text-teal-300/80 uppercase">ECOINTEL · Industrial Emission Intelligence</span></div>
            <p className="text-sm text-zinc-500 mt-0.5">{cur[4]}</p></div>
          <div className="flex items-center gap-4">
            <NavLink to="/approvals" title={`${waiting} awaiting approval`} aria-label="Notifications" className="relative w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-zinc-300">
              {I('M6 8a6 6 0 1112 0c0 7 3 8 3 8H3s3-1 3-8zM10 21h4')}{waiting > 0 && <span className="absolute -top-0.5 -right-0.5 bg-amber-500 text-black text-[10px] rounded-full w-4 h-4 flex items-center justify-center font-bold">{waiting}</span>}</NavLink>
            <div className="flex items-center gap-2"><div className="w-9 h-9 rounded-full bg-zinc-700 flex items-center justify-center text-sm">EO</div><div className="hidden sm:block text-sm"><div className="text-zinc-200">Environmental Officer</div><div className="text-[11px] text-zinc-500">Reviewer</div></div></div></div>
        </header>
        <main className="px-6 lg:px-8 pb-10 max-w-[1500px]"><Outlet /></main>
      </div>
    </div>)
}
