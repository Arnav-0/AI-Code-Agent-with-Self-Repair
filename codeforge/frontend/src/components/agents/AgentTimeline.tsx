'use client'

import { cn } from '@/lib/utils'
import { Clock, DollarSign, Hash } from 'lucide-react'
import type { AgentTrace } from '@/lib/types'

const agentConfig: Record<string, { color: string; bg: string }> = {
  planner: { color: 'bg-blue-500', bg: 'bg-blue-500/10' },
  classifier: { color: 'bg-sky-400', bg: 'bg-sky-400/10' },
  coder: { color: 'bg-purple-500', bg: 'bg-purple-500/10' },
  executor: { color: 'bg-yellow-500', bg: 'bg-yellow-500/10' },
  reviewer: { color: 'bg-orange-500', bg: 'bg-orange-500/10' },
}

interface AgentTimelineProps {
  traces: AgentTrace[]
  className?: string
}

export function AgentTimeline({ traces, className }: AgentTimelineProps) {
  if (traces.length === 0) return null

  const totalMs = traces.reduce((sum, t) => sum + (t.duration_ms ?? 0), 0)
  const totalTokens = traces.reduce((sum, t) => sum + t.tokens_used, 0)
  const totalCost = traces.reduce((sum, t) => sum + t.cost_usd, 0)

  return (
    <div className={cn('space-y-3', className)}>
      {/* Summary stats */}
      <div className="flex items-center gap-4 text-[11px] text-muted-foreground">
        <span className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {(totalMs / 1000).toFixed(1)}s total
        </span>
        <span className="flex items-center gap-1">
          <Hash className="w-3 h-3" />
          {totalTokens.toLocaleString()} tokens
        </span>
        <span className="flex items-center gap-1">
          <DollarSign className="w-3 h-3" />
          ${totalCost.toFixed(4)}
        </span>
        <span className="text-muted-foreground/50">
          {traces.length} step{traces.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Bar timeline */}
      <div className="flex h-7 rounded-xl overflow-hidden border border-border/30 bg-muted/20">
        {traces.map((trace, i) => {
          const pct = totalMs > 0 ? ((trace.duration_ms ?? 0) / totalMs) * 100 : 100 / traces.length
          const config = agentConfig[trace.agent_type] ?? { color: 'bg-zinc-500', bg: 'bg-zinc-500/10' }
          return (
            <div
              key={i}
              className={cn(
                'group relative flex items-center justify-center text-[10px] font-semibold text-white overflow-hidden transition-all hover:brightness-125 cursor-default',
                config.color
              )}
              style={{ width: `${Math.max(pct, 2)}%` }}
              title={`${trace.agent_type}: ${trace.duration_ms ?? 0}ms | ${trace.tokens_used} tokens | $${trace.cost_usd.toFixed(4)}`}
            >
              {pct > 12 && (
                <span className="capitalize truncate px-1.5 drop-shadow-sm">
                  {trace.agent_type}
                </span>
              )}

              {/* Tooltip */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-20 whitespace-nowrap rounded-xl bg-popover border border-border px-3 py-2 text-xs text-popover-foreground shadow-lg">
                <p className="font-semibold capitalize mb-1">{trace.agent_type}</p>
                <div className="space-y-0.5 text-[11px] text-muted-foreground">
                  <p>{trace.duration_ms ?? 0}ms</p>
                  <p>{trace.tokens_used.toLocaleString()} tokens</p>
                  <p>${trace.cost_usd.toFixed(4)}</p>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3">
        {traces.map((trace, i) => {
          const config = agentConfig[trace.agent_type] ?? { color: 'bg-zinc-500', bg: 'bg-zinc-500/10' }
          return (
            <div key={i} className="flex items-center gap-1.5">
              <span className={cn('w-2 h-2 rounded-full', config.color)} />
              <span className="text-[10px] text-muted-foreground capitalize">{trace.agent_type}</span>
              {trace.duration_ms != null && (
                <span className="text-[10px] text-muted-foreground/50">{(trace.duration_ms / 1000).toFixed(1)}s</span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
