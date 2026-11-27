
import { useEffect, useState } from 'react'
import { Bar, Card, ErrorBox, Kpi, Loading } from '../components/ui'
import { useInvestigations } from '../hooks/useInvestigations'
import { statusKey } from '../utils/normalize'

interface ToolMetric {
  tool_name: string
  calls: number
  attempts: number
  successes: number
  failures: number
  retries: number
  total_duration_seconds: number
}

interface McpMetrics {
  total_calls: number
  total_attempts: number
  successful_calls: number
  failed_calls: number
  retries: number
  total_duration_seconds: number
  average_duration_seconds: number
  success_rate: number
  tools: Record<string, ToolMetric>
}

export default function System() {
  const { data, error, loading, reload } = useInvestigations()

  const [metrics, setMetrics] = useState<McpMetrics | null>(null)
  const [metricsError, setMetricsError] = useState<string | null>(null)
  const [metricsLoading, setMetricsLoading] = useState(true)

  const loadMetrics = async () => {
    try {
      setMetricsError(null)

      const response = await fetch('/metrics/mcp')

      if (!response.ok) {
        throw new Error(`MCP metrics API returned ${response.status}`)
      }

      const result: McpMetrics = await response.json()
      setMetrics(result)
    } catch (err) {
      setMetricsError(
        err instanceof Error ? err.message : 'Could not load MCP metrics.'
      )
    } finally {
      setMetricsLoading(false)
    }
  }

  useEffect(() => {
    loadMetrics()
    const interval = window.setInterval(loadMetrics, 15000)

    return () => window.clearInterval(interval)
  }, [])

  if (loading) return <Loading />
  if (error) return <ErrorBox msg={error} retry={reload} />

  const investigations = data ?? []
  const count = (status: string) =>
    investigations.filter(i => statusKey(i.status) === status).length

  const toolEntries = Object.entries(metrics?.tools ?? {})
  const maxCalls = Math.max(
    1,
    ...toolEntries.map(([, tool]) => tool.calls)
  )

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <Kpi label="Running" value={count('running')} />
        <Kpi label="Recovering" value={count('recovering')} accent="text-amber-300" />
        <Kpi label="Failed" value={count('failed')} accent="text-red-300" />
        <Kpi label="Total Investigations" value={investigations.length} />
      </div>

      <Card title="Execution status">
        <div className="space-y-3">
          {['pending', 'running', 'recovering', 'awaiting approval', 'completed', 'failed'].map(status => (
            <Bar
              key={status}
              label={status}
              value={count(status)}
              max={Math.max(1, investigations.length)}
            />
          ))}
        </div>
      </Card>

      <Card title="MCP tool metrics">
        {metricsLoading ? (
          <Loading />
        ) : metricsError ? (
          <ErrorBox msg={metricsError} retry={loadMetrics} />
        ) : metrics ? (
          <div className="space-y-6">
            <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
              <Kpi label="Total Calls" value={metrics.total_calls} />
              <Kpi label="Successful Calls" value={metrics.successful_calls} accent="text-emerald-300" />
              <Kpi label="Failed Calls" value={metrics.failed_calls} accent="text-red-300" />
              <Kpi label="Retries" value={metrics.retries} accent="text-amber-300" />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Kpi
                label="Success Rate"
                value={`${metrics.success_rate.toFixed(1)}%`}
                accent="text-emerald-300"
              />
              <Kpi
                label="Average Attempt Duration"
                value={`${(metrics.average_duration_seconds * 1000).toFixed(2)} ms`}
              />
            </div>

            <div>
              <h3 className="text-sm font-semibold mb-3">
                Tool performance
              </h3>

              {toolEntries.length > 0 ? (
                <div className="space-y-4">
                  {toolEntries.map(([name, tool]) => (
                    <div key={name} className="space-y-2">
                      <Bar
                        label={name}
                        value={tool.calls}
                        max={maxCalls}
                      />

                      <p className="text-xs text-slate-400">
                        {tool.calls} calls · {tool.successes} successful ·{' '}
                        {tool.failures} failed · {tool.retries} retries
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-400">
                  No MCP tool calls recorded yet.
                </p>
              )}
            </div>

            <p className="text-xs text-slate-500">
              Automatically refreshed every 15 seconds.
            </p>
          </div>
        ) : null}
      </Card>
    </div>
  )
}
