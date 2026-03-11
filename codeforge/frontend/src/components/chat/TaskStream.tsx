'use client'

import { useEffect, useRef } from 'react'
import { AgentCard } from '@/components/agents/AgentCard'
import { AgentFlowDiagram } from '@/components/agents/AgentFlowDiagram'
import { ExecutionTimeline } from '@/components/agents/ExecutionTimeline'
import { CodeBlock } from '@/components/chat/CodeBlock'
import { TerminalOutput } from '@/components/execution/TerminalOutput'
import { RepairDiff } from '@/components/execution/RepairDiff'
import { StatusBadge } from '@/components/agents/StatusBadge'
import { Button } from '@/components/ui/button'
import { ResearchDisplay } from '@/components/chat/ResearchDisplay'
import { QuestionForm } from '@/components/chat/QuestionForm'
import {
  Zap, Code2, Terminal, Wrench, CheckCircle2, XCircle,
  FileJson, Check, X, AlertTriangle, Search, HelpCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { WSEvent, ResearchFindings, ResearchQuestion } from '@/lib/types'

interface AgentState {
  type: string
  status: 'running' | 'completed' | 'error'
  thinking: string
  durationMs?: number
  costUsd?: number
  tokensUsed?: number
}

interface TerminalState {
  lines: Array<{ type: 'stdout' | 'stderr' | 'info'; content: string }>
  exitCode?: number
  executionTime?: number
  memoryUsage?: number
}

interface RepairAttemptState {
  attemptNumber: number
  error: string
  originalCode: string
  fixedCode: string
  success?: boolean
}

interface PlanData {
  subtasks?: Array<{ id: number; description: string; dependencies?: number[]; estimated_complexity?: string }>
  [key: string]: unknown
}

function buildStreamState(events: WSEvent[]) {
  const agents: AgentState[] = []
  let generatedCode = ''
  const terminal: TerminalState = { lines: [] }
  const repairAttempts: RepairAttemptState[] = []
  let taskStatus = ''
  let taskError = ''
  let finalCode = ''
  let planFromEvent: PlanData | null = null
  let researchFromEvent: ResearchFindings | null = null
  let questionsFromEvent: ResearchQuestion[] = []

  for (const ev of events) {
    const data = ev.data as Record<string, unknown>
    switch (ev.event) {
      case 'status.change':
      case 'task.status_changed':
        taskStatus = String(data.status ?? '')
        break
      case 'research.complete':
        researchFromEvent = (data.findings as ResearchFindings) || null
        break
      case 'questions.ready':
        questionsFromEvent = (data.questions as ResearchQuestion[]) || []
        taskStatus = 'awaiting_answers'
        break
      case 'answers.received':
        questionsFromEvent = []
        break
      case 'task.started':
        taskStatus = 'planning'
        break
      case 'task.completed':
        taskStatus = 'completed'
        finalCode = String(data.final_code ?? '')
        break
      case 'task.failed':
        taskStatus = 'failed'
        taskError = String(data.error_message ?? data.error ?? 'Unknown error')
        break
      case 'task.cancelled':
        taskStatus = 'cancelled'
        break
      case 'plan.ready':
        taskStatus = 'awaiting_approval'
        planFromEvent = (data.plan as PlanData) || null
        break
      case 'agent.started': {
        const agentType = String(data.agent_type ?? '')
        agents.push({ type: agentType, status: 'running', thinking: '' })
        break
      }
      case 'agent.thinking': {
        const agentType = String(data.agent_type ?? '')
        const last = agents.findLast((a) => a.type === agentType)
        if (last) last.thinking += String(data.chunk ?? data.text ?? '')
        break
      }
      case 'agent.completed': {
        const agentType = String(data.agent_type ?? '')
        const last = agents.findLast((a) => a.type === agentType)
        if (last) {
          last.status = 'completed'
          last.durationMs = Number(data.duration_ms ?? 0)
          last.costUsd = Number(data.cost_usd ?? 0)
          last.tokensUsed = Number(data.tokens_used ?? 0)
        }
        break
      }
      case 'code.generated':
        generatedCode = String(data.code ?? '')
        break
      case 'execution.stdout':
        terminal.lines.push({ type: 'stdout', content: String(data.line ?? data.text ?? '') })
        break
      case 'execution.stderr':
        terminal.lines.push({ type: 'stderr', content: String(data.line ?? data.text ?? '') })
        break
      case 'execution.started':
        terminal.lines.push({
          type: 'info',
          content: `$ Running code (attempt #${Number(data.retry_number ?? 0) + 1})...`,
        })
        break
      case 'execution.completed': {
        terminal.exitCode = Number(data.exit_code ?? 0)
        terminal.executionTime = Number(data.execution_time_ms ?? 0)
        terminal.memoryUsage = Number(data.memory_used_mb ?? 0)
        if (terminal.exitCode === 0) {
          terminal.lines.push({ type: 'info', content: '✓ Execution succeeded' })
        } else {
          terminal.lines.push({ type: 'info', content: `✗ Exited with code ${terminal.exitCode}` })
        }
        break
      }
      case 'repair.started':
        repairAttempts.push({
          attemptNumber: Number(data.retry_number ?? data.attempt ?? repairAttempts.length + 1),
          error: String(data.error_summary ?? data.error ?? ''),
          originalCode: String(data.original_code ?? generatedCode),
          fixedCode: '',
        })
        break
      case 'repair.fix_applied': {
        const last = repairAttempts[repairAttempts.length - 1]
        if (last) {
          last.fixedCode = String(data.fixed_code ?? '')
          last.success = Boolean(data.success)
        }
        break
      }
    }
  }

  return { agents, generatedCode, terminal, repairAttempts, taskStatus, taskError, finalCode, planFromEvent, researchFromEvent, questionsFromEvent }
}

interface TaskStreamProps {
  events: WSEvent[]
  isLoading: boolean
  taskDetail?: import('@/lib/types').TaskDetail | null
  awaitingApproval?: boolean
  awaitingAnswers?: boolean
  planData?: PlanData | null
  researchFindings?: ResearchFindings | null
  questions?: ResearchQuestion[]
  onApprove?: () => void
  onReject?: () => void
  onHintClick?: (hint: string) => void
  onSubmitAnswers?: (answers: Record<string, string>) => void
  onSkipQuestions?: () => void
}

export function TaskStream({
  events, isLoading, taskDetail, awaitingApproval, awaitingAnswers,
  planData, researchFindings: propResearch, questions: propQuestions,
  onApprove, onReject, onHintClick, onSubmitAnswers, onSkipQuestions,
}: TaskStreamProps) {
  const bottomRef = useRef<HTMLDivElement>(null)
  let { agents, generatedCode, terminal, repairAttempts, taskStatus, taskError, finalCode, planFromEvent, researchFromEvent, questionsFromEvent } =
    buildStreamState(events)

  // Merge plan data from props or events
  const displayPlan = planData || planFromEvent

  // Merge research data from props or events
  const displayResearch = propResearch || researchFromEvent
  const displayQuestions = (propQuestions && propQuestions.length > 0) ? propQuestions : questionsFromEvent

  if (taskDetail && !taskStatus) {
    taskStatus = taskDetail.status
    if (taskDetail.status === 'failed') {
      taskError = taskDetail.error_message || 'Unknown error'
    }
    if (taskDetail.final_code) {
      finalCode = taskDetail.final_code
    }
  }
  if (taskDetail && taskStatus && !['completed', 'failed', 'cancelled'].includes(taskStatus)) {
    if (['completed', 'failed', 'cancelled'].includes(taskDetail.status)) {
      taskStatus = taskDetail.status
      if (taskDetail.status === 'failed') {
        taskError = taskDetail.error_message || taskError || 'Unknown error'
      }
      if (taskDetail.final_code) {
        finalCode = taskDetail.final_code
      }
    }
  }

  // If hook says awaiting_approval or awaiting_answers, override status
  if (awaitingApproval) {
    taskStatus = 'awaiting_approval'
  }
  if (awaitingAnswers) {
    taskStatus = 'awaiting_answers'
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events, awaitingApproval, awaitingAnswers])

  if (!finalCode && taskDetail?.final_code) {
    finalCode = taskDetail.final_code
  }

  // When joining a live task mid-stream (e.g. from history), we may have no WS events yet
  // but taskDetail tells us what stage we're in. Synthesize from REST data.
  if (events.length === 0 && isLoading && taskDetail) {
    if (!taskStatus) {
      taskStatus = taskDetail.status
    }
    // If there are traces in the detail, synthesize agent states
    if (taskDetail.traces && taskDetail.traces.length > 0 && agents.length === 0) {
      for (const trace of taskDetail.traces) {
        agents.push({
          type: trace.agent_type,
          status: 'completed',
          thinking: trace.reasoning || '',
          durationMs: trace.duration_ms ?? undefined,
          costUsd: trace.cost_usd,
          tokensUsed: trace.tokens_used,
        })
      }
    }
    // Show code if already generated
    if (taskDetail.final_code && !generatedCode) {
      generatedCode = taskDetail.final_code
    }
    // Show output if available
    if (taskDetail.final_output && terminal.lines.length === 0) {
      for (const line of taskDetail.final_output.split('\n')) {
        terminal.lines.push({ type: 'stdout', content: line })
      }
    }
  }

  if (events.length === 0 && !isLoading && !taskDetail) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-8">
        {/* Hero icon with layered glows */}
        <div className="relative mb-10 float">
          <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-primary via-purple-500 to-cyan-400 flex items-center justify-center shadow-2xl shadow-primary/20 border border-white/10">
            <Zap className="w-10 h-10 text-white drop-shadow-lg" />
          </div>
          <div className="absolute -inset-3 bg-gradient-to-br from-primary/15 to-cyan-400/15 rounded-[2rem] blur-2xl -z-10 breathe" />
          <div className="absolute -inset-8 bg-primary/[0.04] rounded-full blur-3xl -z-20" />
        </div>

        <h2 className="text-3xl font-bold tracking-tight mb-3 gradient-text">CodeForge</h2>
        <p className="text-muted-foreground/70 text-sm max-w-md leading-relaxed">
          AI-powered code generation with autonomous self-repair.
          <br />
          <span className="text-muted-foreground/40">Describe a task and watch it come to life.</span>
        </p>

        {/* Hint chips */}
        <div className="flex flex-wrap gap-2 mt-8 justify-center max-w-lg">
          {['Implement quicksort with tests', 'Build a REST API mock server', 'Create a data pipeline with error handling', 'Implement a thread-safe cache'].map((hint) => (
            <button
              key={hint}
              className="px-3.5 py-2 rounded-xl text-xs text-muted-foreground/70 bg-card/50 border border-border/30 hover:border-primary/30 hover:text-foreground hover:bg-primary/[0.05] hover:shadow-sm hover:shadow-primary/10 transition-all cursor-pointer"
              onClick={() => onHintClick?.(hint)}
            >
              {hint}
            </button>
          ))}
        </div>

        {/* Pipeline visualization */}
        <div className="flex items-center gap-1.5 mt-10">
          {[
            { label: 'Research', color: 'text-cyan-400/50' },
            { label: 'Classify', color: 'text-sky-400/50' },
            { label: 'Plan', color: 'text-blue-400/50' },
            { label: 'Code', color: 'text-purple-400/50' },
            { label: 'Execute', color: 'text-yellow-400/50' },
            { label: 'Self-Repair', color: 'text-orange-400/50' },
            { label: 'Done', color: 'text-emerald-400/50' },
          ].map((step, i, arr) => (
            <span key={step.label} className="flex items-center gap-1.5">
              <span className={`text-[10px] font-mono font-medium ${step.color}`}>{step.label}</span>
              {i < arr.length - 1 && (
                <span className="text-border/60 text-[10px]">&#x25B8;</span>
              )}
            </span>
          ))}
        </div>
      </div>
    )
  }

  const isProcessing = isLoading && !['completed', 'failed', 'cancelled', 'awaiting_approval', 'awaiting_answers'].includes(taskStatus)

  const stageLabels: Record<string, { label: string; icon: React.ReactNode }> = {
    classifying: { label: 'Analyzing task complexity...', icon: <Zap className="w-4 h-4 text-sky-400" /> },
    researching: { label: 'Deep research in progress...', icon: <Search className="w-4 h-4 text-cyan-400" /> },
    questioning: { label: 'Preparing clarification questions...', icon: <HelpCircle className="w-4 h-4 text-cyan-400" /> },
    awaiting_answers: { label: 'Waiting for your answers...', icon: <HelpCircle className="w-4 h-4 text-cyan-400" /> },
    planning: { label: 'Decomposing into subtasks...', icon: <Zap className="w-4 h-4 text-blue-400" /> },
    awaiting_approval: { label: 'Plan ready — review and approve', icon: <FileJson className="w-4 h-4 text-amber-400" /> },
    coding: { label: 'Generating code...', icon: <Code2 className="w-4 h-4 text-purple-400" /> },
    executing: { label: 'Running in sandbox...', icon: <Terminal className="w-4 h-4 text-yellow-400" /> },
    reviewing: { label: 'Analyzing output...', icon: <Wrench className="w-4 h-4 text-orange-400" /> },
    repairing: { label: 'Applying fix...', icon: <Wrench className="w-4 h-4 text-red-400" /> },
  }

  return (
    <div className="p-6 space-y-4 max-w-4xl mx-auto">
      {/* Status badge */}
      {taskStatus && (
        <div className="flex items-center gap-3">
          <StatusBadge status={taskStatus} />
          {taskStatus === 'completed' && (
            <span className="text-xs text-emerald-400/80 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> Task completed successfully
            </span>
          )}
          {taskStatus === 'failed' && (
            <span className="text-xs text-red-400/80 flex items-center gap-1">
              <XCircle className="w-3.5 h-3.5" /> Task failed
            </span>
          )}
          {taskStatus === 'awaiting_approval' && (
            <span className="text-xs text-amber-400/80 flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5" /> Review the plan below before execution
            </span>
          )}
        </div>
      )}

      {/* Agent Pipeline Visualization */}
      {(isLoading || taskStatus) && taskStatus !== '' && (
        <AgentFlowDiagram
          activeAgent={
            taskStatus === 'classifying' ? 'classify' :
            taskStatus === 'researching' ? 'researcher' :
            taskStatus === 'questioning' ? 'questioner' :
            taskStatus === 'awaiting_answers' ? 'questioner' :
            taskStatus === 'planning' ? 'planner' :
            taskStatus === 'coding' ? 'coder' :
            taskStatus === 'executing' ? 'executor' :
            taskStatus === 'reviewing' ? 'reviewer' :
            taskStatus === 'repairing' ? 'coder' :
            agents.length > 0 ? agents[agents.length - 1].type : null
          }
          status={taskStatus}
          retryCount={repairAttempts.length}
        />
      )}

      {/* Processing indicator */}
      {isProcessing && agents.length === 0 && taskStatus && (
        <div className="rounded-2xl border border-border/50 bg-card/50 backdrop-blur-sm p-4">
          <div className="flex items-center gap-3">
            {stageLabels[taskStatus]?.icon ?? <Zap className="w-4 h-4 text-primary" />}
            <div className="flex-1">
              <p className="text-sm font-medium">
                {stageLabels[taskStatus]?.label ?? 'Processing...'}
              </p>
            </div>
            <div className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="h-1.5 w-1.5 rounded-full bg-primary animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </div>
          </div>
          <div className="mt-3 h-1 rounded-full bg-muted overflow-hidden">
            <div className="h-full rounded-full bg-gradient-to-r from-primary to-purple-500 shimmer" style={{ width: '60%' }} />
          </div>
        </div>
      )}

      {/* Initial spinner */}
      {isLoading && !taskStatus && events.length === 0 && (
        <div className="rounded-2xl border border-border/50 bg-card/50 backdrop-blur-sm p-4">
          <div className="flex items-center gap-3">
            <div className="h-4 w-4 rounded-full border-2 border-primary border-t-transparent animate-spin" />
            <p className="text-sm font-medium">Initializing task...</p>
          </div>
        </div>
      )}

      {/* Execution Timeline */}
      {(() => {
        const timelinePhases = agents
          .filter(a => a.status === 'completed' && a.durationMs)
          .map(a => ({
            name: a.type.charAt(0).toUpperCase() + a.type.slice(1),
            durationMs: a.durationMs || 0,
            status: (a.status === 'error' ? 'error' : 'completed') as 'completed' | 'error',
            color: a.type === 'classifier' ? '#38bdf8' :
                   a.type === 'planner' ? '#3b82f6' :
                   a.type === 'coder' ? '#a855f7' :
                   a.type === 'executor' ? '#eab308' :
                   a.type === 'reviewer' ? '#f97316' : '#6366f1',
          }))
        return timelinePhases.length > 1 ? <ExecutionTimeline phases={timelinePhases} /> : null
      })()}

      {/* Research Findings */}
      {displayResearch && (
        <ResearchDisplay findings={displayResearch} />
      )}

      {/* Question Form */}
      {taskStatus === 'awaiting_answers' && displayQuestions.length > 0 && onSubmitAnswers && (
        <QuestionForm
          questions={displayQuestions}
          onSubmit={onSubmitAnswers}
          onSkip={onSkipQuestions || (() => {})}
        />
      )}

      {/* Agent cards */}
      {agents.map((agent, i) => (
        <AgentCard
          key={i}
          agentType={agent.type}
          status={agent.status}
          thinking={agent.thinking}
          durationMs={agent.durationMs}
          costUsd={agent.costUsd}
          tokensUsed={agent.tokensUsed}
        />
      ))}

      {/* Plan Approval Card */}
      {taskStatus === 'awaiting_approval' && displayPlan && (
        <div className="rounded-2xl border-2 border-amber-500/30 bg-amber-500/5 backdrop-blur-sm overflow-hidden">
          <div className="p-4 border-b border-amber-500/20">
            <div className="flex items-center gap-2 mb-1">
              <FileJson className="w-4 h-4 text-amber-400" />
              <h3 className="text-sm font-bold text-amber-300">Execution Plan</h3>
              <span className="text-[10px] bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full font-medium border border-amber-500/20">
                Hard Task
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              This task was classified as complex. Review the plan below and approve to start execution.
            </p>
          </div>

          {/* Subtasks */}
          {displayPlan.subtasks && displayPlan.subtasks.length > 0 && (
            <div className="p-4 space-y-2">
              {displayPlan.subtasks.map((subtask, i) => (
                <div
                  key={subtask.id ?? i}
                  className="flex items-start gap-3 py-2.5 px-3 rounded-xl bg-background/30 border border-border/20"
                >
                  <div className="flex items-center justify-center w-7 h-7 rounded-lg text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 shrink-0 mt-0.5">
                    {i + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-foreground">{subtask.description}</p>
                    <div className="flex items-center gap-2 mt-1">
                      {subtask.estimated_complexity && (
                        <span className={cn(
                          'text-[10px] px-1.5 py-0.5 rounded font-medium',
                          subtask.estimated_complexity === 'simple' && 'bg-emerald-500/10 text-emerald-400',
                          subtask.estimated_complexity === 'medium' && 'bg-yellow-500/10 text-yellow-400',
                          subtask.estimated_complexity === 'hard' && 'bg-red-500/10 text-red-400',
                        )}>
                          {subtask.estimated_complexity}
                        </span>
                      )}
                      {subtask.dependencies && subtask.dependencies.length > 0 && (
                        <span className="text-[10px] text-muted-foreground">
                          depends on: {subtask.dependencies.join(', ')}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Raw plan JSON if no subtasks */}
          {(!displayPlan.subtasks || displayPlan.subtasks.length === 0) && (
            <div className="p-4">
              <pre className="text-[11px] bg-background/50 rounded-xl p-3 overflow-auto max-h-48 font-mono text-muted-foreground leading-relaxed border border-border/20">
                {JSON.stringify(displayPlan, null, 2)}
              </pre>
            </div>
          )}

          {/* Action buttons */}
          {onApprove && (
            <div className="p-4 border-t border-amber-500/20 flex items-center gap-3">
              <Button
                onClick={onApprove}
                size="sm"
                className="gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-500/20"
              >
                <Check className="w-4 h-4" />
                Approve & Execute
              </Button>
              {onReject && (
                <Button
                  onClick={onReject}
                  variant="outline"
                  size="sm"
                  className="gap-2 rounded-xl border-red-500/30 text-red-400 hover:bg-red-500/10 hover:text-red-300"
                >
                  <X className="w-4 h-4" />
                  Cancel
                </Button>
              )}
              <p className="text-[10px] text-muted-foreground ml-auto">
                Approving will start code generation and execution
              </p>
            </div>
          )}
        </div>
      )}

      {/* Generated code */}
      {generatedCode && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Code2 className="w-3.5 h-3.5 text-purple-400" />
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Generated Code</p>
          </div>
          <CodeBlock code={generatedCode} />
        </div>
      )}

      {/* Terminal output */}
      {terminal.lines.length > 0 ? (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Terminal className="w-3.5 h-3.5 text-yellow-400" />
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Execution Output</p>
          </div>
          <TerminalOutput
            lines={terminal.lines}
            exitCode={terminal.exitCode}
            executionTime={terminal.executionTime}
            memoryUsage={terminal.memoryUsage}
          />
        </div>
      ) : taskDetail?.final_output ? (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Terminal className="w-3.5 h-3.5 text-yellow-400" />
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Execution Output</p>
          </div>
          <TerminalOutput
            lines={taskDetail.final_output.split('\n').map(l => ({ type: 'stdout' as const, content: l }))}
            exitCode={0}
          />
        </div>
      ) : null}

      {/* Repair attempts */}
      {repairAttempts.length > 0 && <RepairDiff attempts={repairAttempts} />}

      {/* Self-repair success indicator */}
      {repairAttempts.length > 0 && taskStatus === 'completed' && (
        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <p className="text-xs font-semibold text-emerald-400">Self-Repair Successful</p>
            <p className="text-[11px] text-muted-foreground">
              Fixed after {repairAttempts.length} repair {repairAttempts.length === 1 ? 'cycle' : 'cycles'} &mdash;
              AI debugged its own code automatically
            </p>
          </div>
        </div>
      )}

      {/* Final code */}
      {finalCode && finalCode !== generatedCode && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <p className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Final Code (After Repair)</p>
          </div>
          <CodeBlock code={finalCode} />
        </div>
      )}

      {/* Error */}
      {taskError && (
        <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-4">
          <div className="flex items-center gap-2 mb-2">
            <XCircle className="w-4 h-4 text-red-400" />
            <p className="text-sm text-red-400 font-semibold">Task Failed</p>
          </div>
          <p className="text-xs text-red-300/80 font-mono leading-relaxed">{taskError}</p>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
