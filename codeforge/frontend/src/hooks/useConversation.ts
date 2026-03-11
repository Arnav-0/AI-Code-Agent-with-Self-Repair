'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import {
  createConversation as apiCreateConversation,
  getConversation as apiGetConversation,
  sendMessage as apiSendMessage,
  stopAgent as apiStopAgent,
} from '@/lib/api'
import { buildConversationWsUrl } from '@/lib/ws'
import type { ConversationMessage, AgentStreamEvent, AgentEventType } from '@/lib/types'

const AGENT_TERMINAL_EVENTS = new Set<AgentEventType>(['agent.done', 'agent.error'])

interface UseConversationReturn {
  messages: ConversationMessage[]
  streamingContent: string
  currentAgent: string | null
  isAgentRunning: boolean
  sendMessage: (content: string) => Promise<void>
  stopAgent: () => Promise<void>
  createConversation: (title?: string) => Promise<string>
  loadConversation: (id: string) => Promise<void>
  conversationId: string | null
  error: string | null
  connected: boolean
}

export function useConversation(): UseConversationReturn {
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ConversationMessage[]>([])
  const [streamingContent, setStreamingContent] = useState('')
  const [currentAgent, setCurrentAgent] = useState<string | null>(null)
  const [isAgentRunning, setIsAgentRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [connected, setConnected] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef(0)
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const streamBufferRef = useRef('')
  const maxRetries = 5

  // Process incoming agent stream events
  const handleStreamEvent = useCallback((event: AgentStreamEvent) => {
    switch (event.event) {
      case 'agent.switch': {
        const role = String(event.data.to ?? event.data.agent_role ?? event.data.role ?? '')
        setCurrentAgent(role)
        break
      }

      case 'agent.thinking': {
        const thought = String(event.data.content ?? event.data.text ?? event.data.chunk ?? '')
        if (thought) {
          streamBufferRef.current += thought
          setStreamingContent(streamBufferRef.current)
        }
        break
      }

      case 'agent.text': {
        const text = String(event.data.content ?? event.data.text ?? event.data.chunk ?? '')
        if (text) {
          streamBufferRef.current += text
          setStreamingContent(streamBufferRef.current)
        }
        break
      }

      case 'tool.call': {
        const tcId = String(event.data.id ?? event.data.call_id ?? `tool-call-${Date.now()}`)
        const toolMsg: ConversationMessage = {
          id: tcId,
          conversation_id: '',
          role: 'assistant',
          content: null,
          tool_calls: [{
            id: tcId,
            name: String(event.data.name ?? event.data.tool_name ?? ''),
            arguments: (event.data.arguments as Record<string, unknown>) ?? {},
          }],
          tool_call_id: null,
          tool_name: null,
          agent_role: currentAgent,
          tokens_used: 0,
          cost_usd: 0,
          created_at: new Date().toISOString(),
        }
        setMessages(prev => [...prev, toolMsg])
        break
      }

      case 'tool.result': {
        const trId = String(event.data.id ?? event.data.call_id ?? `tool-result-${Date.now()}`)
        const resultMsg: ConversationMessage = {
          id: `result-${trId}`,
          conversation_id: '',
          role: 'tool',
          content: String(event.data.output ?? event.data.result ?? ''),
          tool_calls: null,
          tool_call_id: trId,
          tool_name: String(event.data.name ?? event.data.tool_name ?? ''),
          agent_role: currentAgent,
          tokens_used: 0,
          cost_usd: 0,
          created_at: new Date().toISOString(),
        }
        setMessages(prev => [...prev, resultMsg])
        break
      }

      case 'agent.done': {
        // Flush any remaining streaming content as an assistant message
        if (streamBufferRef.current.trim()) {
          const assistantMsg: ConversationMessage = {
            id: `assistant-${Date.now()}`,
            conversation_id: '',
            role: 'assistant',
            content: streamBufferRef.current,
            tool_calls: null,
            tool_call_id: null,
            tool_name: null,
            agent_role: currentAgent,
            tokens_used: Number(event.data.total_tokens ?? event.data.tokens_used ?? 0),
            cost_usd: Number(event.data.cost_usd ?? 0),
            created_at: new Date().toISOString(),
          }
          setMessages(prev => [...prev, assistantMsg])
        }
        streamBufferRef.current = ''
        setStreamingContent('')
        setIsAgentRunning(false)
        setCurrentAgent(null)
        break
      }

      case 'agent.error': {
        const errText = String(event.data.error ?? event.data.message ?? 'Unknown error')
        setError(errText)
        // Flush buffer as error message
        if (streamBufferRef.current.trim()) {
          const assistantMsg: ConversationMessage = {
            id: `assistant-err-${Date.now()}`,
            conversation_id: '',
            role: 'assistant',
            content: streamBufferRef.current,
            tool_calls: null,
            tool_call_id: null,
            tool_name: null,
            agent_role: currentAgent,
            tokens_used: 0,
            cost_usd: 0,
            created_at: new Date().toISOString(),
          }
          setMessages(prev => [...prev, assistantMsg])
        }
        streamBufferRef.current = ''
        setStreamingContent('')
        setIsAgentRunning(false)
        break
      }
    }
  }, [currentAgent])

  // WebSocket connection management
  useEffect(() => {
    if (!conversationId) {
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

    retryRef.current = 0

    function connect(id: string) {
      if (wsRef.current) {
        wsRef.current.close()
      }

      try {
        const ws = new WebSocket(buildConversationWsUrl(id))
        wsRef.current = ws

        ws.onopen = () => {
          setConnected(true)
          setError(null)
          retryRef.current = 0
        }

        ws.onmessage = (ev) => {
          try {
            const event = JSON.parse(ev.data as string) as AgentStreamEvent
            handleStreamEvent(event)
          } catch {
            // ignore parse errors or pings
          }
        }

        ws.onerror = () => {
          setError('WebSocket connection error')
          setConnected(false)
        }

        ws.onclose = () => {
          setConnected(false)
          wsRef.current = null

          if (retryRef.current < maxRetries) {
            const delay = Math.min(1000 * 2 ** retryRef.current, 10000)
            retryRef.current += 1
            retryTimeoutRef.current = setTimeout(() => connect(id), delay)
          }
        }
      } catch (err) {
        setError(String(err))
      }
    }

    connect(conversationId)

    return () => {
      if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current)
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [conversationId, handleStreamEvent])

  const createConversation = useCallback(async (title?: string): Promise<string> => {
    setError(null)
    try {
      const convo = await apiCreateConversation(title)
      setConversationId(convo.id)
      setMessages([])
      setStreamingContent('')
      streamBufferRef.current = ''
      setCurrentAgent(null)
      setIsAgentRunning(false)
      return convo.id
    } catch (err) {
      setError(String(err))
      throw err
    }
  }, [])

  const loadConversation = useCallback(async (id: string): Promise<void> => {
    setError(null)
    try {
      const detail = await apiGetConversation(id)
      setConversationId(detail.id)
      setMessages(detail.messages)
      setStreamingContent('')
      streamBufferRef.current = ''
      setCurrentAgent(null)
      setIsAgentRunning(detail.status === 'active')
    } catch (err) {
      setError(String(err))
    }
  }, [])

  const sendMessage = useCallback(async (content: string): Promise<void> => {
    if (!conversationId) {
      // Auto-create conversation if none exists
      try {
        const id = await createConversation()
        // Optimistically add user message
        const userMsg: ConversationMessage = {
          id: `user-${Date.now()}`,
          conversation_id: id,
          role: 'user',
          content,
          tool_calls: null,
          tool_call_id: null,
          tool_name: null,
          agent_role: null,
          tokens_used: 0,
          cost_usd: 0,
          created_at: new Date().toISOString(),
        }
        setMessages(prev => [...prev, userMsg])
        setIsAgentRunning(true)
        streamBufferRef.current = ''
        setStreamingContent('')
        setError(null)
        await apiSendMessage(id, content)
      } catch (err) {
        setError(String(err))
        setIsAgentRunning(false)
      }
      return
    }

    // Optimistically add user message
    const userMsg: ConversationMessage = {
      id: `user-${Date.now()}`,
      conversation_id: conversationId,
      role: 'user',
      content,
      tool_calls: null,
      tool_call_id: null,
      tool_name: null,
      agent_role: null,
      tokens_used: 0,
      cost_usd: 0,
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])
    setIsAgentRunning(true)
    streamBufferRef.current = ''
    setStreamingContent('')
    setError(null)

    try {
      await apiSendMessage(conversationId, content)
    } catch (err) {
      setError(String(err))
      setIsAgentRunning(false)
    }
  }, [conversationId, createConversation])

  const stopAgent = useCallback(async (): Promise<void> => {
    if (!conversationId) return
    try {
      await apiStopAgent(conversationId)
      setIsAgentRunning(false)
      // Flush any partial streaming content
      if (streamBufferRef.current.trim()) {
        const partialMsg: ConversationMessage = {
          id: `assistant-partial-${Date.now()}`,
          conversation_id: conversationId,
          role: 'assistant',
          content: streamBufferRef.current + '\n\n[Stopped]',
          tool_calls: null,
          tool_call_id: null,
          tool_name: null,
          agent_role: currentAgent,
          tokens_used: 0,
          cost_usd: 0,
          created_at: new Date().toISOString(),
        }
        setMessages(prev => [...prev, partialMsg])
      }
      streamBufferRef.current = ''
      setStreamingContent('')
    } catch {
      // Agent may already be stopped
      setIsAgentRunning(false)
    }
  }, [conversationId, currentAgent])

  return {
    messages,
    streamingContent,
    currentAgent,
    isAgentRunning,
    sendMessage,
    stopAgent,
    createConversation,
    loadConversation,
    conversationId,
    error,
    connected,
  }
}
