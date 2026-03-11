'use client'

import { useEffect, useRef, useState } from 'react'
import { Copy, Check, CheckCircle2, XCircle, Clock, HardDrive, TerminalSquare } from 'lucide-react'
import { cn } from '@/lib/utils'

interface TerminalLine {
  type: 'stdout' | 'stderr' | 'info'
  content: string
}

interface TerminalOutputProps {
  lines: TerminalLine[]
  exitCode?: number
  executionTime?: number
  memoryUsage?: number
  className?: string
}

export function TerminalOutput({
  lines,
  exitCode,
  executionTime,
  memoryUsage,
  className,
}: TerminalOutputProps) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [lines])

  const handleCopy = () => {
    const text = lines.map(l => l.content).join('\n')
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div
      className={cn(
        'rounded-2xl border border-border/20 bg-[#060a10] font-mono text-xs overflow-hidden shadow-xl shadow-black/20 relative scanlines',
        className
      )}
    >
      {/* Terminal header */}
      <div className="flex items-center gap-2 px-4 py-3 bg-[#0a0f18] border-b border-white/[0.04] relative">
        <div className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-full bg-[#ff5f57]/80" />
          <span className="h-3 w-3 rounded-full bg-[#febc2e]/80" />
          <span className="h-3 w-3 rounded-full bg-[#28c840]/80" />
        </div>
        <div className="flex items-center gap-1.5 ml-2">
          <TerminalSquare className="w-3 h-3 text-white/20" />
          <span className="text-white/25 text-[10px] font-semibold tracking-wider uppercase">sandbox</span>
        </div>
        <div className="ml-auto flex items-center gap-2">
          {exitCode !== undefined && (
            exitCode === 0
              ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400/60" />
              : <XCircle className="w-3.5 h-3.5 text-red-400/60" />
          )}
          <button
            onClick={handleCopy}
            className="text-white/15 hover:text-white/40 transition-colors"
            title="Copy output"
          >
            {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
          </button>
        </div>
      </div>

      {/* Output lines */}
      <div className="p-4 max-h-72 overflow-auto space-y-px">
        {lines.length === 0 && (
          <span className="text-white/15">
            <span className="text-cyan-400/40">$</span> Waiting for output...
          </span>
        )}
        {lines.map((line, i) => (
          <div
            key={i}
            className={cn(
              'leading-5 whitespace-pre-wrap break-all',
              line.type === 'stdout' && 'text-[#7ee787]',
              line.type === 'stderr' && 'text-[#ff7b72]',
              line.type === 'info' && 'text-cyan-400/30'
            )}
          >
            {line.content}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Footer metrics */}
      {(exitCode !== undefined || executionTime !== undefined) && (
        <div className="flex items-center gap-4 px-4 py-2.5 bg-[#0a0f18] border-t border-white/[0.04] text-white/25">
          {exitCode !== undefined && (
            <span className={cn(
              'font-semibold text-[11px] font-mono',
              exitCode === 0 ? 'text-emerald-400/70' : 'text-red-400/70'
            )}>
              EXIT {exitCode}
            </span>
          )}
          {executionTime !== undefined && (
            <span className="flex items-center gap-1 text-[11px]">
              <Clock className="w-3 h-3" />
              {(executionTime / 1000).toFixed(2)}s
            </span>
          )}
          {memoryUsage !== undefined && memoryUsage > 0 && (
            <span className="flex items-center gap-1 text-[11px]">
              <HardDrive className="w-3 h-3" />
              {memoryUsage.toFixed(1)} MB
            </span>
          )}
        </div>
      )}
    </div>
  )
}
