'use client'

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import type { BenchmarkRun } from '@/lib/types'

interface PassRateChartProps {
  runs: BenchmarkRun[]
}

export function PassRateChart({ runs }: PassRateChartProps) {
  const byType: Record<string, { baseline: number; withRepair: number }> = {}

  for (const run of runs) {
    const t = run.benchmark_type
    if (!byType[t]) byType[t] = { baseline: 0, withRepair: 0 }
    byType[t].baseline = Math.max(byType[t].baseline, run.pass_at_1 * 100)
    if (run.pass_at_1_repair != null) {
      byType[t].withRepair = Math.max(byType[t].withRepair, run.pass_at_1_repair * 100)
    }
  }

  const data = Object.entries(byType).map(([name, v]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    Baseline: parseFloat(v.baseline.toFixed(1)),
    'With Repair': parseFloat(v.withRepair.toFixed(1)),
  }))

  return (
    <div className="w-full h-64">
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis dataKey="name" tick={{ fill: '#a1a1aa', fontSize: 12 }} />
          <YAxis domain={[0, 100]} tick={{ fill: '#a1a1aa', fontSize: 12 }} unit="%" />
          <Tooltip
            contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: 8 }}
            labelStyle={{ color: '#f4f4f5' }}
          />
          <Legend wrapperStyle={{ fontSize: 12, color: '#a1a1aa' }} />
          <Bar dataKey="Baseline" fill="#6366f1" radius={[4, 4, 0, 0]} />
          <Bar dataKey="With Repair" fill="#22c55e" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
