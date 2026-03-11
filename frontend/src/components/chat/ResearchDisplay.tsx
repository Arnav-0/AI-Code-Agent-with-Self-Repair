'use client'

import {
  Search, BookOpen, Package, AlertTriangle, Brain,
  ChevronDown, ChevronRight, Shield, ExternalLink,
} from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import type { ResearchFindings } from '@/lib/types'

const confidenceColors = {
  high: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  low: 'bg-red-500/10 text-red-400 border-red-500/20',
}

function Section({
  title, icon: Icon, children, defaultOpen = true, count,
}: {
  title: string
  icon: React.ComponentType<{ className?: string }>
  children: React.ReactNode
  defaultOpen?: boolean
  count?: number
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="border border-border/20 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-4 py-3 bg-card/40 hover:bg-card/60 transition-colors text-left"
      >
        <Icon className="w-3.5 h-3.5 text-primary shrink-0" />
        <span className="text-xs font-semibold flex-1">{title}</span>
        {count !== undefined && (
          <span className="text-[10px] bg-muted/40 px-1.5 py-0.5 rounded tabular-nums">{count}</span>
        )}
        {open ? <ChevronDown className="w-3 h-3 text-muted-foreground" /> : <ChevronRight className="w-3 h-3 text-muted-foreground" />}
      </button>
      {open && <div className="p-4 space-y-2">{children}</div>}
    </div>
  )
}

export function ResearchDisplay({ findings }: { findings: ResearchFindings }) {
  if (!findings) return null

  const complexity = findings.estimated_complexity || 'unknown'
  const approach = findings.recommended_approach || 'No approach specified'
  const keyFindings = findings.key_findings || []
  const libraries = findings.libraries || []
  const risks = findings.risks || []

  return (
    <div className="rounded-2xl border-2 border-primary/20 bg-primary/[0.03] backdrop-blur-sm overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-primary/10 bg-primary/[0.05]">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary to-cyan-400 flex items-center justify-center">
            <Search className="w-3.5 h-3.5 text-white" />
          </div>
          <h3 className="text-sm font-bold">Research Findings</h3>
          {findings.search_results_used && (
            <span className="text-[10px] bg-cyan-500/10 text-cyan-400 px-2 py-0.5 rounded-full border border-cyan-500/20">
              <ExternalLink className="w-2.5 h-2.5 inline mr-0.5" />
              Web-enhanced
            </span>
          )}
          <span className={cn(
            'text-[10px] px-2 py-0.5 rounded-full border ml-auto',
            complexity === 'simple' && 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
            complexity === 'medium' && 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
            complexity === 'hard' && 'bg-red-500/10 text-red-400 border-red-500/20',
          )}>
            {complexity}
          </span>
        </div>
        <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
          {approach}
        </p>
      </div>

      <div className="p-4 space-y-3">
        {/* Key Findings */}
        {keyFindings.length > 0 && (
          <Section title="Key Findings" icon={Brain} count={keyFindings.length}>
            {keyFindings.map((f, i) => (
              <div key={i} className="flex gap-3 py-2 px-3 rounded-xl bg-background/30 border border-border/15">
                <div className={cn('shrink-0 mt-0.5 text-[9px] px-1.5 py-0.5 rounded border font-medium', confidenceColors[f.confidence] || confidenceColors.medium)}>
                  {f.confidence || 'unknown'}
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-foreground">{f.topic || 'General'}</p>
                  <p className="text-[11px] text-muted-foreground mt-0.5 leading-relaxed">{f.insight || ''}</p>
                </div>
              </div>
            ))}
          </Section>
        )}

        {/* Libraries */}
        {libraries.length > 0 && (
          <Section title="Recommended Libraries" icon={Package} count={libraries.length} defaultOpen={false}>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {libraries.map((lib, i) => (
                <div key={i} className="flex items-start gap-2 py-2 px-3 rounded-lg bg-background/30 border border-border/15">
                  <Package className="w-3 h-3 text-purple-400 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-xs font-semibold text-foreground font-mono">{lib.name || 'unknown'}</p>
                    <p className="text-[10px] text-muted-foreground">{lib.purpose || ''}</p>
                    {lib.version_note && (
                      <p className="text-[10px] text-yellow-400/70 mt-0.5">{lib.version_note}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Section>
        )}

        {/* Architecture */}
        {findings.architecture_notes && (
          <Section title="Architecture Notes" icon={BookOpen} defaultOpen={false}>
            <p className="text-[11px] text-muted-foreground leading-relaxed whitespace-pre-wrap">
              {findings.architecture_notes}
            </p>
          </Section>
        )}

        {/* Risks */}
        {risks.length > 0 && (
          <Section title="Risks & Considerations" icon={AlertTriangle} count={risks.length} defaultOpen={false}>
            {risks.map((risk, i) => (
              <div key={i} className="flex items-start gap-2 py-1.5">
                <Shield className="w-3 h-3 text-amber-400 mt-0.5 shrink-0" />
                <p className="text-[11px] text-muted-foreground">{risk}</p>
              </div>
            ))}
          </Section>
        )}
      </div>
    </div>
  )
}
