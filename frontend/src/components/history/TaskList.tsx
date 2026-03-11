'use client'

import { cn } from '@/lib/utils'
import { StatusBadge } from '@/components/agents/StatusBadge'
import { Clock, DollarSign, RotateCcw, ChevronLeft, ChevronRight, Inbox, Activity } from 'lucide-react'
import type { Task } from '@/lib/types'

const TERMINAL_STATUSES = new Set(['completed', 'failed', 'cancelled'])

interface TaskListProps {
  tasks: Task[]
  selectedId: string | null
  onSelect: (task: Task) => void
  total: number
  page: number
  perPage: number
  onPageChange: (page: number) => void
}

export function TaskList({
  tasks,
  selectedId,
  onSelect,
  total,
  page,
  perPage,
  onPageChange,
}: TaskListProps) {
  const totalPages = Math.ceil(total / perPage)

  if (tasks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-muted-foreground px-8 text-center">
        <Inbox className="w-8 h-8 mb-3 text-muted-foreground/40" />
        <p className="text-sm font-medium">No tasks yet</p>
        <p className="text-xs text-muted-foreground/60 mt-1">Submit your first task to get started</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-auto">
        {tasks.map((task) => {
          const isLive = !TERMINAL_STATUSES.has(task.status)
          return (
            <button
              key={task.id}
              onClick={() => onSelect(task)}
              className={cn(
                'w-full text-left px-4 py-3.5 border-b border-border/30 hover:bg-accent/30 transition-all relative',
                selectedId === task.id && 'bg-accent/50 border-l-2 border-l-primary',
              )}
            >
              {/* Live indicator dot */}
              {isLive && (
                <span className="absolute top-3 right-3 h-2 w-2 rounded-full bg-primary animate-pulse" />
              )}

              <p className="text-sm font-medium truncate mb-2 pr-4">
                {task.prompt.slice(0, 100)}
                {task.prompt.length > 100 ? '...' : ''}
              </p>

              <div className="flex items-center gap-2 flex-wrap">
                <StatusBadge status={task.status} />

                {isLive && (
                  <span className="text-[10px] font-medium text-primary flex items-center gap-0.5">
                    <Activity className="w-2.5 h-2.5" />
                    live
                  </span>
                )}

                {task.model_used && (
                  <span className="text-[10px] text-muted-foreground/70 bg-muted/40 px-1.5 py-0.5 rounded">
                    {task.model_used}
                  </span>
                )}

                <span className="flex items-center gap-0.5 text-[10px] text-muted-foreground/70">
                  <DollarSign className="w-2.5 h-2.5" />
                  {task.total_cost_usd.toFixed(4)}
                </span>

                {task.total_time_ms != null && task.total_time_ms > 0 && (
                  <span className="flex items-center gap-0.5 text-[10px] text-muted-foreground/70">
                    <Clock className="w-2.5 h-2.5" />
                    {(task.total_time_ms / 1000).toFixed(1)}s
                  </span>
                )}

                {task.retry_count > 0 && (
                  <span className="flex items-center gap-0.5 text-[10px] text-orange-400/80">
                    <RotateCcw className="w-2.5 h-2.5" />
                    {task.retry_count}
                  </span>
                )}

                <span className="text-[10px] text-muted-foreground/50 ml-auto">
                  {new Date(task.created_at).toLocaleDateString()}
                </span>
              </div>
            </button>
          )
        })}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-2.5 border-t border-border/30 bg-card/30">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="flex items-center gap-1 text-xs text-muted-foreground disabled:opacity-30 hover:text-foreground transition-colors"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            Prev
          </button>
          <span className="text-[11px] text-muted-foreground">
            {page} of {totalPages}
          </span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="flex items-center gap-1 text-xs text-muted-foreground disabled:opacity-30 hover:text-foreground transition-colors"
          >
            Next
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  )
}
