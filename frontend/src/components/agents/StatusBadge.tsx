import { cn } from '@/lib/utils'
import type { TaskStatus } from '@/lib/types'

const statusConfig: Record<string, { label: string; className: string; pulse: boolean }> = {
  pending: { label: 'Pending', className: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20', pulse: false },
  classifying: { label: 'Classifying', className: 'bg-sky-500/10 text-sky-400 border-sky-500/20', pulse: true },
  researching: { label: 'Researching', className: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20', pulse: true },
  questioning: { label: 'Preparing Q&A', className: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20', pulse: true },
  awaiting_answers: { label: 'Awaiting Answers', className: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20', pulse: true },
  planning: { label: 'Planning', className: 'bg-blue-500/10 text-blue-400 border-blue-500/20', pulse: true },
  awaiting_approval: { label: 'Awaiting Approval', className: 'bg-amber-500/10 text-amber-400 border-amber-500/20', pulse: true },
  coding: { label: 'Coding', className: 'bg-purple-500/10 text-purple-400 border-purple-500/20', pulse: true },
  executing: { label: 'Executing', className: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20', pulse: true },
  reviewing: { label: 'Reviewing', className: 'bg-orange-500/10 text-orange-400 border-orange-500/20', pulse: true },
  repairing: { label: 'Repairing', className: 'bg-red-500/10 text-red-400 border-red-500/20', pulse: true },
  completed: { label: 'Completed', className: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20', pulse: false },
  failed: { label: 'Failed', className: 'bg-red-500/10 text-red-400 border-red-500/20', pulse: false },
  cancelled: { label: 'Cancelled', className: 'bg-amber-500/10 text-amber-400 border-amber-500/20', pulse: false },
}

interface StatusBadgeProps {
  status: TaskStatus | string
  className?: string
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status] ?? {
    label: status,
    className: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
    pulse: false,
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-[11px] font-semibold tracking-wide uppercase',
        config.className,
        className,
      )}
    >
      {config.pulse && (
        <span className="relative flex h-1.5 w-1.5">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 bg-current" />
          <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-current" />
        </span>
      )}
      {config.label}
    </span>
  )
}
