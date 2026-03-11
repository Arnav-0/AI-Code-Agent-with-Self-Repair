'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { createTask, getTask, cancelTask as apiCancelTask, approveTask as apiApproveTask, submitAnswers as apiSubmitAnswers } from '@/lib/api'
import { useWebSocket } from './useWebSocket'
import type { TaskDetail, WSEvent, ResearchFindings, ResearchQuestion } from '@/lib/types'

const TERMINAL_STATUSES = new Set(['completed', 'failed', 'cancelled'])
const POLL_INTERVAL_MS = 2000

interface PlanData {
  subtasks?: Array<{ id: number; description: string; dependencies?: number[]; estimated_complexity?: string }>
  [key: string]: unknown
}

interface UseTaskReturn {
  submitTask: (prompt: string, contextCode?: string) => Promise<void>
  cancelTask: () => Promise<void>
  approveTask: () => Promise<void>
  submitAnswers: (answers: Record<string, string>) => Promise<void>
  skipQuestions: () => Promise<void>
  currentTaskId: string | null
  taskDetail: TaskDetail | null
  isLoading: boolean
  error: string | null
  events: WSEvent[]
  connected: boolean
  reset: () => void
  awaitingApproval: boolean
  awaitingAnswers: boolean
  planData: PlanData | null
  researchFindings: ResearchFindings | null
  questions: ResearchQuestion[]
}

