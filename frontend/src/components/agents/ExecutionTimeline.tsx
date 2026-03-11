'use client'

import { cn } from '@/lib/utils'

interface TimelinePhase {
  name: string
  durationMs: number
  status: 'completed' | 'running' | 'pending' | 'error'
  color: string
}

interface ExecutionTimelineProps {
  phases: TimelinePhase[]
}

export function ExecutionTimeline({ phases }: ExecutionTimelineProps) {
  const totalMs = phases.reduce((sum, p) => sum + p.durationMs, 0) || 1

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
          Execution Timeline
        </p>
        <span className="text-[10px] text-muted-foreground tabular-nums">
          {(totalMs / 1000).toFixed(1)}s total
        </span>
      </div>
      <div className="flex h-8 rounded-xl overflow-hidden border border-border/20">
        {phases.map((phase, i) => {
          const width = Math.max((phase.durationMs / totalMs) * 100, 4)
          return (
            <div
              key={i}
              className={cn(
                'relative group flex items-center justify-center transition-all',
                phase.status === 'running' && 'animate-pulse',
              )}
              style={{
                width: `${width}%`,
                backgroundColor:
                  phase.status === 'error' ? '#ef444440' : `${phase.color}20`,
                borderRight:
                  i < phases.length - 1
                    ? '1px solid rgba(255,255,255,0.05)'
                    : undefined,
              }}
            >
              <span
                className="text-[9px] font-medium truncate px-1"
                style={{ color: phase.color }}
              >
                {phase.name}
              </span>
              {/* Tooltip on hover */}
              <div className="absolute bottom-full mb-1 left-1/2 -translate-x-1/2 bg-card border border-border rounded-lg px-2.5 py-1.5 text-[10px] opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10 shadow-xl">
                <p className="font-semibold" style={{ color: phase.color }}>
                  {phase.name}
                </p>
                <p className="text-muted-foreground tabular-nums">
                  {(phase.durationMs / 1000).toFixed(2)}s ({width.toFixed(0)}%)
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
