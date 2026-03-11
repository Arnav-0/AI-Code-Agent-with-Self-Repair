'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { StatusBadge } from '@/components/agents/StatusBadge'
import { AgentTimeline } from '@/components/agents/AgentTimeline'
import { CodeBlock } from '@/components/chat/CodeBlock'
import { TerminalOutput } from '@/components/execution/TerminalOutput'
import { Button } from '@/components/ui/button'
import { approveTask, cancelTask } from '@/lib/api'
import {
  Code2,
  Terminal,
  XCircle,
  Clock,
  DollarSign,
  Hash,
  Zap,
  CalendarDays,
  ChevronDown,
  ChevronRight,
  FileJson,
  Cpu,
  RotateCcw,
  Activity,
  Check,
  X,
  AlertTriangle,
  Play,
  ListTree,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { TaskDetail as TaskDetailType } from '@/lib/types'

interface TaskDetailProps {
  task: TaskDetailType
}

/** Render plan subtasks as a structured visual list instead of raw JSON. */
function PlanSubtasks({ plan }: { plan: Record<string, unknown> }) {
  const subtasks = (plan.subtasks ?? []) as Array<{
    id: number; description: string; dependencies?: number[]; estimated_complexity?: string
  }>
  const reasoning = plan.reasoning as string | undefined

  if (subtasks.length === 0) {
    // Fallback: show formatted JSON but in a nice container
    const { _meta, ...display } = plan
    return (
      <pre className="text-[11px] bg-[#0a0e14] rounded-xl p-4 overflow-auto max-h-64 font-mono text-emerald-300/70 leading-relaxed border border-border/20">
        {JSON.stringify(display, null, 2)}
      </pre>
    )
  }

  return (
    <div className="space-y-2">
      {subtasks.map((st, i) => (
        <div
          key={st.id ?? i}
          className="flex items-start gap-3 py-2.5 px-3 rounded-xl bg-background/30 border border-border/20"
        >
          <div className="flex items-center justify-center w-7 h-7 rounded-lg text-xs font-bold bg-primary/10 text-primary border border-primary/20 shrink-0 mt-0.5">
            {i + 1}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs text-foreground leading-relaxed">{st.description}</p>
            <div className="flex items-center gap-2 mt-1.5">
              {st.estimated_complexity && (
                <span className={cn(
                  'text-[10px] px-1.5 py-0.5 rounded font-medium',
                  st.estimated_complexity === 'simple' && 'bg-emerald-500/10 text-emerald-400',
                  st.estimated_complexity === 'medium' && 'bg-yellow-500/10 text-yellow-400',
                  st.estimated_complexity === 'hard' && 'bg-red-500/10 text-red-400',
                )}>
                  {st.estimated_complexity}
                </span>
              )}
              {st.dependencies && st.dependencies.length > 0 && (
                <span className="text-[10px] text-muted-foreground/60">
                  depends on: {st.dependencies.join(', ')}
                </span>
              )}
            </div>
          </div>
        </div>
      ))}
      {reasoning && (
        <p className="text-[11px] text-muted-foreground/50 italic mt-1 px-1">{reasoning}</p>
      )}
    </div>
  )
}

/** Render trace output data in a readable way instead of raw JSON dump. */
function TraceOutput({ data }: { data: Record<string, unknown> }) {
  // Try to extract meaningful fields
  const code = data.code as string | undefined
  const explanation = data.explanation as string | undefined
  const imports = data.imports as string[] | undefined
  const fixDescription = data.fix_description as string | undefined
  const rootCause = data.root_cause as string | undefined
  const confidence = data.confidence as number | undefined

  const hasStructured = code || explanation || fixDescription || rootCause

  if (!hasStructured) {
    // Fallback to JSON but formatted nicely
    return (
      <pre className="text-[11px] bg-[#0a0e14] rounded-xl p-3 overflow-auto max-h-40 font-mono text-muted-foreground/70 leading-relaxed border border-border/20">
        {JSON.stringify(data, null, 2)}
      </pre>
    )
  }

  return (
    <div className="space-y-2">
      {rootCause && (
        <div className="rounded-lg bg-red-500/5 border border-red-500/15 px-3 py-2">
          <p className="text-[10px] text-red-400/60 uppercase tracking-wider font-semibold mb-0.5">Root Cause</p>
          <p className="text-xs text-red-300/80">{rootCause}</p>
        </div>
      )}
      {fixDescription && (
        <div className="rounded-lg bg-emerald-500/5 border border-emerald-500/15 px-3 py-2">
          <p className="text-[10px] text-emerald-400/60 uppercase tracking-wider font-semibold mb-0.5">Fix Applied</p>
          <p className="text-xs text-emerald-300/80">{fixDescription}</p>
          {confidence != null && (
            <p className="text-[10px] text-muted-foreground/50 mt-1">
              Confidence: {(confidence * 100).toFixed(0)}%
            </p>
          )}
        </div>
      )}
      {explanation && !fixDescription && (
        <p className="text-xs text-foreground/70 leading-relaxed">{explanation}</p>
      )}
      {imports && imports.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {imports.map((imp) => (
            <span key={imp} className="text-[10px] font-mono bg-muted/30 px-1.5 py-0.5 rounded border border-border/20 text-muted-foreground">
              {imp}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

export function TaskDetail({ task }: TaskDetailProps) {
  const router = useRouter()
  const [showPlan, setShowPlan] = useState(false)
  const [showTraceDetails, setShowTraceDetails] = useState<string | null>(null)
  const [approving, setApproving] = useState(false)

  const finalOutputLines = task.final_output
    ? task.final_output.split('\n').map((l) => ({ type: 'stdout' as const, content: l }))
    : []

  return (
    <div className="p-5 space-y-5 overflow-auto h-full">
      {/* Header */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 flex-wrap">
          <StatusBadge status={task.status} />
          {task.complexity && (
            <span className={cn(
              'text-[11px] font-medium px-2 py-0.5 rounded-md border',
              task.complexity === 'hard' && 'bg-red-500/10 border-red-500/20 text-red-400',
              task.complexity === 'medium' && 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400',
              task.complexity === 'simple' && 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
            )}>
              <Cpu className="w-3 h-3 inline mr-1" />
              {task.complexity}
            </span>
          )}
          {task.model_used && (
            <span className="text-[11px] text-muted-foreground bg-muted/50 px-2 py-0.5 rounded-md border border-border/30">
              {task.model_used}
            </span>
          )}
          {task.retry_count > 0 && (
            <span className="text-[11px] font-medium text-orange-400 bg-orange-500/10 px-2 py-0.5 rounded-md border border-orange-500/20 flex items-center gap-1">
              <RotateCcw className="w-3 h-3" />
              {task.retry_count} retries
            </span>
          )}
        </div>
        <p className="text-sm text-foreground leading-relaxed">{task.prompt}</p>
        {['completed', 'failed', 'cancelled'].includes(task.status) && (
          <div className="flex items-center gap-2 mt-2">
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5 rounded-xl text-xs"
              onClick={() => router.push(`/?prompt=${encodeURIComponent(task.prompt)}`)}
            >
              <Play className="w-3 h-3" />
              Re-run
            </Button>
            {task.final_code && (
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5 rounded-xl text-xs border-purple-500/30 text-purple-400 hover:bg-purple-500/10"
                onClick={() => router.push(`/?prompt=${encodeURIComponent(task.prompt)}&refine=1`)}
              >
                <RotateCcw className="w-3 h-3" />
                Refine Code
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Metrics row */}
      <div className="flex gap-3 flex-wrap">
        <div className="flex items-center gap-2 rounded-lg bg-muted/30 px-3 py-2 border border-border/20">
          <DollarSign className="w-3.5 h-3.5 text-purple-400" />
          <div>
            <p className="text-[10px] text-muted-foreground">Cost</p>
            <p className="text-xs font-mono font-semibold">${task.total_cost_usd.toFixed(4)}</p>
          </div>
        </div>
        {task.total_time_ms != null && task.total_time_ms > 0 && (
          <div className="flex items-center gap-2 rounded-lg bg-muted/30 px-3 py-2 border border-border/20">
            <Clock className="w-3.5 h-3.5 text-yellow-400" />
            <div>
              <p className="text-[10px] text-muted-foreground">Duration</p>
              <p className="text-xs font-mono font-semibold">{(task.total_time_ms / 1000).toFixed(1)}s</p>
            </div>
          </div>
        )}
        <div className="flex items-center gap-2 rounded-lg bg-muted/30 px-3 py-2 border border-border/20">
          <CalendarDays className="w-3.5 h-3.5 text-blue-400" />
          <div>
            <p className="text-[10px] text-muted-foreground">Created</p>
            <p className="text-xs font-mono font-semibold">{new Date(task.created_at).toLocaleString()}</p>
          </div>
        </div>
        {task.traces.length > 0 && (
          <div className="flex items-center gap-2 rounded-lg bg-muted/30 px-3 py-2 border border-border/20">
            <Zap className="w-3.5 h-3.5 text-emerald-400" />
            <div>
              <p className="text-[10px] text-muted-foreground">Agent Steps</p>
              <p className="text-xs font-mono font-semibold">{task.traces.length}</p>
            </div>
          </div>
        )}
      </div>

      {/* Agent Timeline */}
      {task.traces.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Activity className="w-3.5 h-3.5 text-primary" />
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Agent Pipeline</p>
          </div>
          <AgentTimeline traces={task.traces} />

          {/* Individual trace cards */}
          <div className="space-y-2">
            {task.traces.map((trace, i) => {
              const isExpanded = showTraceDetails === trace.id
              return (
                <div key={trace.id} className="rounded-xl border border-border/20 bg-card/30 overflow-hidden">
                  <button
                    className="flex w-full items-center gap-3 p-3 text-left hover:bg-accent/20 transition-colors"
                    onClick={() => setShowTraceDetails(isExpanded ? null : trace.id)}
                  >
                    <div className="flex items-center justify-center w-7 h-7 rounded-lg text-xs font-bold bg-primary/10 text-primary">
                      {i + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold capitalize">{trace.agent_type}</p>
                      {trace.reasoning && (
                        <p className="text-[11px] text-muted-foreground truncate mt-0.5">{trace.reasoning}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
                      {trace.duration_ms != null && (
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {(trace.duration_ms / 1000).toFixed(1)}s
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Hash className="w-3 h-3" />
                        {trace.tokens_used.toLocaleString()}
                      </span>
                      <span className="flex items-center gap-1">
                        <DollarSign className="w-3 h-3" />
                        ${trace.cost_usd.toFixed(4)}
                      </span>
                    </div>
                    {isExpanded ? (
                      <ChevronDown className="w-3.5 h-3.5 text-muted-foreground/50" />
                    ) : (
                      <ChevronRight className="w-3.5 h-3.5 text-muted-foreground/50" />
                    )}
                  </button>
                  {isExpanded && (
                    <div className="border-t border-border/20 p-3 space-y-2.5 bg-muted/10">
                      {trace.reasoning && (
                        <div>
                          <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Reasoning</p>
                          <p className="text-xs text-foreground/80 leading-relaxed">{trace.reasoning}</p>
                        </div>
                      )}
                      {trace.output_data && (
                        <div>
                          <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1.5">Output</p>
                          <TraceOutput data={trace.output_data} />
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Plan Approval (for awaiting_approval tasks) */}
      {task.status === 'awaiting_approval' && task.plan && (() => {
        const plan = task.plan as Record<string, unknown>
        return (
          <div className="rounded-2xl border-2 border-amber-500/30 bg-amber-500/5 overflow-hidden">
            <div className="p-4 border-b border-amber-500/20">
              <div className="flex items-center gap-2 mb-1">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-bold text-amber-300">Plan Awaiting Approval</h3>
              </div>
              <p className="text-xs text-muted-foreground">
                This hard task needs your approval before execution begins.
              </p>
            </div>
            <div className="p-4">
              <PlanSubtasks plan={plan} />
            </div>
            <div className="p-4 border-t border-amber-500/20 flex items-center gap-3">
              <Button
                onClick={async () => {
                  setApproving(true)
                  try { await approveTask(task.id) } catch { /* */ }
                  setApproving(false)
                }}
                disabled={approving}
                size="sm"
                className="gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white"
              >
                <Check className="w-4 h-4" />
                {approving ? 'Approving...' : 'Approve & Execute'}
              </Button>
              <Button
                onClick={async () => {
                  try { await cancelTask(task.id) } catch { /* */ }
                }}
                variant="outline"
                size="sm"
                className="gap-2 rounded-xl border-red-500/30 text-red-400 hover:bg-red-500/10"
              >
                <X className="w-4 h-4" />
                Reject
              </Button>
            </div>
          </div>
        )
      })()}

      {/* Plan (collapsible, for completed tasks) */}
      {task.plan && task.status !== 'awaiting_approval' && (() => {
        const plan = task.plan as Record<string, unknown>
        return (
          <div className="space-y-2">
            <button
              className="flex items-center gap-2 group"
              onClick={() => setShowPlan(!showPlan)}
            >
              <ListTree className="w-3.5 h-3.5 text-blue-400" />
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider group-hover:text-foreground transition-colors">
                Execution Plan
              </p>
              <span className="text-[10px] text-muted-foreground/40">
                {((plan.subtasks ?? []) as unknown[]).length} subtasks
              </span>
              {showPlan ? (
                <ChevronDown className="w-3 h-3 text-muted-foreground/50" />
              ) : (
                <ChevronRight className="w-3 h-3 text-muted-foreground/50" />
              )}
            </button>
            {showPlan && (
              <div className="rounded-xl border border-border/20 bg-card/30 p-3">
                <PlanSubtasks plan={plan} />
              </div>
            )}
          </div>
        )
      })()}

      {/* Final code */}
      {task.final_code && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Code2 className="w-3.5 h-3.5 text-purple-400" />
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Final Code</p>
          </div>
          <CodeBlock code={task.final_code} language="python" />
        </div>
      )}

      {/* Execution output */}
      {finalOutputLines.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Terminal className="w-3.5 h-3.5 text-yellow-400" />
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Execution Output</p>
          </div>
          <TerminalOutput lines={finalOutputLines} exitCode={task.status === 'completed' ? 0 : 1} />
        </div>
      )}

      {/* Error */}
      {task.error_message && (
        <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-4">
          <div className="flex items-center gap-2 mb-2">
            <XCircle className="w-4 h-4 text-red-400" />
            <p className="text-sm text-red-400 font-semibold">Error</p>
          </div>
          <p className="text-xs text-red-300/80 font-mono leading-relaxed whitespace-pre-wrap">{task.error_message}</p>
        </div>
      )}
    </div>
  )
}
