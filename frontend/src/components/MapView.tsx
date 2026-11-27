import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
export interface Pin { lat: number; lon: number; kind: 'station' | 'facility'; label: string; color?: string; popup: string }
const esc = (s: string) => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]!))
export default function MapView({ pins, className = 'h-[380px]' }: { pins: Pin[]; className?: string }) {
  const el = useRef<HTMLDivElement>(null); const map = useRef<L.Map | null>(null); const layer = useRef<L.LayerGroup | null>(null)
  useEffect(() => {
    if (!el.current || map.current) return
    map.current = L.map(el.current, { zoomControl: true, attributionControl: true }).setView([13.08, 80.27], 9)
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18, attribution: '© OpenStreetMap contributors' }).addTo(map.current)
    layer.current = L.layerGroup().addTo(map.current)
    return () => { map.current?.remove(); map.current = null }
  }, [])
  useEffect(() => {
    const g = layer.current, m = map.current; if (!g || !m) return
    g.clearLayers()
    const valid = pins.filter(p => isFinite(p.lat) && isFinite(p.lon))
    valid.forEach(p => {
      const bg = p.kind === 'station' ? (p.color ?? '#2fb5a0') : '#f97316'
      const icon = L.divIcon({ className: '', iconSize: [26, 26], html: `<div class="pin" style="background:${bg};${p.kind === 'facility' ? 'border-radius:50%' : ''}">${p.kind === 'station' ? '◉' : '▲'}</div>` })
      L.marker([p.lat, p.lon], { icon, title: p.label }).bindPopup(`<b>${esc(p.label)}</b><br/>${p.popup}`).addTo(g)
    })
    if (valid.length) m.fitBounds(L.latLngBounds(valid.map(p => [p.lat, p.lon] as [number, number])).pad(0.3), { maxZoom: 13 })
    setTimeout(() => m.invalidateSize(), 50)
  }, [pins])
  return (<div className={`relative rounded-2xl overflow-hidden border border-white/10 ${className}`}>
    <div ref={el} className="absolute inset-0" role="application" aria-label="Map of stations and facilities" />
    <div className="absolute bottom-2 left-2 z-[500] flex gap-2 text-[10px]"><span className="bg-black/70 text-amber-300 px-2 py-1 rounded">Sample data may be synthetic</span>
      <span className="bg-black/70 text-zinc-300 px-2 py-1 rounded">◉ station · ▲ facility candidate</span></div>
    {!pins.some(p => isFinite(p.lat) && isFinite(p.lon)) && <div className="absolute inset-0 z-[500] flex items-center justify-center pointer-events-none"><span className="bg-black/70 text-zinc-300 text-xs px-3 py-2 rounded">No station coordinates available from the API yet</span></div>}
  </div>)
}
