'use client'

import { useState } from 'react'
import {
  FileText,
  Terminal,
  Search,
  FolderOpen,
  Pencil,
  Trash2,
  Globe,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  XCircle,
  Wrench,
  Clock,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface ToolCallDisplayProps {
  toolName: string
  arguments_: Record<string, unknown>
  result?: string | null
  isError?: boolean
  durationMs?: number
}

const TOOL_ICON_MAP: Record<string, { icon: typeof FileText; color: string }> = {
  read_file: { icon: FileText, color: 'text-blue-400' },
  read: { icon: FileText, color: 'text-blue-400' },
  write_file: { icon: Pencil, color: 'text-emerald-400' },
  write: { icon: Pencil, color: 'text-emerald-400' },
  edit_file: { icon: Pencil, color: 'text-amber-400' },
  edit: { icon: Pencil, color: 'text-amber-400' },
  delete_file: { icon: Trash2, color: 'text-red-400' },
  list_directory: { icon: FolderOpen, color: 'text-cyan-400' },
  list_dir: { icon: FolderOpen, color: 'text-cyan-400' },
  glob: { icon: FolderOpen, color: 'text-cyan-400' },
  bash: { icon: Terminal, color: 'text-yellow-400' },
  execute: { icon: Terminal, color: 'text-yellow-400' },
  run_command: { icon: Terminal, color: 'text-yellow-400' },
  search: { icon: Search, color: 'text-purple-400' },
  grep: { icon: Search, color: 'text-purple-400' },
  find: { icon: Search, color: 'text-purple-400' },
  web_search: { icon: Globe, color: 'text-indigo-400' },
  web_fetch: { icon: Globe, color: 'text-indigo-400' },
}

function getToolIcon(name: string) {
  const lower = name.toLowerCase()
  for (const [key, val] of Object.entries(TOOL_ICON_MAP)) {
    if (lower.includes(key)) return val
  }
  return { icon: Wrench, color: 'text-muted-foreground' }
}

function formatArguments(args: Record<string, unknown>): string[] {
  return Object.entries(args).map(([key, value]) => {
    const strVal = typeof value === 'string'
      ? (value.length > 100 ? value.slice(0, 100) + '...' : value)
      : JSON.stringify(value)
    return `${key}: ${strVal}`
  })
}

function truncateResult(result: string, maxLines: number = 8): { text: string; truncated: boolean } {
  const lines = result.split('\n')
  if (lines.length <= maxLines) return { text: result, truncated: false }
  return { text: lines.slice(0, maxLines).join('\n'), truncated: true }
}

export function ToolCallDisplay({ toolName, arguments_, result, isError, durationMs }: ToolCallDisplayProps) {
  const [expanded, setExpanded] = useState(false)
  const { icon: Icon, color } = getToolIcon(toolName)
  const formattedArgs = formatArguments(arguments_)
  const hasResult = result !== null && result !== undefined && result !== ''

  const truncated = hasResult ? truncateResult(result!, expanded ? 999 : 8) : null

  return (
    <div
      className={cn(
        'rounded-xl border overflow-hidden transition-all duration-200',
        isError
          ? 'border-red-500/20 bg-red-500/[0.03]'
          : 'border-border/30 bg-card/30 hover:border-border/50',
      )}
    >
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2.5 w-full px-3 py-2 text-left hover:bg-white/[0.02] transition-colors"
      >
        <div className={cn('flex items-center justify-center w-6 h-6 rounded-lg bg-background/50', color)}>
          <Icon className="w-3.5 h-3.5" />
        </div>

        <span className="text-xs font-semibold text-foreground/90 font-mono flex-1 truncate">
          {toolName}
        </span>

        {durationMs !== undefined && (
          <span className="flex items-center gap-1 text-[10px] text-muted-foreground/60 font-mono shrink-0">
            <Clock className="w-2.5 h-2.5" />
            {durationMs}ms
          </span>
        )}

        {hasResult && (
          isError ? (
            <XCircle className="w-3.5 h-3.5 text-red-400 shrink-0" />
          ) : (
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400/70 shrink-0" />
          )
        )}

        {hasResult ? (
          expanded ? (
            <ChevronDown className="w-3.5 h-3.5 text-muted-foreground/40 shrink-0" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5 text-muted-foreground/40 shrink-0" />
          )
        ) : null}
      </button>

      {/* Arguments */}
      {formattedArgs.length > 0 && (
        <div className="px-3 pb-2 -mt-0.5">
          {formattedArgs.map((arg, i) => (
            <div key={i} className="text-[11px] text-muted-foreground/60 font-mono truncate leading-relaxed pl-8">
              {arg}
            </div>
          ))}
        </div>
      )}

      {/* Result (collapsible) */}
      {hasResult && (
        <div className={cn(
          'mx-3 mb-3 rounded-lg overflow-hidden border',
          isError ? 'border-red-500/15 bg-red-950/30' : 'border-border/15 bg-[#060a10]',
        )}>
          <pre className={cn(
            'text-[11px] font-mono p-3 overflow-x-auto leading-relaxed whitespace-pre-wrap break-all max-h-[300px] overflow-y-auto',
            isError ? 'text-red-300/80' : 'text-muted-foreground/70',
          )}>
            {expanded ? result : truncated?.text}
          </pre>
          {truncated?.truncated && !expanded && (
            <button
              onClick={(e) => { e.stopPropagation(); setExpanded(true) }}
              className="w-full py-1.5 text-[10px] text-primary/60 hover:text-primary/80 bg-white/[0.02] border-t border-border/10 transition-colors font-medium"
            >
              Show {result!.split('\n').length - 8} more lines
            </button>
          )}
        </div>
      )}
    </div>
  )
}
