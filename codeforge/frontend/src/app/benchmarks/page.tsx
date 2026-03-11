'use client'

import { useEffect, useState } from 'react'
import { useBenchmarks } from '@/hooks/useBenchmarks'
import { getCostSummary, getPerformanceSummary, getModelDistribution, getHistory } from '@/lib/api'
import { CostAnalysis } from '@/components/benchmarks/CostAnalysis'
import { ModelDistribution } from '@/components/benchmarks/ModelDistribution'
import { StatusBadge } from '@/components/agents/StatusBadge'
import { Button } from '@/components/ui/button'
import {
  BarChart3,
  Play,
  TrendingUp,
  Clock,
  DollarSign,
  Activity,
  Target,
  Wrench,
  Hash,
  Loader2,
  Cpu,
  Zap,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { CostSummary, PerformanceSummary, ModelDistribution as ModelDistributionType, Task } from '@/lib/types'

function StatCard({
  label, value, subtitle, icon: Icon, gradient, trend,
}: {
  label: string; value: string; subtitle?: string
  icon: React.ComponentType<{ className?: string }>
  gradient: string; trend?: string
}) {
  return (
    <div className="rounded-2xl border border-border/20 bg-card/30 backdrop-blur-md p-4 space-y-3 hover:border-primary/15 transition-all card-futuristic">
      <div className="flex items-center justify-between">
        <div className={cn('flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br shadow-md', gradient)}>
          <Icon className="h-4 w-4 text-white" />
        </div>
        {trend && (
          <span className="text-[11px] font-medium text-emerald-400 flex items-center gap-0.5">
            <TrendingUp className="w-3 h-3" />{trend}
          </span>
        )}
      </div>
      <div>
        <p className="text-2xl font-bold tracking-tight tabular-nums">{value}</p>
        <p className="text-[11px] text-muted-foreground mt-0.5">{label}</p>
        {subtitle && <p className="text-[10px] text-muted-foreground/60 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  )
}

function DailyCostChart({ data }: { data: { date: string; cost: number }[] }) {
  if (data.length === 0) return <div className="h-28 flex items-center justify-center text-muted-foreground text-xs">No cost data yet</div>
  const maxCost = Math.max(...data.map(d => d.cost), 0.0001)
  return (
    <div className="flex items-end gap-1 h-28 px-1">
      {data.slice(-14).map((d, i) => {
        const height = Math.max((d.cost / maxCost) * 100, 4)
        return (
          <div key={i} className="flex-1 flex flex-col items-center gap-1 group" title={`${d.date}: $${d.cost.toFixed(4)}`}>
            <span className="text-[8px] text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity tabular-nums">
              ${d.cost.toFixed(3)}
            </span>
            <div
              className="w-full bg-gradient-to-t from-primary/80 to-purple-400/80 rounded-t transition-all group-hover:from-primary group-hover:to-purple-400"
              style={{ height: `${height}%` }}
            />
            <span className="text-[8px] text-muted-foreground tabular-nums">{d.date.slice(5)}</span>
          </div>
        )
      })}
    </div>
  )
}

function StatusPills({ data }: { data: Record<string, number> }) {
  const colors: Record<string, string> = {
    completed: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
    failed: 'bg-red-500/10 border-red-500/20 text-red-400',
    cancelled: 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400',
    pending: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
    awaiting_approval: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
    executing: 'bg-purple-500/10 border-purple-500/20 text-purple-400',
    coding: 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400',
    reviewing: 'bg-orange-500/10 border-orange-500/20 text-orange-400',
  }
  return (
    <div className="flex gap-2 flex-wrap">
      {Object.entries(data).sort(([,a],[,b]) => b - a).map(([status, count]) => (
        <div key={status} className={cn('rounded-lg px-3 py-1.5 text-xs font-medium border', colors[status] || 'bg-muted/50 border-border/30 text-muted-foreground')}>
          <span className="capitalize">{status}</span>
          <span className="ml-1.5 font-bold">{count}</span>
        </div>
      ))}
    </div>
  )
}

export default function DashboardPage() {
  const { runs, isLoading: benchLoading, triggerRun } = useBenchmarks()
  const [perf, setPerf] = useState<PerformanceSummary | null>(null)
  const [cost, setCost] = useState<CostSummary | null>(null)
  const [modelDist, setModelDist] = useState<ModelDistributionType | null>(null)
  const [recentTasks, setRecentTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getPerformanceSummary().catch(() => null),
      getCostSummary().catch(() => null),
      getModelDistribution().catch(() => null),
      getHistory({ per_page: 15, sort_by: 'created_at', order: 'desc' }).catch(() => null),
    ]).then(([p, c, m, h]) => {
      if (p) setPerf(p)
      if (c) setCost(c)
      if (m) setModelDist(m)
      if (h) setRecentTasks(h.items)
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full gap-3">
        <Loader2 className="w-5 h-5 animate-spin text-primary" />
        <span className="text-sm text-muted-foreground">Loading analytics...</span>
      </div>
    )
  }

  const totalTasks = perf?.total_tasks ?? 0
  const successRate = perf ? perf.success_rate * 100 : 0
  const avgRetries = perf?.avg_retries ?? 0
  const totalCost = cost?.total_cost_usd ?? 0
  const avgCostPerTask = totalTasks > 0 ? totalCost / totalTasks : 0

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-yellow-400 shadow-lg shadow-orange-500/20">
            <BarChart3 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">Analytics Dashboard</h1>
            <p className="text-xs text-muted-foreground">
              {totalTasks} tasks executed | Real-time performance metrics
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          {(['humaneval', 'mbpp', 'custom'] as const).map((type) => (
            <Button key={type} variant="outline" size="sm" onClick={() => triggerRun(type)} disabled={benchLoading} className="gap-1.5 rounded-xl text-xs">
              {benchLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
              {type}
            </Button>
          ))}
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        <StatCard label="Total Tasks" value={String(totalTasks)} icon={Hash} gradient="from-blue-500 to-cyan-400" />
        <StatCard
          label="Success Rate" value={`${successRate.toFixed(1)}%`}
          subtitle={`${perf?.tasks_by_status?.completed ?? 0} passed, ${perf?.tasks_by_status?.failed ?? 0} failed`}
          icon={Target} gradient="from-emerald-500 to-green-400"
          trend={successRate >= 70 ? 'Good' : undefined}
        />
        <StatCard
          label="Total Cost" value={`$${totalCost.toFixed(4)}`}
          subtitle={`$${avgCostPerTask.toFixed(4)} avg per task`}
          icon={DollarSign} gradient="from-purple-500 to-pink-400"
        />
        <StatCard
          label="Avg Retries" value={avgRetries.toFixed(1)}
          subtitle="self-repair cycles per task"
          icon={Wrench} gradient="from-orange-500 to-red-400"
        />
        <StatCard
          label="Models Used" value={String(modelDist?.distribution?.length ?? 0)}
          subtitle={modelDist?.distribution?.[0]?.model ?? 'none'}
          icon={Cpu} gradient="from-indigo-500 to-violet-400"
        />
      </div>

      {/* Status distribution */}
      {perf && Object.keys(perf.tasks_by_status).length > 0 && (
        <div className="rounded-2xl border border-border/20 bg-card/30 backdrop-blur-md p-4 card-futuristic">
          <div className="flex items-center gap-2 mb-3">
            <Activity className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-semibold">Task Status Distribution</h3>
          </div>
          <StatusPills data={perf.tasks_by_status} />
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-border/20 bg-card/30 backdrop-blur-md p-4 card-futuristic">
          <div className="flex items-center gap-2 mb-3">
            <DollarSign className="w-4 h-4 text-yellow-400" />
            <h3 className="text-sm font-semibold">Daily Cost (14d)</h3>
          </div>
          <DailyCostChart data={cost?.daily_costs ?? []} />
        </div>

        <div className="rounded-2xl border border-border/20 bg-card/30 backdrop-blur-md p-4 card-futuristic">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-semibold">Model Usage</h3>
          </div>
          <ModelDistribution data={modelDist} />
        </div>

        <div className="rounded-2xl border border-border/20 bg-card/30 backdrop-blur-md p-4 card-futuristic">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-semibold">Cost by Model</h3>
          </div>
          <CostAnalysis data={cost} />
        </div>
      </div>

      {/* Recent tasks */}
      <div className="rounded-2xl border border-border/20 bg-card/30 backdrop-blur-md p-4 card-futuristic">
        <div className="flex items-center gap-2 mb-4">
          <Clock className="w-4 h-4 text-blue-400" />
          <h3 className="text-sm font-semibold">Recent Tasks</h3>
          <span className="text-[10px] text-muted-foreground/60 bg-muted/30 px-1.5 py-0.5 rounded-md tabular-nums">{recentTasks.length}</span>
        </div>
        {recentTasks.length > 0 ? (<>
          <div className="space-y-1">
            {recentTasks.map((task) => {
              const created = new Date(task.created_at)
              const updated = new Date(task.updated_at)
              const durationSec = Math.round((updated.getTime() - created.getTime()) / 1000)
              const isTerminal = ['completed', 'failed', 'cancelled'].includes(task.status)
              return (
                <div key={task.id} className="flex items-center gap-3 py-3 px-3 rounded-xl hover:bg-accent/40 transition-colors group border border-transparent hover:border-border/20">
                  <StatusBadge status={task.status} />
                  <p className="text-xs flex-1 truncate group-hover:text-foreground transition-colors">{task.prompt}</p>
                  <div className="flex items-center gap-4 shrink-0 text-[10px] text-muted-foreground tabular-nums">
                    {task.complexity && (
                      <span className={cn(
                        'px-1.5 py-0.5 rounded font-medium',
                        task.complexity === 'simple' && 'bg-emerald-500/10 text-emerald-400',
                        task.complexity === 'medium' && 'bg-yellow-500/10 text-yellow-400',
                        task.complexity === 'hard' && 'bg-red-500/10 text-red-400',
                      )}>{task.complexity}</span>
                    )}
                    {isTerminal && durationSec > 0 && (
                      <span className="flex items-center gap-0.5">
                        <Clock className="w-3 h-3" />{durationSec}s
                      </span>
                    )}
                    <span>${task.total_cost_usd.toFixed(4)}</span>
                    {task.retry_count > 0 && (
                      <span className="text-orange-400 flex items-center gap-0.5">
                        <Wrench className="w-3 h-3" />{task.retry_count}
                      </span>
                    )}
                    {task.model_used && (
                      <span className="hidden lg:inline">{task.model_used}</span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
          <div className="pt-3 mt-2 border-t border-border/20 text-center">
            <a href="/history" className="text-xs text-primary hover:text-primary/80 transition-colors">
              View all tasks in History →
            </a>
          </div>
        </>) : (
          <div className="text-center py-8 text-muted-foreground">
            <p className="text-sm">No tasks yet. Submit your first task from the Chat page.</p>
          </div>
        )}
      </div>
    </div>
  )
}
