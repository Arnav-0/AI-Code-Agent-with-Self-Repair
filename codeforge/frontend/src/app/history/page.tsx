'use client'

import { useCallback, useEffect, useState } from 'react'
import { getHistory, getTask } from '@/lib/api'
import { FilterBar } from '@/components/history/FilterBar'
import { TaskList } from '@/components/history/TaskList'
import { TaskDetail } from '@/components/history/TaskDetail'
import { TaskStream } from '@/components/chat/TaskStream'
import { useWebSocket } from '@/hooks/useWebSocket'
import { Inbox } from 'lucide-react'
import type { HistoryParams, Task, TaskDetail as TaskDetailType } from '@/lib/types'

const TERMINAL_STATUSES = new Set(['completed', 'failed', 'cancelled'])
const LIVE_POLL_MS = 3000

export default function HistoryPage() {
  const [params, setParams] = useState<HistoryParams>({
    sort_by: 'created_at',
    order: 'desc',
    per_page: 20,
    page: 1,
  })
  const [tasks, setTasks] = useState<Task[]>([])
  const [total, setTotal] = useState(0)
  const [selectedTask, setSelectedTask] = useState<TaskDetailType | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  // WebSocket for live task streaming
  const isLive = selectedTask != null && !TERMINAL_STATUSES.has(selectedTask.status)
  const wsTaskId = isLive ? selectedId : null
  const { events: wsEvents, clearEvents } = useWebSocket(wsTaskId)

  useEffect(() => {
    getHistory(params)
      .then((res) => {
        setTasks(res.items)
        setTotal(res.total)
      })
      .catch(() => null)
  }, [params])

  // Poll for updates on live tasks
  useEffect(() => {
    if (!selectedTask || !selectedId) return
    if (TERMINAL_STATUSES.has(selectedTask.status)) return

    const interval = setInterval(async () => {
      try {
        const updated = await getTask(selectedId)
        setSelectedTask(updated)
        if (TERMINAL_STATUSES.has(updated.status)) {
          // Refresh the list to update status badges
          getHistory(params).then((res) => {
            setTasks(res.items)
            setTotal(res.total)
          }).catch(() => null)
        }
      } catch { /* ignore */ }
    }, LIVE_POLL_MS)

    return () => clearInterval(interval)
  }, [selectedTask, selectedId, params])

  // Also periodically refresh the task list to pick up new tasks and status changes
  useEffect(() => {
    const hasLiveTasks = tasks.some(t => !TERMINAL_STATUSES.has(t.status))
    if (!hasLiveTasks) return

    const interval = setInterval(() => {
      getHistory(params).then((res) => {
        setTasks(res.items)
        setTotal(res.total)
      }).catch(() => null)
    }, LIVE_POLL_MS)

    return () => clearInterval(interval)
  }, [tasks, params])

  const handleSelect = useCallback(async (task: Task) => {
    setSelectedId(task.id)
    clearEvents()
    try {
      const detail = await getTask(task.id)
      setSelectedTask(detail)
    } catch {
      setSelectedTask(null)
    }
  }, [clearEvents])

  return (
    <div className="flex h-full">
      {/* Left panel - list */}
      <div className="w-[380px] min-w-[320px] border-r border-border/20 flex flex-col bg-card/10">
        <FilterBar params={params} onChange={setParams} />
        <div className="flex-1 overflow-hidden">
          <TaskList
            tasks={tasks}
            selectedId={selectedId}
            onSelect={handleSelect}
            total={total}
            page={params.page ?? 1}
            perPage={params.per_page ?? 20}
            onPageChange={(p) => setParams((prev) => ({ ...prev, page: p }))}
          />
        </div>
      </div>

      {/* Right panel */}
      <div className="flex-1 overflow-auto">
        {selectedTask ? (
          isLive ? (
            /* Live task — show real-time streaming view */
            <div className="flex flex-col h-full">
              {/* Task prompt header */}
              <div className="px-5 py-4 border-b border-border/30 bg-card/30">
                <p className="text-sm text-foreground leading-relaxed">{selectedTask.prompt}</p>
                <div className="flex items-center gap-2 mt-2 text-[10px] text-muted-foreground">
                  {selectedTask.complexity && (
                    <span className="bg-muted/50 px-1.5 py-0.5 rounded">{selectedTask.complexity}</span>
                  )}
                  {selectedTask.model_used && (
                    <span className="bg-muted/50 px-1.5 py-0.5 rounded">{selectedTask.model_used}</span>
                  )}
                </div>
              </div>
              {/* Live stream */}
              <div className="flex-1 overflow-auto">
                <TaskStream
                  events={wsEvents}
                  isLoading={true}
                  taskDetail={selectedTask}
                />
              </div>
            </div>
          ) : (
            /* Completed/failed task — show full detail view */
            <TaskDetail task={selectedTask} />
          )
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center px-8">
            <div className="relative mb-6 float">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 via-purple-500/15 to-cyan-400/15 flex items-center justify-center border border-primary/10 shadow-lg shadow-primary/5">
                <Inbox className="w-7 h-7 text-muted-foreground/60" />
              </div>
              <div className="absolute -inset-4 bg-primary/[0.04] rounded-[2rem] blur-2xl -z-10 breathe" />
            </div>
            <p className="text-sm font-medium text-muted-foreground/80 mb-1">No task selected</p>
            <p className="text-[11px] text-muted-foreground/40 font-mono">
              Select a task to inspect agent traces and code
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
