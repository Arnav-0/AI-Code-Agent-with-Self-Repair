'use client'

import { cn } from '@/lib/utils'
import { Wrench, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react'
import dynamic from 'next/dynamic'

const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false })

interface RepairAttempt {
  attemptNumber: number
  error: string
  originalCode: string
  fixedCode: string
  success?: boolean
}

interface RepairDiffProps {
  attempts: RepairAttempt[]
  className?: string
}

function CodePane({ label, code, language = 'python' }: { label: string; code: string; language?: string }) {
  const lineCount = code.split('\n').length
  const height = Math.min(Math.max(lineCount * 19 + 20, 80), 300)

  return (
    <div className="flex-1 min-w-0">
      <div className="text-[11px] font-semibold text-white/40 mb-2 px-1 uppercase tracking-wider">{label}</div>
      <div className="rounded-xl overflow-hidden border border-white/5">
        <MonacoEditor
          height={height}
          language={language}
          value={code}
          theme="vs-dark"
          options={{
            readOnly: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            lineNumbers: 'off',
            folding: false,
            renderLineHighlight: 'none',
            overviewRulerLanes: 0,
            scrollbar: { vertical: 'auto', horizontal: 'hidden' },
            fontSize: 12,
            fontFamily: 'var(--font-geist-mono), monospace',
            padding: { top: 8, bottom: 8 },
          }}
        />
      </div>
    </div>
  )
}

export function RepairDiff({ attempts, className }: RepairDiffProps) {
  if (attempts.length === 0) return null

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center gap-2">
        <Wrench className="w-3.5 h-3.5 text-orange-400" />
        <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Self-Repair</span>
        <span className="text-[11px] text-muted-foreground/60 ml-1">
          {attempts.length} attempt{attempts.length !== 1 ? 's' : ''}
        </span>
      </div>

      {attempts.map((attempt) => (
        <div
          key={attempt.attemptNumber}
          className="rounded-2xl border border-orange-500/15 bg-orange-500/[0.03] p-4 space-y-3"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-orange-400 flex items-center gap-1.5">
              <AlertTriangle className="w-3 h-3" />
              Attempt #{attempt.attemptNumber}
            </span>
            {attempt.success !== undefined && (
              <span
                className={cn(
                  'text-xs font-semibold flex items-center gap-1',
                  attempt.success ? 'text-emerald-400' : 'text-red-400'
                )}
              >
                {attempt.success ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                {attempt.success ? 'Fixed' : 'Failed'}
              </span>
            )}
          </div>

          {attempt.error && (
            <div className="rounded-xl bg-red-500/5 border border-red-500/15 px-3 py-2">
              <p className="text-xs text-red-400/80 font-mono whitespace-pre-wrap leading-relaxed">{attempt.error}</p>
            </div>
          )}

          <div className="flex gap-3">
            <CodePane label="Original" code={attempt.originalCode} />
            <CodePane label="Fixed" code={attempt.fixedCode} />
          </div>
        </div>
      ))}
    </div>
  )
}
