'use client'

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { ModelDistribution as ModelDistributionType } from '@/lib/types'

interface ModelDistributionProps {
  data: ModelDistributionType | null
}

export function ModelDistribution({ data }: ModelDistributionProps) {
  if (!data || data.distribution.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">
        No model data
      </div>
    )
  }

  const chartData = data.distribution.map((d) => ({
    name: d.model,
    percentage: parseFloat(d.percentage.toFixed(1)),
    count: d.count,
  }))

  return (
    <div className="w-full h-48">
      <ResponsiveContainer>
        <BarChart
          layout="vertical"
          data={chartData}
          margin={{ top: 0, right: 20, left: 10, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" horizontal={false} />
          <XAxis type="number" domain={[0, 100]} unit="%" tick={{ fill: '#a1a1aa', fontSize: 11 }} />
          <YAxis type="category" dataKey="name" tick={{ fill: '#a1a1aa', fontSize: 11 }} width={80} />
          <Tooltip
            contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: 8 }}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={(v: any, _: any, entry: any) => [
              `${v ?? 0}% (${entry.payload.count} tasks)`,
              'Usage',
            ]}
          />
          <Bar dataKey="percentage" fill="#6366f1" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
