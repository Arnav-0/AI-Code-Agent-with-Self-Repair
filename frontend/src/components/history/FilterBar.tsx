'use client'

import { Input } from '@/components/ui/input'
import { Search, ArrowUpDown, Filter } from 'lucide-react'
import type { HistoryParams } from '@/lib/types'

const STATUS_OPTIONS = ['all', 'completed', 'failed', 'pending', 'classifying', 'planning', 'coding', 'executing', 'reviewing']
const SORT_OPTIONS = [
  { value: 'created_at', label: 'Date' },
  { value: 'total_cost_usd', label: 'Cost' },
  { value: 'total_time_ms', label: 'Duration' },
]

interface FilterBarProps {
  params: HistoryParams
  onChange: (params: HistoryParams) => void
}

export function FilterBar({ params, onChange }: FilterBarProps) {
  return (
    <div className="flex flex-wrap items-center gap-2 p-3 border-b border-border/30 bg-card/30 backdrop-blur-sm">
      <div className="relative flex-1 min-w-[140px]">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground/50" />
        <Input
          placeholder="Search..."
          value={params.search ?? ''}
          onChange={(e) => onChange({ ...params, search: e.target.value, page: 1 })}
          className="h-8 pl-8 text-xs rounded-lg bg-background/50 border-border/30"
        />
      </div>

      <div className="relative">
        <Filter className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-muted-foreground/50 pointer-events-none" />
        <select
          value={params.status ?? 'all'}
          onChange={(e) =>
            onChange({ ...params, status: e.target.value === 'all' ? undefined : e.target.value, page: 1 })
          }
          className="h-8 rounded-lg border border-border/30 bg-background/50 pl-7 pr-2 text-xs text-foreground appearance-none cursor-pointer"
        >
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </option>
          ))}
        </select>
      </div>

      <div className="relative">
        <select
          value={params.sort_by ?? 'created_at'}
          onChange={(e) => onChange({ ...params, sort_by: e.target.value })}
          className="h-8 rounded-lg border border-border/30 bg-background/50 px-2 text-xs text-foreground appearance-none cursor-pointer"
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      <button
        onClick={() => onChange({ ...params, order: params.order === 'asc' ? 'desc' : 'asc' })}
        className="h-8 w-8 rounded-lg border border-border/30 bg-background/50 flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-accent/30 transition-colors"
        title={params.order === 'asc' ? 'Ascending' : 'Descending'}
      >
        <ArrowUpDown className="w-3.5 h-3.5" />
      </button>
    </div>
  )
}
