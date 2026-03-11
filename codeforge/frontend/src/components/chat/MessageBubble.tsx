'use client'

import { useMemo } from 'react'
import { User, Bot, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'
import { ToolCallDisplay } from '@/components/chat/ToolCallDisplay'
import type { ConversationMessage } from '@/lib/types'

interface MessageBubbleProps {
  message: ConversationMessage
  isStreaming?: boolean
}

/** Minimal markdown-to-JSX renderer: handles code blocks, inline code, bold, italic, headings, and lists. */
function renderMarkdown(text: string): React.ReactNode[] {
  const elements: React.ReactNode[] = []
  const lines = text.split('\n')
  let i = 0

  while (i < lines.length) {
    const line = lines[i]

    // Fenced code block
    if (line.trimStart().startsWith('```')) {
      const lang = line.trimStart().slice(3).trim()
      const codeLines: string[] = []
      i++
      while (i < lines.length && !lines[i].trimStart().startsWith('```')) {
        codeLines.push(lines[i])
        i++
      }
      i++ // skip closing ```
      elements.push(
        <pre
          key={`code-${elements.length}`}
          className="my-2 rounded-lg bg-[#060a10] border border-border/15 p-3 overflow-x-auto"
        >
          {lang && (
            <div className="text-[10px] text-muted-foreground/40 font-mono mb-2 uppercase tracking-wider">
              {lang}
            </div>
          )}
          <code className="text-[12px] font-mono text-emerald-300/80 leading-relaxed">
            {codeLines.join('\n')}
          </code>
        </pre>
      )
      continue
    }

    // Heading
    const headingMatch = line.match(/^(#{1,3})\s+(.*)/)
    if (headingMatch) {
      const level = headingMatch[1].length
      const headingText = headingMatch[2]
      const headingClass = cn(
        'font-semibold text-foreground mt-3 mb-1',
        level === 1 && 'text-base',
        level === 2 && 'text-sm',
        level === 3 && 'text-xs text-foreground/80',
      )
      if (level === 1) {
        elements.push(<h2 key={`h-${elements.length}`} className={headingClass}>{renderInline(headingText)}</h2>)
      } else if (level === 2) {
        elements.push(<h3 key={`h-${elements.length}`} className={headingClass}>{renderInline(headingText)}</h3>)
      } else {
        elements.push(<h4 key={`h-${elements.length}`} className={headingClass}>{renderInline(headingText)}</h4>)
      }
      i++
      continue
    }

    // Unordered list item
    if (line.match(/^\s*[-*]\s+/)) {
      const listItems: React.ReactNode[] = []
      while (i < lines.length && lines[i].match(/^\s*[-*]\s+/)) {
        const itemText = lines[i].replace(/^\s*[-*]\s+/, '')
        listItems.push(
          <li key={`li-${i}`} className="text-sm leading-relaxed text-foreground/85">
            {renderInline(itemText)}
          </li>
        )
        i++
      }
      elements.push(
        <ul key={`ul-${elements.length}`} className="my-1.5 ml-4 list-disc space-y-0.5 marker:text-muted-foreground/30">
          {listItems}
        </ul>
      )
      continue
    }

    // Numbered list item
    if (line.match(/^\s*\d+\.\s+/)) {
      const listItems: React.ReactNode[] = []
      while (i < lines.length && lines[i].match(/^\s*\d+\.\s+/)) {
        const itemText = lines[i].replace(/^\s*\d+\.\s+/, '')
        listItems.push(
          <li key={`li-${i}`} className="text-sm leading-relaxed text-foreground/85">
            {renderInline(itemText)}
          </li>
        )
        i++
      }
      elements.push(
        <ol key={`ol-${elements.length}`} className="my-1.5 ml-4 list-decimal space-y-0.5 marker:text-muted-foreground/40">
          {listItems}
        </ol>
      )
      continue
    }

    // Empty line
    if (line.trim() === '') {
      elements.push(<div key={`br-${elements.length}`} className="h-2" />)
      i++
      continue
    }

    // Regular paragraph
    elements.push(
      <p key={`p-${elements.length}`} className="text-sm leading-relaxed text-foreground/85">
        {renderInline(line)}
      </p>
    )
    i++
  }

  return elements
}

/** Render inline markdown: **bold**, *italic*, `code`, and [links](url). */
function renderInline(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = []
  // Match patterns: **bold**, *italic*, `code`
  const regex = /(\*\*(.+?)\*\*)|(\*(.+?)\*)|(`(.+?)`)/g
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = regex.exec(text)) !== null) {
    // Text before match
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index))
    }

    if (match[1]) {
      // **bold**
      parts.push(
        <strong key={`b-${match.index}`} className="font-semibold text-foreground">
          {match[2]}
        </strong>
      )
    } else if (match[3]) {
      // *italic*
      parts.push(
        <em key={`i-${match.index}`} className="italic text-foreground/80">
          {match[4]}
        </em>
      )
    } else if (match[5]) {
      // `code`
      parts.push(
        <code
          key={`c-${match.index}`}
          className="px-1.5 py-0.5 rounded-md bg-primary/[0.08] text-primary/90 text-[12px] font-mono border border-primary/10"
        >
          {match[6]}
        </code>
      )
    }

    lastIndex = match.index + match[0].length
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex))
  }

  return parts.length > 0 ? parts : [text]
}

