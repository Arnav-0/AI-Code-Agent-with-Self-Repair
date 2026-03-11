'use client'

import { useState, useEffect } from 'react'
import { ChevronDown, ChevronRight, Brain, Code2, Play, Search, Wrench, Clock, Coins, Hash } from 'lucide-react'
import { cn } from '@/lib/utils'

const agentConfig: Record<string, { icon: React.ComponentType<{ className?: string }>; gradient: string; label: string }> = {
  planner: { icon: Brain, gradient: 'from-blue-500 to-cyan-400', label: 'Planner' },
  coder: { icon: Code2, gradient: 'from-purple-500 to-pink-400', label: 'Coder' },
  executor: { icon: Play, gradient: 'from-yellow-500 to-orange-400', label: 'Executor' },
  reviewer: { icon: Search, gradient: 'from-orange-500 to-red-400', label: 'Reviewer' },
}

interface AgentCardProps {
  agentType: string
  status: 'running' | 'completed' | 'error'
  thinking?: string
  durationMs?: number
  costUsd?: number
  tokensUsed?: number
  outputSummary?: string
}

export function AgentCard({
  agentType,
  status,
  thinking,
  durationMs,
  costUsd,
  tokensUsed,
  outputSummary,
}: AgentCardProps) {
  const [expanded, setExpanded] = useState(status === 'running')
  const [elapsed, setElapsed] = useState(0)
  const config = agentConfig[agentType] ?? { icon: Wrench, gradient: 'from-zinc-500 to-zinc-400', label: agentType }
  const Icon = config.icon

  useEffect(() => {
    if (status !== 'running') return
    setElapsed(0)
    const start = Date.now()
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - start) / 1000))
    }, 1000)
    return () => clearInterval(interval)
  }, [status])

  return (
    <div
      className={cn(
        'rounded-2xl border bg-card/40 backdrop-blur-md transition-all duration-300 overflow-hidden card-futuristic',
        status === 'running' && 'border-primary/20 pulse-glow',
        status === 'completed' && 'border-emerald-500/15 shadow-sm shadow-emerald-500/5',
        status === 'error' && 'border-red-500/15 shadow-sm shadow-red-500/5',
      )}
    >
      <button
        className="flex w-full items-center gap-3 p-4 text-left hover:bg-accent/30 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className={cn(
          'flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br shadow-sm',
          config.gradient,
        )}>
          <Icon className="h-4 w-4 text-white" />
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold">{config.label}</p>
          <p className="text-[11px] text-muted-foreground">
            {status === 'running' && 'Processing...'}
            {status === 'completed' && 'Completed'}
            {status === 'error' && 'Failed'}
          </p>
        </div>

        {status === 'running' && (
          <div className="flex items-center gap-2 mr-2">
            <div className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="h-1.5 w-1.5 rounded-full bg-primary animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </div>
            <span className="text-xs text-muted-foreground tabular-nums">{elapsed}s</span>
          </div>
        )}

        {status === 'completed' && durationMs !== undefined && (
          <div className="flex items-center gap-3 mr-2">
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="w-3 h-3" />
              {(durationMs / 1000).toFixed(1)}s
            </span>
            {costUsd ? (
              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                <Coins className="w-3 h-3" />
                ${costUsd.toFixed(4)}
              </span>
            ) : null}
          </div>
        )}

        {status === 'completed' && (
          <div className="w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center mr-1">
            <svg className="w-3 h-3 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
        )}

        {(thinking || tokensUsed || outputSummary) && (
          expanded
            ? <ChevronDown className="h-4 w-4 text-muted-foreground/50" />
            : <ChevronRight className="h-4 w-4 text-muted-foreground/50" />
        )}
      </button>

      {expanded && (thinking || tokensUsed || outputSummary) && (
        <div className="border-t border-border/50 px-4 pb-4 pt-3 space-y-3 bg-muted/20">
          {tokensUsed !== undefined && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Hash className="w-3 h-3" />
              <span>{tokensUsed.toLocaleString()} tokens</span>
            </div>
          )}
          {outputSummary && (
            <p className="text-xs text-muted-foreground leading-relaxed">{outputSummary}</p>
          )}
          {thinking && (
            <pre className="text-xs text-muted-foreground/80 whitespace-pre-wrap font-mono leading-relaxed bg-background/50 rounded-xl p-3 border border-border/30 max-h-48 overflow-auto">
              {thinking}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}
