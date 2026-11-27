
import { useParams } from 'react-router-dom'
import {
  Badge, Card, Disclaimer, ErrorBox, Json, Kpi, Loading, Missing, Tag
} from '../components/ui'
import { api } from '../services/api'
import { useApi } from '../hooks/useApi'
import MapView, { Pin } from '../components/MapView'
import {
  find, fmtDate, fmtDur, isLive, normalizeInv, show
} from '../utils/normalize'

const POLL = [
  ['PM2.5', 'pm25'],
  ['PM10', 'pm10'],
  ['SO2', 'so2'],
  ['NOx', 'nox'],
] as const

function parseResult(raw: any) {
  const investigation = raw?.investigation ?? raw

  let result = investigation?.result_data

  if (!result && investigation?.result_json) {
    try {
      result = JSON.parse(investigation.result_json)
    } catch {
      result = {}
    }
  }

  return { investigation, result: result ?? {} }
}

export function Facilities({ raw }: { raw: any }) {
  const { result } = parseResult(raw)

  const profiles = result.facility_profiles ?? []
  const recommendations =
    result.investigation_plan?.recommendations ?? []

  if (!profiles.length) {
    return <Missing what="facility profiles in investigation results" />
  }

  const recommendationMap = new Map(
    recommendations.map((r: any) => [r.facility_id, r])
  )

  const rows = profiles.map((profile: any) => ({
    ...profile,
    ...(recommendationMap.get(profile.facility_id) ?? {}),
  }))

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="text-left text-zinc-500">
          <tr>
            <th className="py-3">Facility</th>
            <th>Industry</th>
            <th>Distance</th>
            <th>Wind aligned</th>
            <th>Priority</th>
            <th>Score</th>
          </tr>
        </thead>

        <tbody>
          {rows.map((r: any) => (
            <tr
              key={r.facility_id}
              className="border-t border-white/5"
            >
              <td className="py-3">
                <div className="font-medium text-white">
                  {r.facility_name}
                </div>
                <div className="text-xs text-zinc-500">
                  {r.facility_id}
                </div>
              </td>

              <td>{show(r.industry_type)}</td>
              <td>{show(r.distance_km)} km</td>
              <td>
                {r.is_directionally_aligned ? 'Yes' : 'No'}
              </td>
              <td>{show(r.priority_level)}</td>
              <td className="font-semibold text-amber-300">
                {show(r.priority_score)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <p className="text-xs text-zinc-500 mt-3">
        Scores represent screening priority, not probability of
        responsibility or proof of causation.
      </p>
    </div>
  )
}

export function Interpretation({ raw }: { raw: any }) {
  const { result } = parseResult(raw)

  const interp = result.llm_interpretation
  const validation = result.llm_validation

  if (!interp) {
    return <Missing what="LLM interpretation" />
  }

  return (
    <div className="space-y-4">
      <div className="text-sm">
        Validation:{' '}
        <span className={
          validation?.is_valid
            ? 'text-emerald-400'
            : 'text-amber-400'
        }>
          {validation?.is_valid ? 'Passed' : 'Review required'}
        </span>
      </div>

      {validation?.warnings?.length > 0 && (
        <div className="rounded-lg bg-amber-500/10 border border-amber-500/30 p-3 text-sm text-amber-300">
          <strong>Validation warnings</strong>
          <ul className="list-disc ml-5 mt-2">
            {validation.warnings.map((w: string, i: number) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-4 text-sm">
        {[
          ['Ambient Analysis', interp.ambient_analysis],
          ['Wind Analysis', interp.wind_analysis],
          ['Facility Analysis', interp.facility_analysis],
          ['Limitations', interp.limitations],
          ['Recommendations', interp.recommendations],
        ].map(([heading, content]: any) => (
          <div key={heading}>
            <h4 className="font-medium text-white mb-2">
              {heading}
            </h4>
            {Array.isArray(content) ? (
              <ul className="list-disc ml-5 space-y-1">
                {content.map((item: string, i: number) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            ) : (
              <p className="text-zinc-300">
                {show(content)}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default function Details() {
  const { id = '' } = useParams()

  const {
    data: raw,
    error,
    loading,
    reload
  } = useApi(
    () => api.get(id),
    [id],
    d => d && isLive(String(find(d, ['status']))) ? 3000 : 0
  )

  if (loading) return <Loading />
  if (error) return <ErrorBox msg={error} retry={reload} />

  const { investigation, result } = parseResult(raw)
  const inv = normalizeInv(investigation)

  const exceedances =
    result.exceedance_result?.exceedances ?? []

  const wind = result.wind_reading ?? {}
  const ambient = result.ambient_reading ?? {}

  const profiles = result.facility_profiles ?? []
  const recommendations =
    result.investigation_plan?.recommendations ?? []

  const recommendationMap = new Map(
    recommendations.map((r: any) => [r.facility_id, r])
  )

  // Show every measured pollutant, not just exceedances.
  const pollutants: Record<string, any> = {
    pm25: ambient.pm25,
    pm10: ambient.pm10,
    so2: ambient.so2,
    nox: ambient.nox,
  }

  // Backward compatibility with older saved investigations.
  exceedances.forEach((e: any) => {
    const key = String(e.pollutant)
      .toLowerCase()
      .replace(/[^a-z0-9]/g, '')

    if (pollutants[key] == null) {
      pollutants[key] = e.measured_value
    }
  })

  const pins: Pin[] = [
    {
      lat: Number(investigation.station_latitude),
      lon: Number(investigation.station_longitude),
      kind: 'station',
      label: `Station ${investigation.station_id}`,
      popup: 'Ambient air quality monitoring station',
    },

    ...profiles.map((f: any) => {
      const recommendation: any =
        recommendationMap.get(f.facility_id) ?? {}

      return {
        lat: Number(f.location?.latitude),
        lon: Number(f.location?.longitude),
        kind: 'facility' as const,
        label: f.facility_name,
        popup: `Distance: ${recommendation.distance_km ?? '—'} km<br/>Priority: ${recommendation.priority_level ?? '—'}<br/>Score: ${recommendation.priority_score ?? '—'}`,
      }
    }),
  ]

  const validPins = pins.filter(
    p => Number.isFinite(p.lat) && Number.isFinite(p.lon)
  )

  return (
    <div className="space-y-6">

      <div className="flex items-center gap-3">
        <h1 className="text-xl font-semibold text-white">
          Investigation {inv.id}
        </h1>

        <Badge status={inv.status} />

        {isLive(inv.status) && (
          <span className="text-xs text-zinc-500 animate-pulse">
            Auto-refreshing
          </span>
        )}
      </div>

      <Disclaimer />

      <Card
        title="Monitoring Station & Industrial Facilities"
        right={<Tag tone="amber">Synthetic demo locations</Tag>}
      >
        <MapView pins={validPins} className="h-[380px]" />

        <div className="flex flex-wrap gap-4 text-xs text-zinc-400 mt-3">
          <span>◉ Monitoring station</span>
          <span>▲ Factory candidates ({profiles.length})</span>
        </div>
      </Card>

      <Card
        title="A. Investigation Overview"
        right={<Tag tone="teal">Deterministic Python</Tag>}
      >
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Kpi label="Station" value={inv.stationId} />
          <Kpi label="Stage" value={inv.stage} />
          <Kpi
            label="Created"
            value={
              <span className="text-base">
                {fmtDate(inv.createdAt)}
              </span>
            }
          />
          <Kpi label="Duration" value={fmtDur(inv.durationSec)} />
        </div>
      </Card>

      <Card
        title="B. Ambient Air Quality Evidence"
        right={<Tag tone="sky">Retrieved measurements</Tag>}
      >
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {POLL.map(([label, key]) => {
            const value = pollutants[key]

            return (
              <Kpi
                key={label}
                label={label}
                value={
                  value != null
                    ? show(value)
                    : 'Not available'
                }
              />
            )
          })}
        </div>

        <p className="text-xs text-zinc-400 mt-3">
          All available ambient measurements are displayed, including
          pollutants below the configured demonstration thresholds.
          Missing measurements are not treated as zero.
          Thresholds are synthetic, not official regulatory standards.
        </p>
      </Card>

      <Card
        title="C. Wind Analysis"
        right={<Tag tone="sky">Retrieved data</Tag>}
      >
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Kpi label="Wind speed" value={show(wind.wind_speed)} />
          <Kpi label="Wind direction" value={
            wind.wind_direction != null
              ? `${show(wind.wind_direction)}°`
              : 'Not available'
          } />
          <Kpi label="Station latitude" value={show(investigation.station_latitude)} />
          <Kpi label="Station longitude" value={show(investigation.station_longitude)} />
        </div>
        <p className="text-xs text-zinc-500 mt-3">
          Wind speed units are not specified in the source data.
        </p>
      </Card>

      <Card
        title={`D. Facility Screening Candidates (${profiles.length})`}
        right={<Tag tone="amber">Heuristic screening</Tag>}
      >
        <Facilities raw={raw} />
      </Card>

      <Card
        title="E. AI Interpretation & Validation"
        right={<Tag tone="violet">LLM-generated · not independently verified</Tag>}
      >
        <Interpretation raw={raw} />
      </Card>

      <Card
        title="F. Evidence, Methodology & Timeline"
        right={<Tag>Synthetic demo data</Tag>}
      >
        <div className="text-sm space-y-3">
          <div>
            Data source: {show(result.data_source)}
          </div>

          <div>
            Investigation timestamp: {show(result.investigation_timestamp)}
          </div>

          <div>
            Exceedance count: {show(result.exceedance_result?.exceedance_count)}
          </div>

          <div>
            MCP tool metrics:
            <Json data={result.mcp_metrics} />
          </div>

          <div>
            Validation:
            <Json data={result.llm_validation} />
          </div>
        </div>
      </Card>

      <Card
        title="G. Human Decision"
        right={<Tag tone="teal">Human review</Tag>}
      >
        <div className="text-sm">
          Status: <Badge status={inv.status} />
        </div>

        <p className="text-xs text-zinc-400 mt-2">
          Decisions are made only in the Approval Center.
          Screening results do not establish legal responsibility.
        </p>
      </Card>

    </div>
  )
}
