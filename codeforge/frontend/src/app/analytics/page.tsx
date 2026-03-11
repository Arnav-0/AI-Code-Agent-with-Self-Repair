'use client'

import { useEffect, useState } from 'react'
import { getSelfRepairSummary, getPerformanceSummary, getCostSummary } from '@/lib/api'
import {
  Wrench, Shield, Zap, TrendingUp, AlertTriangle,
  CheckCircle2, XCircle, BarChart3, Loader2, Bug,
  ArrowUpRight, Gauge,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { SelfRepairSummary, PerformanceSummary, CostSummary } from '@/lib/types'

function MetricRing({ value, label, color, size = 100 }: {
  value: number; label: string; color: string; size?: number
}) {
  const radius = (size - 12) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (value / 100) * circumference

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke="currentColor" strokeWidth="6"
            className="text-muted/30"
          />
          <circle cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke={color} strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-lg font-bold tabular-nums">{value.toFixed(1)}%</span>
        </div>
      </div>
      <span className="text-[11px] text-muted-foreground font-medium">{label}</span>
    </div>
  )
}

function ComplexityTable({ data }: { data: SelfRepairSummary['complexity_breakdown'] }) {
  if (data.length === 0) return <p className="text-xs text-muted-foreground">No data yet</p>

  const complexityColor: Record<string, string> = {
    simple: 'text-emerald-400',
    medium: 'text-yellow-400',
    hard: 'text-red-400',
    unknown: 'text-muted-foreground',
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-border/30">
            <th className="text-left py-2 px-2 text-muted-foreground font-medium">Complexity</th>
            <th className="text-right py-2 px-2 text-muted-foreground font-medium">Total</th>
            <th className="text-right py-2 px-2 text-muted-foreground font-medium">Passed</th>
            <th className="text-right py-2 px-2 text-muted-foreground font-medium">Repaired</th>
            <th className="text-right py-2 px-2 text-muted-foreground font-medium">Failed</th>
            <th className="text-right py-2 px-2 text-muted-foreground font-medium">Avg Retries</th>
            <th className="text-right py-2 px-2 text-muted-foreground font-medium">Avg Cost</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={row.complexity} className="border-b border-border/10 hover:bg-accent/20 transition-colors">
              <td className={cn('py-2.5 px-2 font-semibold capitalize', complexityColor[row.complexity] || 'text-foreground')}>
                {row.complexity}
              </td>
              <td className="text-right py-2.5 px-2 tabular-nums">{row.total}</td>
              <td className="text-right py-2.5 px-2 tabular-nums text-emerald-400">{row.succeeded}</td>
              <td className="text-right py-2.5 px-2 tabular-nums text-orange-400">{row.repaired}</td>
              <td className="text-right py-2.5 px-2 tabular-nums text-red-400">{row.failed}</td>
              <td className="text-right py-2.5 px-2 tabular-nums">{row.avg_retries}</td>
              <td className="text-right py-2.5 px-2 tabular-nums">${row.avg_cost_usd.toFixed(4)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ErrorPatternsChart({ data }: { data: SelfRepairSummary['error_patterns'] }) {
  if (data.length === 0) return <p className="text-xs text-muted-foreground">No error data yet</p>
  const maxCount = Math.max(...data.map(d => d.count))

  return (
    <div className="space-y-2">
      {data.map((err, i) => (
        <div key={i} className="group">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] font-mono text-foreground truncate max-w-[70%]" title={err.error_type}>
              {err.error_type}
            </span>
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-muted-foreground tabular-nums">{err.count}x</span>
              <span className={cn(
                'text-[10px] font-medium tabular-nums',
                err.repair_success_rate >= 0.8 ? 'text-emerald-400' :
                err.repair_success_rate >= 0.5 ? 'text-yellow-400' : 'text-red-400'
              )}>
                {(err.repair_success_rate * 100).toFixed(0)}% fixed
              </span>
            </div>
          </div>
          <div className="h-2 rounded-full bg-muted/30 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${(err.count / maxCount) * 100}%`,
                background: `linear-gradient(90deg, ${err.repair_success_rate >= 0.8 ? '#10b981' : err.repair_success_rate >= 0.5 ? '#eab308' : '#ef4444'}80, ${err.repair_success_rate >= 0.8 ? '#10b981' : err.repair_success_rate >= 0.5 ? '#eab308' : '#ef4444'}40)`,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

function DailyRepairChart({ data }: { data: { date: string; cost: number }[] }) {
  if (data.length === 0) return <p className="text-xs text-muted-foreground text-center py-4">No data yet</p>
  const maxVal = Math.max(...data.map(d => d.cost), 1)
  return (
    <div className="flex items-end gap-1 h-24 px-1">
      {data.slice(-14).map((d, i) => {
        const height = Math.max((d.cost / maxVal) * 100, 4)
        return (
          <div key={i} className="flex-1 flex flex-col items-center gap-1 group" title={`${d.date}: ${d.cost}% repaired`}>
            <span className="text-[8px] text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity tabular-nums">
              {d.cost}%
            </span>
            <div
              className="w-full rounded-t transition-all group-hover:opacity-100"
              style={{
                height: `${height}%`,
                background: `linear-gradient(to top, #f97316cc, #eab308cc)`,
              }}
            />
            <span className="text-[8px] text-muted-foreground tabular-nums">{d.date.slice(5)}</span>
          </div>
        )
      })}
    </div>
  )
}

export default function AnalyticsPage() {
  const [repair, setRepair] = useState<SelfRepairSummary | null>(null)
  const [perf, setPerf] = useState<PerformanceSummary | null>(null)
  const [cost, setCost] = useState<CostSummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getSelfRepairSummary().catch(() => null),
      getPerformanceSummary().catch(() => null),
      getCostSummary().catch(() => null),
    ]).then(([r, p, c]) => {
      if (r) setRepair(r)
      if (p) setPerf(p)
      if (c) setCost(c)
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full gap-3">
        <Loader2 className="w-5 h-5 animate-spin text-primary" />
        <span className="text-sm text-muted-foreground">Loading self-repair analytics...</span>
      </div>
    )
  }

  const totalTasks = repair?.total_tasks ?? 0
  const successRate = perf ? perf.success_rate * 100 : 0
  const repairRate = repair ? repair.repair_success_rate * 100 : 0
  const firstTryRate = repair ? repair.first_try_success_rate * 100 : 0
  const overallEffective = firstTryRate + (100 - firstTryRate) * (repairRate / 100)

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-red-500 shadow-lg shadow-orange-500/20">
          <Wrench className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-xl font-bold tracking-tight">Self-Repair Analytics</h1>
          <p className="text-xs text-muted-foreground">
            How effectively the AI debugs its own code failures
          </p>
        </div>
      </div>

      {/* Hero metrics — the three rings */}
      <div className="rounded-2xl border border-border/20 bg-card/30 backdrop-blur-md p-6 card-futuristic">
        <div className="flex items-center gap-2 mb-5">
          <Gauge className="w-4 h-4 text-primary" />
          <h2 className="text-sm font-semibold">Key Metrics</h2>
          <span className="text-[10px] text-muted-foreground ml-1">last 30 days</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 place-items-center">
          <MetricRing value={firstTryRate} label="First-Try Success" color="#10b981" />
          <MetricRing value={repairRate} label="Repair Success" color="#f97316" />
          <MetricRing value={overallEffective} label="Effective Success" color="#8b5cf6" />
          <MetricRing value={successRate} label="Overall Pass Rate" color="#3b82f6" />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6">
          <div className="flex items-center gap-2 p-2.5 rounded-xl bg-background/50 border border-border/20">
            <Zap className="w-3.5 h-3.5 text-blue-400 shrink-0" />
            <div>
              <p className="text-sm font-bold tabular-nums">{totalTasks}</p>
              <p className="text-[10px] text-muted-foreground">Total Tasks</p>
            </div>
          </div>
          <div className="flex items-center gap-2 p-2.5 rounded-xl bg-background/50 border border-border/20">
            <Wrench className="w-3.5 h-3.5 text-orange-400 shrink-0" />
            <div>
              <p className="text-sm font-bold tabular-nums">{repair?.tasks_with_retries ?? 0}</p>
              <p className="text-[10px] text-muted-foreground">Needed Repair</p>
            </div>
          </div>
          <div className="flex items-center gap-2 p-2.5 rounded-xl bg-background/50 border border-border/20">
            <ArrowUpRight className="w-3.5 h-3.5 text-yellow-400 shrink-0" />
            <div>
              <p className="text-sm font-bold tabular-nums">{repair?.avg_retries_when_repairing?.toFixed(1) ?? '0'}</p>
              <p className="text-[10px] text-muted-foreground">Avg Retries/Repair</p>
            </div>
          </div>
          <div className="flex items-center gap-2 p-2.5 rounded-xl bg-background/50 border border-border/20">
            <Shield className="w-3.5 h-3.5 text-purple-400 shrink-0" />
            <div>
              <p className="text-sm font-bold tabular-nums">${repair?.total_repair_cost_usd?.toFixed(4) ?? '0'}</p>
              <p className="text-[10px] text-muted-foreground">Repair Cost</p>
            </div>
          </div>
        </div>
      </div>

      {/* Two-column: Complexity + Error Patterns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Complexity Breakdown */}
        <div className="rounded-2xl border border-border/20 bg-card/30 backdrop-blur-md p-4 card-futuristic">
          <div className="flex items-center gap-2 mb-3">
            <BarChart3 className="w-4 h-4 text-blue-400" />
            <h3 className="text-sm font-semibold">Performance by Complexity</h3>
          </div>
          <ComplexityTable data={repair?.complexity_breakdown ?? []} />
        </div>

        {/* Error Patterns */}
        <div className="rounded-2xl border border-border/20 bg-card/30 backdrop-blur-md p-4 card-futuristic">
          <div className="flex items-center gap-2 mb-3">
            <Bug className="w-4 h-4 text-red-400" />
            <h3 className="text-sm font-semibold">Error Patterns & Fix Rate</h3>
          </div>
          <ErrorPatternsChart data={repair?.error_patterns ?? []} />
        </div>
      </div>

      {/* Daily repair rate chart */}
      <div className="rounded-2xl border border-border/20 bg-card/30 backdrop-blur-md p-4 card-futuristic">
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp className="w-4 h-4 text-orange-400" />
          <h3 className="text-sm font-semibold">Daily Repair Rate</h3>
          <span className="text-[10px] text-muted-foreground ml-1">% of tasks needing repair per day</span>
        </div>
        <DailyRepairChart data={repair?.daily_repair_rate ?? []} />
      </div>

      {/* Insights panel */}
      {repair && totalTasks > 0 && (
        <div className="rounded-2xl border border-border/20 bg-card/30 backdrop-blur-md p-4 card-futuristic">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-semibold">Insights</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {repairRate >= 80 && (
              <div className="flex items-start gap-2 p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <p className="text-[11px] text-emerald-300/80">
                  Self-repair is highly effective at {repairRate.toFixed(0)}%. The AI successfully debugs most failures.
                </p>
              </div>
            )}
            {repairRate < 50 && repairRate > 0 && (
              <div className="flex items-start gap-2 p-3 rounded-xl bg-red-500/5 border border-red-500/20">
                <XCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                <p className="text-[11px] text-red-300/80">
                  Repair success is low at {repairRate.toFixed(0)}%. Consider increasing max retries or using a stronger model.
                </p>
              </div>
            )}
            {repair.max_retries_seen >= 3 && (
              <div className="flex items-start gap-2 p-3 rounded-xl bg-amber-500/5 border border-amber-500/20">
                <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <p className="text-[11px] text-amber-300/80">
                  Some tasks required {repair.max_retries_seen} retries. Model escalation may help for complex errors.
                </p>
              </div>
            )}
            {firstTryRate >= 70 && (
              <div className="flex items-start gap-2 p-3 rounded-xl bg-blue-500/5 border border-blue-500/20">
                <Zap className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                <p className="text-[11px] text-blue-300/80">
                  {firstTryRate.toFixed(0)}% of tasks pass on the first try. Code generation quality is strong.
                </p>
              </div>
            )}
            {repair.total_repair_cost_usd > 0 && (
              <div className="flex items-start gap-2 p-3 rounded-xl bg-purple-500/5 border border-purple-500/20">
                <Shield className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                <p className="text-[11px] text-purple-300/80">
                  Self-repair cost: ${repair.total_repair_cost_usd.toFixed(4)} — {((repair.total_repair_cost_usd / (cost?.total_cost_usd || repair.total_repair_cost_usd || 1)) * 100).toFixed(1)}% of total spend.
                </p>
              </div>
            )}
            {overallEffective >= 90 && (
              <div className="flex items-start gap-2 p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
                <TrendingUp className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <p className="text-[11px] text-emerald-300/80">
                  Effective success rate is {overallEffective.toFixed(1)}% — combining first-try passes with successful repairs.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
