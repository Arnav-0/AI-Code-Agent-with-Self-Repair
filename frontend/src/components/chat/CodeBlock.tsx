'use client'

import { useCallback, useState } from 'react'
import { Check, Copy, Download, FileCode2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import dynamic from 'next/dynamic'

const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false })

function detectLanguage(code: string): string {
  if (code.includes('def ') || code.includes('import ') || code.includes('print(')) return 'python'
  if (code.includes('function ') || code.includes('const ') || code.includes('=>')) return 'typescript'
  if (code.includes('public class') || code.includes('System.out')) return 'java'
  if (code.includes('#include') || code.includes('int main')) return 'cpp'
  return 'python'
}

interface CodeBlockProps {
  code: string
  language?: string
  filename?: string
}

export function CodeBlock({ code, language, filename }: CodeBlockProps) {
  const [copied, setCopied] = useState(false)
  const detectedLang = language || detectLanguage(code)

  const lineCount = code.split('\n').length
  const editorHeight = Math.min(Math.max(lineCount * 19 + 20, 80), 450)

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }, [code])

  const handleDownload = useCallback(() => {
    const ext = detectedLang === 'python' ? 'py' : detectedLang === 'typescript' ? 'ts' : detectedLang
    const name = filename || `code.${ext}`
    const blob = new Blob([code], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = name
    a.click()
    URL.revokeObjectURL(url)
  }, [code, detectedLang, filename])

  return (
    <div className="relative rounded-2xl overflow-hidden border border-border/20 bg-[#060a10] shadow-2xl shadow-black/20">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-[#0a0f18] border-b border-white/[0.04]">
        <div className="flex items-center gap-2">
          <FileCode2 className="w-3.5 h-3.5 text-purple-400/60" />
          <span className="text-[11px] text-white/40 font-medium">
            {filename || detectedLang}
          </span>
          <span className="text-[10px] text-white/20">{lineCount} lines</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            className="flex items-center justify-center h-7 w-7 rounded-lg text-white/20 hover:text-white/50 hover:bg-white/5 transition-all"
            onClick={handleDownload}
            title="Download"
          >
            <Download className="w-3.5 h-3.5" />
          </button>
          <button
            className={cn(
              'flex items-center justify-center h-7 w-7 rounded-lg transition-all',
              copied ? 'text-emerald-400 bg-emerald-400/10' : 'text-white/20 hover:text-white/50 hover:bg-white/5'
            )}
            onClick={handleCopy}
            title="Copy"
          >
            {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>
      <MonacoEditor
        height={editorHeight}
        language={detectedLang}
        value={code}
        theme="vs-dark"
        options={{
          readOnly: true,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          lineNumbers: 'on',
          folding: false,
          renderLineHighlight: 'none',
          overviewRulerLanes: 0,
          hideCursorInOverviewRuler: true,
          scrollbar: { vertical: 'auto', horizontal: 'auto' },
          fontSize: 13,
          fontFamily: 'var(--font-geist-mono), monospace',
          padding: { top: 12, bottom: 12 },
        }}
      />
    </div>
  )
}
