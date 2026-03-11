'use client'

import { useCallback, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Check, HelpCircle, Send, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ResearchQuestion } from '@/lib/types'

const impactColors = {
  high: 'bg-red-500/10 text-red-400 border-red-500/20',
  medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  low: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
}

const categoryIcons: Record<string, string> = {
  architecture: 'Arch',
  api_design: 'API',
  data_model: 'Data',
  security: 'Sec',
  performance: 'Perf',
  scope: 'Scope',
  dependencies: 'Deps',
}

interface QuestionFormProps {
  questions: ResearchQuestion[]
  onSubmit: (answers: Record<string, string>) => void
  onSkip: () => void
}

export function QuestionForm({ questions, onSubmit, onSkip }: QuestionFormProps) {
  const [answers, setAnswers] = useState<Record<string, string>>(() => {
    const defaults: Record<string, string> = {}
    for (const q of questions) {
      defaults[String(q.id)] = q.default_answer || ''
    }
    return defaults
  })
  const [submitting, setSubmitting] = useState(false)

  const setAnswer = useCallback((id: number, value: string) => {
    setAnswers(prev => ({ ...prev, [String(id)]: value }))
  }, [])

  const handleSubmit = useCallback(() => {
    if (submitting) return
    setSubmitting(true)
    onSubmit(answers)
  }, [answers, onSubmit, submitting])

  const handleDefaults = useCallback(() => {
    if (submitting) return
    setSubmitting(true)
    const defaults: Record<string, string> = {}
    for (const q of questions) {
      defaults[String(q.id)] = q.default_answer || ''
    }
    setAnswers(defaults)
    onSubmit(defaults)
  }, [questions, onSubmit, submitting])

  const handleSkip = useCallback(() => {
    if (submitting) return
    setSubmitting(true)
    onSkip()
  }, [onSkip, submitting])

  return (
    <div className="rounded-2xl border-2 border-cyan-500/20 bg-cyan-500/[0.03] backdrop-blur-sm overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-cyan-500/10 bg-cyan-500/[0.05]">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center">
            <HelpCircle className="w-3.5 h-3.5 text-white" />
          </div>
          <h3 className="text-sm font-bold">Clarification Questions</h3>
          <span className="text-[10px] bg-cyan-500/10 text-cyan-400 px-2 py-0.5 rounded-full border border-cyan-500/20">
            {questions.length} {questions.length === 1 ? 'question' : 'questions'}
          </span>
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          Answer these to help build exactly what you need. Defaults are pre-filled — adjust or accept.
        </p>
      </div>

      {/* Questions */}
      <div className="p-4 space-y-4">
        {questions.map((q, i) => (
          <div key={q.id} className="space-y-2">
            <div className="flex items-start gap-2">
              <div className="flex items-center justify-center w-6 h-6 rounded-lg text-[10px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shrink-0 mt-0.5">
                {i + 1}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-foreground leading-relaxed">{q.question}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className={cn('text-[9px] px-1.5 py-0.5 rounded border font-medium', impactColors[q.impact])}>
                    {q.impact}
                  </span>
                  <span className="text-[9px] bg-muted/40 text-muted-foreground px-1.5 py-0.5 rounded">
                    {categoryIcons[q.category] || q.category}
                  </span>
                  <span className="text-[10px] text-muted-foreground/60 italic">{q.why}</span>
                </div>
              </div>
            </div>

            {/* Answer input */}
            {q.options && q.options.length > 0 ? (
              <div className="ml-8 flex flex-wrap gap-1.5">
                {q.options.map((opt) => (
                  <button
                    key={opt}
                    onClick={() => setAnswer(q.id, opt)}
                    className={cn(
                      'px-3 py-1.5 rounded-lg text-[11px] border transition-all',
                      answers[String(q.id)] === opt
                        ? 'bg-primary/10 border-primary/30 text-primary font-medium'
                        : 'bg-card/30 border-border/20 text-muted-foreground hover:border-primary/20 hover:text-foreground'
                    )}
                  >
                    {answers[String(q.id)] === opt && <Check className="w-2.5 h-2.5 inline mr-1" />}
                    {opt}
                  </button>
                ))}
              </div>
            ) : (
              <div className="ml-8">
                <textarea
                  value={answers[String(q.id)] || ''}
                  onChange={e => setAnswer(q.id, e.target.value)}
                  placeholder={q.default_answer || 'Your answer...'}
                  rows={2}
                  className="w-full text-[11px] bg-background/50 border border-border/20 rounded-xl px-3 py-2 resize-none focus:outline-none focus:border-primary/30 focus:ring-1 focus:ring-primary/10 text-foreground placeholder:text-muted-foreground/40"
                />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="p-4 border-t border-cyan-500/10 flex items-center gap-3">
        <Button
          onClick={handleSubmit}
          disabled={submitting}
          size="sm"
          className="gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 text-white shadow-lg shadow-cyan-500/20"
        >
          <Send className="w-3.5 h-3.5" />
          {submitting ? 'Submitting...' : 'Submit Answers'}
        </Button>
        <Button
          onClick={handleDefaults}
          disabled={submitting}
          variant="outline"
          size="sm"
          className="gap-2 rounded-xl text-xs"
        >
          <Sparkles className="w-3 h-3" />
          Use Defaults
        </Button>
        <Button
          onClick={handleSkip}
          disabled={submitting}
          variant="ghost"
          size="sm"
          className="gap-2 rounded-xl text-xs text-muted-foreground"
        >
          Skip Questions
        </Button>
        <p className="text-[10px] text-muted-foreground ml-auto">
          Your answers refine the implementation plan
        </p>
      </div>
    </div>
  )
}
