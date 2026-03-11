'use client'

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import type { BenchmarkRun } from '@/lib/types'

const TYPE_COLORS: Record<string, string> = {
  humaneval: '#6366f1',
  mbpp: '#22c55e',
  custom: '#f97316',
}

interface HistoricalTrendProps {
  runs: BenchmarkRun[]
}

export function HistoricalTrend({ runs }: HistoricalTrendProps) {
  const types = [...new Set(runs.map((r) => r.benchmark_type))]

  // Group by date and type
  const byDate: Record<string, Record<string, number>> = {}
  for (const run of runs) {
    const date = run.created_at.slice(0, 10)
    if (!byDate[date]) byDate[date] = {}
    byDate[date][run.benchmark_type] = run.pass_at_1 * 100
  }

  const data = Object.entries(byDate)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, vals]) => ({ date, ...vals }))

  if (data.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">
        No historical data
      </div>
    )
  }

  return (
    <div className="w-full h-48">
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis dataKey="date" tick={{ fill: '#a1a1aa', fontSize: 10 }} />
          <YAxis domain={[0, 100]} unit="%" tick={{ fill: '#a1a1aa', fontSize: 11 }} />
          <Tooltip
            contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: 8 }}
            formatter={(v: number | undefined) => [`${(v ?? 0).toFixed(1)}%`]}
          />
          <Legend wrapperStyle={{ fontSize: 12, color: '#a1a1aa' }} />
          {types.map((t) => (
            <Line
              key={t}
              type="monotone"
              dataKey={t}
              stroke={TYPE_COLORS[t] ?? '#71717a'}
              strokeWidth={2}
              dot={{ r: 3 }}
              name={t.charAt(0).toUpperCase() + t.slice(1)}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
