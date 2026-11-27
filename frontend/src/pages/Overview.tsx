
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import MapView, { Pin } from '../components/MapView'
import {
  Badge, Card, Disclaimer, Empty, ErrorBox, Kpi, Loading,
  Missing, Tag, statusHex
} from '../components/ui'
import { useInvestigations } from '../hooks/useInvestigations'
import { api } from '../services/api'
import { fmtDate, show, statusKey } from '../utils/normalize'

function getResult(detail: any) {
  const investigation = detail?.investigation ?? detail

  if (investigation?.result_data) {
    return investigation.result_data
  }

  try {
    return JSON.parse(investigation?.result_json ?? '{}')
  } catch {
    return {}
  }
}

export default function Overview() {
  const { data, error, loading, reload } = useInvestigations()

  const [q, setQ] = useState('')
  const [st, setSt] = useState('')
  const [detail, setDetail] = useState<any>(null)
  const [detailError, setDetailError] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)

  const list = data ?? []
  const latest = list[0]

  // Fetch full investigation results separately from the summary list.
  useEffect(() => {
    if (!latest?.id) {
      setDetail(null)
      return
    }

    let active = true

    setDetail(null)
    setDetailError('')

    api.get(latest.id)
      .then(response => {
        if (active) setDetail(response)
      })
      .catch(err => {
        if (active) {
          setDetailError(err.message ?? 'Could not load investigation details')
        }
      })

    return () => {
      active = false
    }
  }, [latest?.id, refreshKey])

  const result = useMemo(() => getResult(detail), [detail])

  const profiles = result?.facility_profiles ?? []
  const recommendations = result?.investigation_plan?.recommendations ?? []

  const recommendationMap = new Map(
    recommendations.map((r: any) => [r.facility_id, r])
  )

  // Display the latest station and all facility locations.
  const pins: Pin[] = useMemo(() => {
    if (!latest) return []

    const detailInvestigation = detail?.investigation ?? detail

    const stationLat = Number(
      detailInvestigation?.station_latitude ?? latest.lat
    )
    const stationLon = Number(
      detailInvestigation?.station_longitude ?? latest.lon
    )

    const station: Pin[] =
      Number.isFinite(stationLat) && Number.isFinite(stationLon)
        ? [{
            lat: stationLat,
            lon: stationLon,
            kind: 'station',
            label: `Station ${latest.stationId}`,
            color: statusHex[statusKey(latest.status)],
            popup: `Investigation ${latest.id}`,
          }]
        : []

    const facilities: Pin[] = profiles
      .filter((f: any) =>
        Number.isFinite(Number(f.location?.latitude)) &&
        Number.isFinite(Number(f.location?.longitude))
      )
      .map((f: any) => {
        const recommendation: any =
          recommendationMap.get(f.facility_id) ?? {}

        return {
          lat: Number(f.location.latitude),
          lon: Number(f.location.longitude),
          kind: 'facility' as const,
          label: f.facility_name,
          popup: `Distance: ${recommendation.distance_km ?? '—'} km<br/>Priority: ${recommendation.priority_level ?? '—'}<br/>Score: ${recommendation.priority_score ?? '—'}`,
        }
      })

    return [...station, ...facilities]
  }, [latest, detail, profiles.length, recommendations.length])

  if (loading) return <Loading />
  if (error) return <ErrorBox msg={error} retry={reload} />

  const c = (...s: string[]) =>
    list.filter(i => s.includes(statusKey(i.status))).length

  const dist: Record<string, number> = {}

  list.forEach(i => {
    const k = statusKey(i.status)
    dist[k] = (dist[k] ?? 0) + 1
  })

  let acc = 0
  const total = Math.max(1, list.length)

  const grad = Object.entries(dist)
    .map(([k, v]) => {
      const a = acc
      acc += (v / total) * 100
      return `${statusHex[k] ?? '#52525b'} ${a}% ${acc}%`
    })
    .join(',')

  const exceedances =
    result?.exceedance_result?.exceedances ?? []

  // Start with the complete ambient reading.
  // Fall back to exceedance values for older investigations.
  const ambient = result?.ambient_reading ?? {}

  const pollutants: Record<string, any> = {
    pm25: ambient.pm25,
    pm10: ambient.pm10,
    so2: ambient.so2,
    nox: ambient.nox,
  }

  exceedances.forEach((e: any) => {
    const key = String(e.pollutant)
      .toLowerCase()
      .replace(/[^a-z0-9]/g, '')

    if (pollutants[key] == null) {
      pollutants[key] = e.measured_value
    }
  })

  const exc = result?.exceedance_result?.exceedance_count ?? 0

  const adv: [string, string, string][] = []

  if (c('awaiting approval')) {
    adv.push([
      'amber',
      `${c('awaiting approval')} investigation(s) require human review`,
      '/approvals'
    ])
  }

  if (exc) {
    adv.push([
      'rose',
      `Potential exceedance flagged in latest investigation`,
      '/investigations'
    ])
  }

  if (c('running', 'pending', 'recovering')) {
    adv.push([
      'sky',
      `${c('running', 'pending', 'recovering')} investigation(s) in progress — evidence incomplete`,
      '/investigations'
    ])
  }

  if (c('failed')) {
    adv.push([
      'rose',
      `${c('failed')} investigation(s) failed — inspect details`,
      '/investigations'
    ])
  }

  if (c('completed', 'approved')) {
    adv.push([
      'teal',
      `${c('completed', 'approved')} investigation(s) completed`,
      '/investigations'
    ])
  }

  const tone: any = {
    amber: 'text-amber-300',
    rose: 'text-rose-300',
    sky: 'text-sky-300',
    teal: 'text-teal-300'
  }

  const rows = list.filter(i =>
    (!st || statusKey(i.status) === st) &&
    `${i.id} ${i.stationId}`.toLowerCase().includes(q.toLowerCase())
  )

  const env = [
    ['PM2.5', 'pm25'],
    ['PM10', 'pm10'],
    ['SO2', 'so2'],
    ['NOx', 'nox']
  ] as const

  return (
    <div className="grid grid-cols-12 gap-5">

      <Card
        title="Monitoring Station & Industrial Facilities"
        className="col-span-12 xl:col-span-8"
        right={
          <button
            onClick={() => {
              reload()
              setRefreshKey(v => v + 1)
            }}
            className="text-xs text-zinc-400 hover:text-white"
          >
            Refresh ↻
          </button>
        }
      >
        <MapView pins={pins} className="h-[400px]" />

        <div className="flex flex-wrap gap-4 text-xs text-zinc-400 mt-3">
          <span>◉ Monitoring station</span>
          <span>▲ Industrial facility</span>
          <span>{profiles.length} facilities retrieved</span>
        </div>

        {detailError && (
          <p className="text-xs text-rose-400 mt-2">
            Could not load facility details: {detailError}
          </p>
        )}

        {!detail && !detailError && latest && (
          <p className="text-xs text-zinc-500 mt-2">
            Loading detailed facility locations...
          </p>
        )}

        {!latest && (
          <p className="text-xs text-zinc-500 mt-2">
            Start an investigation to display station and factory locations.
          </p>
        )}
      </Card>

      <Card
        title="Investigation Advisory"
        className="col-span-12 xl:col-span-4"
      >
        {!adv.length
          ? <Empty text="No investigations yet. Start one to see advisories." />
          : (
            <ul className="space-y-3 text-sm">
              {adv.map(([t, m, to], i) => (
                <li key={i}>
                  <Link to={to} className={`${tone[t]} hover:underline`}>
                    ● {m}
                  </Link>
                </li>
              ))}
            </ul>
          )}

        <p className="text-[11px] text-zinc-500 mt-4">
          Derived from investigation state. Not a verified health or compliance assessment.
        </p>
      </Card>

      <Card
        title="Environmental Data"
        className="col-span-12 md:col-span-7 xl:col-span-5"
        right={<Tag tone="amber">Latest · synthetic demo</Tag>}
      >
        <div className="grid grid-cols-4 gap-2 text-center">
          {env.map(([label, key]) => {
            const value = pollutants[key]

            return (
              <div key={label}>
                <div className="text-lg font-semibold text-white">
                  {value == null
                    ? <span className="text-sm text-zinc-500">N/A</span>
                    : show(value)}
                </div>
                <div className="text-xs text-zinc-500">{label}</div>
              </div>
            )
          })}
        </div>

        <p className="text-[11px] text-zinc-500 mt-3">
          {detail
            ? `Investigation ${latest?.id}. Displays all available ambient measurements, including values below exceedance thresholds.`
            : 'Waiting for detailed investigation data.'}
        </p>
      </Card>

      <Card
        title="Investigation Status"
        className="col-span-12 md:col-span-5 xl:col-span-4"
      >
        {!list.length
          ? <Empty text="No data" />
          : (
            <div className="flex items-center gap-5">
              <div
                className="w-28 h-28 rounded-full shrink-0 grid place-items-center"
                style={{ background: `conic-gradient(${grad})` }}
              >
                <div className="w-20 h-20 rounded-full bg-panel grid place-items-center text-xl font-semibold">
                  {list.length}
                </div>
              </div>

              <ul className="text-xs space-y-1.5">
                {Object.entries(dist).map(([k, v]) => (
                  <li key={k} className="capitalize flex items-center gap-2">
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{ background: statusHex[k] ?? '#52525b' }}
                    />
                    {k} · {v}
                  </li>
                ))}
              </ul>
            </div>
          )}
      </Card>

      <Card title="Summary" className="col-span-12 xl:col-span-3">
        <div className="grid grid-cols-2 gap-2">
          <Kpi label="Total" value={list.length} />
          <Kpi label="Active" value={c('pending', 'running', 'recovering')} accent="text-sky-300" />
          <Kpi label="Awaiting" value={c('awaiting approval')} accent="text-amber-300" />
          <Kpi label="Approved" value={c('approved')} accent="text-emerald-300" />
        </div>

        <p className="text-[11px] text-zinc-500 mt-2">
          Latest exceedances: {exc}
        </p>
      </Card>

      <Card
        title="Recent Investigations"
        className="col-span-12 xl:col-span-8"
        right={
          <div className="flex gap-2">
            <input
              aria-label="Search"
              value={q}
              onChange={e => setQ(e.target.value)}
              placeholder="Search…"
              className="rounded-lg px-3 py-1.5 text-xs w-32"
            />

            <select
              aria-label="Status filter"
              value={st}
              onChange={e => setSt(e.target.value)}
              className="rounded-lg px-2 py-1.5 text-xs"
            >
              <option value="">All</option>
              {Object.keys(dist).map(s => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </div>
        }
      >
        {!rows.length
          ? <Empty text="No investigations match." />
          : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-zinc-500 text-xs">
                  <tr>
                    <th className="py-2 font-normal">ID</th>
                    <th className="font-normal">Station</th>
                    <th className="font-normal">Status</th>
                    <th className="font-normal">Stage</th>
                    <th className="font-normal">Created</th>
                    <th />
                  </tr>
                </thead>

                <tbody>
                  {rows.slice(0, 8).map(i => (
                    <tr
                      key={i.id}
                      className="border-t border-white/5 hover:bg-white/5"
                    >
                      <td className="py-2 font-medium">{i.id}</td>
                      <td>{i.stationId}</td>
                      <td><Badge status={i.status} /></td>
                      <td className="text-zinc-400">{i.stage}</td>
                      <td className="text-zinc-500">{fmtDate(i.createdAt)}</td>
                      <td>
                        <Link
                          className="text-teal-300"
                          to={`/investigations/${i.id}`}
                        >
                          View →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </Card>

      <Card title="Workflow Activity" className="col-span-12 xl:col-span-4">
        <div className="space-y-2 text-sm">
          {['pending', 'running', 'recovering', 'awaiting approval', 'failed'].map(s => (
            <div
              key={s}
              className="flex justify-between capitalize text-zinc-400"
            >
              <span>{s}</span>
              <span className="text-zinc-100">{c(s)}</span>
            </div>
          ))}
        </div>

        <div className="mt-3">
          <Missing what="detailed MCP tool metrics (calls, retries, durations)" />
        </div>
      </Card>

      <div className="col-span-12">
        <Disclaimer />
      </div>

    </div>
  )
}
