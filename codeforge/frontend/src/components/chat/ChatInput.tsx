'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { CircleStop, ArrowUp, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ChatInputProps {
  onSubmit: (prompt: string, contextCode?: string) => void
  onCancel?: () => void
  disabled?: boolean
  showCancel?: boolean
  contextCode?: string | null
}

export function ChatInput({ onSubmit, onCancel, disabled = false, showCancel = false, contextCode }: ChatInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const adjustHeight = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    const lineHeight = 24
    const minHeight = lineHeight
    const maxHeight = lineHeight * 6
    el.style.height = `${Math.min(Math.max(el.scrollHeight, minHeight), maxHeight)}px`
  }, [])

  useEffect(() => {
    adjustHeight()
  }, [value, adjustHeight])

  const handleSubmit = useCallback(() => {
    const prompt = value.trim()
    if (!prompt || disabled) return
    onSubmit(prompt, contextCode || undefined)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }, [value, disabled, onSubmit])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSubmit()
      }
    },
    [handleSubmit]
  )

  return (
    <div className="p-4 pb-6">
      <div className={cn(
        'relative flex items-end gap-2 rounded-2xl border bg-card/60 backdrop-blur-lg p-2.5 transition-all duration-300',
        'shadow-lg shadow-black/10',
        'focus-within:border-primary/20 focus-within:shadow-primary/5 focus-within:glow-sm',
        disabled && 'opacity-60'
      )}>
        {/* Gradient border on focus */}
        <div className="absolute inset-0 rounded-2xl opacity-0 transition-opacity duration-300 pointer-events-none border border-transparent focus-within:opacity-100 card-futuristic" />

        <div className="flex items-center pl-2 pb-1.5 text-primary/30">
          <Sparkles className="w-4 h-4" />
        </div>
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={contextCode
            ? "Describe what to change... e.g. 'Add error handling' or 'Make it async'"
            : "Describe a coding task... e.g. 'Write a Python function for binary search with unit tests'"
          }
          rows={1}
          className={cn(
            'flex-1 resize-none bg-transparent text-sm leading-6 py-1.5',
            'placeholder:text-muted-foreground/30 focus:outline-none',
            'min-h-[32px] max-h-[144px]',
          )}
        />
        {showCancel && onCancel ? (
          <button
            onClick={onCancel}
            className={cn(
              'flex items-center justify-center w-9 h-9 rounded-xl flex-shrink-0',
              'bg-red-500/10 text-red-400 border border-red-500/20',
              'hover:bg-red-500/20 hover:shadow-sm hover:shadow-red-500/10 transition-all duration-200'
            )}
            title="Cancel task"
          >
            <CircleStop className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={disabled || !value.trim()}
            className={cn(
              'flex items-center justify-center w-9 h-9 rounded-xl flex-shrink-0 transition-all duration-200',
              value.trim() && !disabled
                ? 'bg-gradient-to-br from-primary to-purple-500 text-white shadow-md shadow-primary/25 hover:shadow-lg hover:shadow-primary/35 hover:scale-105'
                : 'bg-muted/50 text-muted-foreground/20 cursor-not-allowed'
            )}
          >
            <ArrowUp className="w-4 h-4" />
          </button>
        )}
      </div>
      <p className="text-center text-[10px] text-muted-foreground/30 mt-2 font-mono">
        {contextCode
          ? 'REFINING PREVIOUS CODE — ENTER TO SEND'
          : 'ENTER TO SEND — SHIFT+ENTER FOR NEW LINE'
        }
      </p>
    </div>
  )
}
