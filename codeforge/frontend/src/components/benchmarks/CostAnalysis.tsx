'use client'

import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import type { CostSummary } from '@/lib/types'

const COLORS = ['#6366f1', '#22c55e', '#f97316', '#eab308', '#ec4899', '#14b8a6']

interface CostAnalysisProps {
  data: CostSummary | null
}

export function CostAnalysis({ data }: CostAnalysisProps) {
  if (!data) return <div className="h-64 flex items-center justify-center text-muted-foreground text-sm">No data</div>

  const chartData = Object.entries(data.cost_by_model).map(([name, value]) => ({
    name,
    value: parseFloat((value as number).toFixed(4)),
  }))

  return (
    <div className="space-y-2">
      <div className="text-center">
        <p className="text-2xl font-bold">${data.total_cost_usd.toFixed(4)}</p>
        <p className="text-xs text-muted-foreground">Total cost</p>
      </div>
      <div className="w-full h-48">
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={70}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              label={({ name, percent }: any) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
              labelLine={false}
            >
              {chartData.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: 8 }}
              formatter={(v: number | undefined) => [`$${(v ?? 0).toFixed(4)}`, 'Cost']}
            />
            <Legend wrapperStyle={{ fontSize: 11, color: '#a1a1aa' }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
