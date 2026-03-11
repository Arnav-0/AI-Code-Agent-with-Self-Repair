'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Bot,
  CircleStop,
  ArrowUp,
  Sparkles,
  Wifi,
  WifiOff,
  Coins,
  Hash,
  Loader2,
  Plus,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useConversation } from '@/hooks/useConversation'
import { MessageBubble, StreamingBubble } from '@/components/chat/MessageBubble'
import { Button } from '@/components/ui/button'

const AGENT_ROLE_STYLES: Record<string, { label: string; color: string; bgColor: string }> = {
  explorer: { label: 'Explorer', color: 'text-cyan-400', bgColor: 'bg-cyan-400/10 border-cyan-400/20' },
  coder: { label: 'Coder', color: 'text-purple-400', bgColor: 'bg-purple-400/10 border-purple-400/20' },
  tester: { label: 'Tester', color: 'text-yellow-400', bgColor: 'bg-yellow-400/10 border-yellow-400/20' },
  reviewer: { label: 'Reviewer', color: 'text-orange-400', bgColor: 'bg-orange-400/10 border-orange-400/20' },
  main: { label: 'Main', color: 'text-violet-400', bgColor: 'bg-violet-400/10 border-violet-400/20' },
  planner: { label: 'Planner', color: 'text-blue-400', bgColor: 'bg-blue-400/10 border-blue-400/20' },
  orchestrator: { label: 'Orchestrator', color: 'text-indigo-400', bgColor: 'bg-indigo-400/10 border-indigo-400/20' },
}

function getAgentStyle(role: string | null) {
  if (!role) return AGENT_ROLE_STYLES.main
  return AGENT_ROLE_STYLES[role.toLowerCase()] ?? {
    label: role.charAt(0).toUpperCase() + role.slice(1),
    color: 'text-violet-400',
    bgColor: 'bg-violet-400/10 border-violet-400/20',
  }
}

const EXAMPLE_PROMPTS = [
  'Read the main config file and summarize its settings',
  'Find all TODO comments in the codebase',
  'Create a Python utility for parsing CSV files',
  'Review the error handling in the API routes',
  'Write unit tests for the authentication module',
  'Refactor the database queries to use async/await',
]

