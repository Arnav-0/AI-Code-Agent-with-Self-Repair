'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { buildTaskWsUrl } from '@/lib/ws'
import type { WSEvent } from '@/lib/types'

const TERMINAL_EVENTS = new Set(['task.completed', 'task.failed', 'task.cancelled'])

interface UseWebSocketReturn {
  connected: boolean
  events: WSEvent[]
  lastEvent: WSEvent | null
  error: string | null
  clearEvents: () => void
  sendEvent: (event: string, data?: Record<string, unknown>) => void
}

export function useWebSocket(taskId: string | null): UseWebSocketReturn {
  const [connected, setConnected] = useState(false)
  const [events, setEvents] = useState<WSEvent[]>([])
  const [lastEvent, setLastEvent] = useState<WSEvent | null>(null)
  const [error, setError] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef(0)
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const doneRef = useRef(false)
  const maxRetries = 3

  const clearEvents = useCallback(() => {
    setEvents([])
    setLastEvent(null)
    doneRef.current = false
  }, [])

  const sendEvent = useCallback((event: string, data?: Record<string, unknown>) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ event, ...(data || {}) }))
    }
  }, [])

  useEffect(() => {
    if (!taskId) {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current)
      }
      setConnected(false)
      return
    }

    doneRef.current = false
    retryRef.current = 0

    function connect(id: string) {
      if (wsRef.current) {
        wsRef.current.close()
      }

      try {
        const ws = new WebSocket(buildTaskWsUrl(id))
        wsRef.current = ws

        ws.onopen = () => {
          setConnected(true)
          setError(null)
          retryRef.current = 0
        }

        ws.onmessage = (ev) => {
          try {
            const event = JSON.parse(ev.data as string) as WSEvent
            setEvents((prev) => [...prev, event])
            setLastEvent(event)
            if (TERMINAL_EVENTS.has(event.event)) {
              doneRef.current = true
            }
          } catch {
            // ignore parse errors
          }
        }

        ws.onerror = () => {
          setError('WebSocket error')
          setConnected(false)
        }

        ws.onclose = () => {
          setConnected(false)
          wsRef.current = null

          if (!doneRef.current && retryRef.current < maxRetries) {
            const delay = Math.min(1000 * 2 ** retryRef.current, 8000)
            retryRef.current += 1
            retryTimeoutRef.current = setTimeout(() => connect(id), delay)
          }
        }
      } catch (err) {
        setError(String(err))
      }
    }

    connect(taskId)

    return () => {
      if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current)
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [taskId])

  return { connected, events, lastEvent, error, clearEvents, sendEvent }
}