export function useTask(): UseTaskReturn {
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null)
  const [taskDetail, setTaskDetail] = useState<TaskDetail | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pollEvents, setPollEvents] = useState<WSEvent[]>([])
  const [awaitingApproval, setAwaitingApproval] = useState(false)
  const [awaitingAnswers, setAwaitingAnswers] = useState(false)
  const [planData, setPlanData] = useState<PlanData | null>(null)
  const [researchFindings, setResearchFindings] = useState<ResearchFindings | null>(null)
  const [questions, setQuestions] = useState<ResearchQuestion[]>([])
  const finishedRef = useRef(false)
  const lastPollStatusRef = useRef<string>('')

  const { connected, events: wsEvents, lastEvent, clearEvents: clearWsEvents, sendEvent } = useWebSocket(currentTaskId)

  // Merge WS events with poll-synthesized events
  const events = wsEvents.length > 0 ? wsEvents : pollEvents

  // Handle terminal events, plan.ready, research, and questions from WebSocket
  useEffect(() => {
    if (!lastEvent || !currentTaskId) return
    const ev = lastEvent.event
    if (ev === 'task.completed' || ev === 'task.failed' || ev === 'task.cancelled') {
      finishedRef.current = true
      setAwaitingApproval(false)
      setAwaitingAnswers(false)
      getTask(currentTaskId)
        .then(setTaskDetail)
        .catch(() => null)
        .finally(() => setIsLoading(false))
    }
    if (ev === 'plan.ready') {
      const data = lastEvent.data as Record<string, unknown>
      setPlanData((data.plan as PlanData) || null)
      setAwaitingApproval(true)
    }
    if (ev === 'research.complete') {
      const data = lastEvent.data as Record<string, unknown>
      setResearchFindings((data.findings as ResearchFindings) || null)
    }
    if (ev === 'questions.ready') {
      const data = lastEvent.data as Record<string, unknown>
      setQuestions((data.questions as ResearchQuestion[]) || [])
      setAwaitingAnswers(true)
    }
    if (ev === 'answers.received') {
      setAwaitingAnswers(false)
      setQuestions([])
    }
    if (ev === 'task.status_changed') {
      const data = lastEvent.data as Record<string, unknown>
      if (data.status === 'awaiting_approval') {
        setAwaitingApproval(true)
        // Fetch task to get plan data if not already received
        if (!planData) {
          getTask(currentTaskId).then((t) => {
            if (t.plan) {
              const { _meta, _research, _questions, ...rest } = t.plan as PlanData & { _meta?: unknown; _research?: unknown; _questions?: unknown }
              if (_research) setResearchFindings(_research as ResearchFindings)
              if (_questions) setQuestions(_questions as ResearchQuestion[])
              setPlanData(rest)
            }
          }).catch(() => null)
        }
      }
      if (data.status === 'awaiting_answers') {
        setAwaitingAnswers(true)
        // Fetch task to get research data
        getTask(currentTaskId).then((t) => {
          if (t.plan) {
            const planObj = t.plan as Record<string, unknown>
            if (planObj._research) setResearchFindings(planObj._research as ResearchFindings)
            if (planObj._questions) setQuestions(planObj._questions as ResearchQuestion[])
          }
        }).catch(() => null)
      }
      if (data.status === 'coding' || data.status === 'executing') {
        setAwaitingApproval(false)
        setAwaitingAnswers(false)
      }
    }
  }, [lastEvent, currentTaskId, planData])

  // Polling: detect intermediate AND terminal status changes via REST API
  useEffect(() => {
    if (!currentTaskId || !isLoading) return

    const poll = async () => {
      if (finishedRef.current) return
      try {
        const task = await getTask(currentTaskId)

        // Synthesize status events when WS isn't delivering them
        if (task.status !== lastPollStatusRef.current && task.status !== 'pending') {
          lastPollStatusRef.current = task.status
          const syntheticEvent: WSEvent = {
            event: 'task.status_changed',
            timestamp: new Date().toISOString(),
            data: { status: task.status },
          }
          setPollEvents(prev => [...prev, syntheticEvent])

          // Detect awaiting_approval from polling
          if (task.status === 'awaiting_approval') {
            setAwaitingApproval(true)
            if (task.plan) {
              const { _meta, _research, _questions, ...rest } = task.plan as PlanData & { _meta?: unknown; _research?: unknown; _questions?: unknown }
              if (_research) setResearchFindings(_research as ResearchFindings)
              if (_questions) setQuestions(_questions as ResearchQuestion[])
              setPlanData(rest)
            }
          }

          // Detect awaiting_answers from polling
          if (task.status === 'awaiting_answers') {
            setAwaitingAnswers(true)
            if (task.plan) {
              const planObj = task.plan as Record<string, unknown>
              if (planObj._research) setResearchFindings(planObj._research as ResearchFindings)
              if (planObj._questions) setQuestions(planObj._questions as ResearchQuestion[])
            }
          }
        }

        if (TERMINAL_STATUSES.has(task.status)) {
          finishedRef.current = true
          setTaskDetail(task)
          setIsLoading(false)
        }
      } catch {
        // ignore polling errors
      }
    }

    const interval = setInterval(poll, POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [currentTaskId, isLoading])

  const clearEvents = useCallback(() => {
    clearWsEvents()
    setPollEvents([])
    lastPollStatusRef.current = ''
  }, [clearWsEvents])

  const submitTask = useCallback(async (prompt: string, contextCode?: string) => {
    setIsLoading(true)
    setError(null)
    setTaskDetail(null)
    setAwaitingApproval(false)
    setAwaitingAnswers(false)
    setPlanData(null)
    setResearchFindings(null)
    setQuestions([])
    finishedRef.current = false
    clearEvents()
    try {
      const task = await createTask(prompt, contextCode)
      setCurrentTaskId(task.id)
    } catch (err) {
      setError(String(err))
      setIsLoading(false)
    }
  }, [clearEvents])

  const cancelTask = useCallback(async () => {
    if (!currentTaskId) return
    try {
      await apiCancelTask(currentTaskId)
    } catch {
      // Task may already be done
    } finally {
      setIsLoading(false)
      setAwaitingApproval(false)
      setAwaitingAnswers(false)
    }
  }, [currentTaskId])

  const approveTask = useCallback(async () => {
    if (!currentTaskId) return
    try {
      await apiApproveTask(currentTaskId)
      setAwaitingApproval(false)
      // Task continues — still loading
    } catch (err) {
      setError(String(err))
    }
  }, [currentTaskId])

  const submitAnswersHandler = useCallback(async (answers: Record<string, string>) => {
    if (!currentTaskId) return
    try {
      // Send via WebSocket for real-time handling
      sendEvent('answers.submit', { answers })
      // Also send via REST as fallback
      await apiSubmitAnswers(currentTaskId, answers)
      setAwaitingAnswers(false)
      setQuestions([])
    } catch (err) {
      setError(String(err))
    }
  }, [currentTaskId, sendEvent])

  const skipQuestions = useCallback(async () => {
    if (!currentTaskId || questions.length === 0) return
    // Submit with default answers
    const defaults: Record<string, string> = {}
    for (const q of questions) {
      defaults[String(q.id)] = q.default_answer || ''
    }
    await submitAnswersHandler(defaults)
  }, [currentTaskId, questions, submitAnswersHandler])

  const reset = useCallback(() => {
    setCurrentTaskId(null)
    setTaskDetail(null)
    setIsLoading(false)
    setError(null)
    setAwaitingApproval(false)
    setAwaitingAnswers(false)
    setPlanData(null)
    setResearchFindings(null)
    setQuestions([])
    finishedRef.current = false
    clearEvents()
  }, [clearEvents])

  return {
    submitTask, cancelTask, approveTask, submitAnswers: submitAnswersHandler,
    skipQuestions, currentTaskId, taskDetail, isLoading, error, events,
    connected, reset, awaitingApproval, awaitingAnswers, planData,
    researchFindings, questions,
  }
}