export function ConversationView() {
  const {
    messages,
    streamingContent,
    currentAgent,
    isAgentRunning,
    sendMessage,
    stopAgent,
    createConversation,
    conversationId,
    error,
    connected,
  } = useConversation()

  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom on new messages or streaming content
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  // Auto-resize textarea
  const adjustTextareaHeight = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    const lineHeight = 24
    const maxHeight = lineHeight * 6
    el.style.height = `${Math.min(Math.max(el.scrollHeight, lineHeight), maxHeight)}px`
  }, [])

  useEffect(() => {
    adjustTextareaHeight()
  }, [inputValue, adjustTextareaHeight])

  const handleSubmit = useCallback(async () => {
    const content = inputValue.trim()
    if (!content || isAgentRunning) return
    setInputValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
    await sendMessage(content)
  }, [inputValue, isAgentRunning, sendMessage])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSubmit()
      }
    },
    [handleSubmit]
  )

  const handleHintClick = useCallback(async (prompt: string) => {
    await sendMessage(prompt)
  }, [sendMessage])

  const handleNewConversation = useCallback(async () => {
    await createConversation()
  }, [createConversation])

  // Compute totals from messages
  const totalTokens = messages.reduce((sum, m) => sum + (m.tokens_used ?? 0), 0)
  const totalCost = messages.reduce((sum, m) => sum + (m.cost_usd ?? 0), 0)

  const agentStyle = getAgentStyle(currentAgent)

  const isEmpty = messages.length === 0 && !streamingContent && !isAgentRunning

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-background to-background/95">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-border/20 bg-background/50 backdrop-blur-lg shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-xl bg-gradient-to-br from-violet-500/20 to-indigo-500/20 border border-violet-500/15">
            <Bot className="w-4 h-4 text-violet-400" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-foreground">Agent</h1>
            <div className="flex items-center gap-2 mt-0.5">
              {isAgentRunning && currentAgent && (
                <span className={cn(
                  'inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded-md border',
                  agentStyle.bgColor, agentStyle.color,
                )}>
                  <Sparkles className="w-2.5 h-2.5" />
                  {agentStyle.label}
                </span>
              )}
              {isAgentRunning && !currentAgent && (
                <span className="inline-flex items-center gap-1 text-[10px] font-medium text-violet-400/60">
                  <Loader2 className="w-2.5 h-2.5 animate-spin" />
                  Processing...
                </span>
              )}
              {!isAgentRunning && conversationId && (
                <span className="text-[10px] text-muted-foreground/50">Ready</span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Token & cost counters */}
          {totalTokens > 0 && (
            <div className="flex items-center gap-3 text-[10px] text-muted-foreground/50 font-mono">
              <span className="flex items-center gap-1">
                <Hash className="w-3 h-3" />
                {totalTokens.toLocaleString()} tokens
              </span>
              <span className="flex items-center gap-1">
                <Coins className="w-3 h-3" />
                ${totalCost.toFixed(4)}
              </span>
            </div>
          )}

          {/* Connection status */}
          <div className={cn(
            'flex items-center gap-1 text-[10px] font-mono',
            connected ? 'text-emerald-400/60' : 'text-muted-foreground/30',
          )}>
            {connected ? (
              <Wifi className="w-3 h-3" />
            ) : (
              <WifiOff className="w-3 h-3" />
            )}
          </div>

          {/* New conversation button */}
          {conversationId && (
            <Button
              variant="outline"
              size="sm"
              className="gap-1 rounded-lg text-muted-foreground/70"
              onClick={handleNewConversation}
            >
              <Plus className="w-3 h-3" />
              New
            </Button>
          )}
        </div>
      </div>

      {/* Messages area */}
      <div ref={scrollContainerRef} className="flex-1 overflow-y-auto">
        {isEmpty ? (
          /* Empty state / welcome */
          <div className="flex flex-col items-center justify-center h-full text-center px-8">
            {/* Hero icon */}
            <div className="relative mb-10 float">
              <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-violet-500 via-indigo-500 to-purple-600 flex items-center justify-center shadow-2xl shadow-violet-500/20 border border-white/10">
                <Bot className="w-10 h-10 text-white drop-shadow-lg" />
              </div>
              <div className="absolute -inset-3 bg-gradient-to-br from-violet-500/15 to-indigo-400/15 rounded-[2rem] blur-2xl -z-10 breathe" />
              <div className="absolute -inset-8 bg-violet-500/[0.04] rounded-full blur-3xl -z-20" />
            </div>

            <h2 className="text-3xl font-bold tracking-tight mb-3 gradient-text">CodeForge Agent</h2>
            <p className="text-muted-foreground/70 text-sm max-w-md leading-relaxed">
              An AI coding agent that explores, writes, tests, and reviews code.
              <br />
              <span className="text-muted-foreground/40">Ask anything about your codebase or request changes.</span>
            </p>

            {/* Example prompts */}
            <div className="flex flex-wrap gap-2 mt-8 justify-center max-w-xl">
              {EXAMPLE_PROMPTS.map((hint) => (
                <button
                  key={hint}
                  className="px-3.5 py-2 rounded-xl text-xs text-muted-foreground/70 bg-card/50 border border-border/30 hover:border-violet-500/30 hover:text-foreground hover:bg-violet-500/[0.05] hover:shadow-sm hover:shadow-violet-500/10 transition-all cursor-pointer"
                  onClick={() => handleHintClick(hint)}
                >
                  {hint}
                </button>
              ))}
            </div>

            {/* Agent roles visualization */}
            <div className="flex items-center gap-1.5 mt-10">
              {[
                { label: 'Explore', color: 'text-cyan-400/50' },
                { label: 'Plan', color: 'text-blue-400/50' },
                { label: 'Code', color: 'text-purple-400/50' },
                { label: 'Test', color: 'text-yellow-400/50' },
                { label: 'Review', color: 'text-orange-400/50' },
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
        ) : (
          /* Message list */
          <div className="py-4 space-y-1 max-w-3xl mx-auto">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {/* Streaming content */}
            {streamingContent && (
              <StreamingBubble content={streamingContent} agentRole={currentAgent} />
            )}

            {/* Agent working indicator */}
            {isAgentRunning && !streamingContent && (
              <div className="flex gap-3 px-4 py-2 max-w-3xl">
                <div className="flex items-start shrink-0 pt-0.5">
                  <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-500/20 to-indigo-500/20 border border-violet-500/20 flex items-center justify-center">
                    <Bot className="w-3.5 h-3.5 text-violet-400" />
                  </div>
                </div>
                <div className="flex items-center gap-2 py-2">
                  <div className="flex gap-1">
                    {[0, 1, 2].map((i) => (
                      <div
                        key={i}
                        className="h-1.5 w-1.5 rounded-full bg-violet-400/80 animate-bounce"
                        style={{ animationDelay: `${i * 0.15}s` }}
                      />
                    ))}
                  </div>
                  {currentAgent && (
                    <span className={cn('text-[10px] font-mono', agentStyle.color)}>
                      {agentStyle.label} is working...
                    </span>
                  )}
                </div>
              </div>
            )}

            <div ref={messagesEndRef} className="h-1" />
          </div>
        )}
      </div>

      {/* Error display */}
      {error && (
        <div className="mx-6 mb-3 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3 backdrop-blur-sm">
          <p className="text-sm text-red-400 font-mono">{error}</p>
        </div>
      )}

      {/* Input area */}
      <div className="p-4 pb-6 shrink-0">
        <div className={cn(
          'relative flex items-end gap-2 rounded-2xl border bg-card/60 backdrop-blur-lg p-2.5 transition-all duration-300',
          'shadow-lg shadow-black/10',
          'focus-within:border-violet-500/20 focus-within:shadow-violet-500/5 focus-within:glow-sm',
          isAgentRunning && 'opacity-80',
        )}>
          {/* Gradient border effect */}
          <div className="absolute inset-0 rounded-2xl opacity-0 transition-opacity duration-300 pointer-events-none border border-transparent focus-within:opacity-100 card-futuristic" />

          <div className="flex items-center pl-2 pb-1.5 text-violet-400/30">
            <Sparkles className="w-4 h-4" />
          </div>

          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isAgentRunning}
            placeholder="Ask the agent to explore, write, or modify code..."
            rows={1}
            className={cn(
              'flex-1 resize-none bg-transparent text-sm leading-6 py-1.5',
              'placeholder:text-muted-foreground/30 focus:outline-none',
              'min-h-[32px] max-h-[144px]',
            )}
          />

          {isAgentRunning ? (
            <button
              onClick={stopAgent}
              className={cn(
                'flex items-center justify-center w-9 h-9 rounded-xl flex-shrink-0',
                'bg-red-500/10 text-red-400 border border-red-500/20',
                'hover:bg-red-500/20 hover:shadow-sm hover:shadow-red-500/10 transition-all duration-200'
              )}
              title="Stop agent"
            >
              <CircleStop className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!inputValue.trim()}
              className={cn(
                'flex items-center justify-center w-9 h-9 rounded-xl flex-shrink-0 transition-all duration-200',
                inputValue.trim()
                  ? 'bg-gradient-to-br from-violet-500 to-indigo-500 text-white shadow-md shadow-violet-500/25 hover:shadow-lg hover:shadow-violet-500/35 hover:scale-105'
                  : 'bg-muted/50 text-muted-foreground/20 cursor-not-allowed'
              )}
            >
              <ArrowUp className="w-4 h-4" />
            </button>
          )}
        </div>
        <p className="text-center text-[10px] text-muted-foreground/30 mt-2 font-mono">
          ENTER TO SEND &mdash; SHIFT+ENTER FOR NEW LINE
        </p>
      </div>
    </div>
  )
}