export function MessageBubble({ message, isStreaming = false }: MessageBubbleProps) {
  const { role, content, tool_calls, tool_name, agent_role } = message

  // Memoize rendered markdown for assistant text messages (must be called unconditionally)
  const renderedContent = useMemo(() => {
    if (role !== 'assistant' || !content || (tool_calls && tool_calls.length > 0)) return null
    return renderMarkdown(content)
  }, [role, content, tool_calls])

  // Tool result messages
  if (role === 'tool' && tool_name) {
    return (
      <div className="flex gap-3 px-4 py-1 max-w-3xl">
        <div className="w-7 shrink-0" /> {/* Spacer to align with assistant messages */}
        <div className="flex-1 min-w-0">
          <ToolCallDisplay
            toolName={tool_name}
            arguments_={{}}
            result={content}
            isError={content?.toLowerCase().includes('error') || content?.toLowerCase().includes('failed')}
          />
        </div>
      </div>
    )
  }

  // Assistant messages with tool calls
  if (role === 'assistant' && tool_calls && tool_calls.length > 0) {
    return (
      <div className="flex gap-3 px-4 py-1 max-w-3xl">
        <div className="w-7 shrink-0" />
        <div className="flex-1 min-w-0 space-y-1.5">
          {content && (
            <div className="text-sm text-foreground/85 leading-relaxed mb-2">
              {renderMarkdown(content)}
            </div>
          )}
          {tool_calls.map((tc) => (
            <ToolCallDisplay
              key={tc.id}
              toolName={tc.name}
              arguments_={tc.arguments}
            />
          ))}
        </div>
      </div>
    )
  }

  // User messages
  if (role === 'user') {
    return (
      <div className="flex gap-3 px-4 py-2 justify-end max-w-3xl ml-auto">
        <div className="max-w-[85%] min-w-0">
          <div className={cn(
            'rounded-2xl rounded-br-md px-4 py-2.5',
            'bg-gradient-to-br from-primary/90 to-primary/70',
            'text-primary-foreground shadow-md shadow-primary/10',
          )}>
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
          </div>
        </div>
        <div className="flex items-end shrink-0">
          <div className="w-7 h-7 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center">
            <User className="w-3.5 h-3.5 text-primary/70" />
          </div>
        </div>
      </div>
    )
  }

  // Assistant messages (text)
  if (role === 'assistant') {
    return (
      <div className="flex gap-3 px-4 py-2 max-w-3xl">
        <div className="flex items-start shrink-0 pt-0.5">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-500/20 to-indigo-500/20 border border-violet-500/20 flex items-center justify-center">
            <Bot className="w-3.5 h-3.5 text-violet-400" />
          </div>
        </div>
        <div className="flex-1 min-w-0">
          {agent_role && (
            <div className="flex items-center gap-1.5 mb-1">
              <Sparkles className="w-2.5 h-2.5 text-violet-400/60" />
              <span className="text-[10px] font-medium text-violet-400/60 uppercase tracking-wider font-mono">
                {agent_role}
              </span>
            </div>
          )}
          <div className="space-y-1">
            {renderedContent}
            {isStreaming && (
              <span className="inline-block w-2 h-4 bg-violet-400/80 rounded-sm animate-pulse ml-0.5 align-text-bottom" />
            )}
          </div>
        </div>
      </div>
    )
  }

  return null
}

/** Renders streaming content (partial assistant response). */
export function StreamingBubble({ content, agentRole }: { content: string; agentRole: string | null }) {
  if (!content) return null

  const rendered = renderMarkdown(content)

  return (
    <div className="flex gap-3 px-4 py-2 max-w-3xl">
      <div className="flex items-start shrink-0 pt-0.5">
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-500/20 to-indigo-500/20 border border-violet-500/20 flex items-center justify-center">
          <Bot className="w-3.5 h-3.5 text-violet-400" />
        </div>
      </div>
      <div className="flex-1 min-w-0">
        {agentRole && (
          <div className="flex items-center gap-1.5 mb-1">
            <Sparkles className="w-2.5 h-2.5 text-violet-400/60" />
            <span className="text-[10px] font-medium text-violet-400/60 uppercase tracking-wider font-mono">
              {agentRole}
            </span>
          </div>
        )}
        <div className="space-y-1">
          {rendered}
          <span className="inline-block w-2 h-4 bg-violet-400/80 rounded-sm animate-pulse ml-0.5 align-text-bottom" />
        </div>
      </div>
    </div>
  )
}
