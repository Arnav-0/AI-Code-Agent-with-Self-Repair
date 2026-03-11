'use client'

import { Slider } from '@/components/ui/slider'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'
import type { RoutingSettings } from '@/lib/types'

interface RoutingConfigProps {
  value: RoutingSettings
  onChange: (v: RoutingSettings) => void
}

export function RoutingConfig({ value, onChange }: RoutingConfigProps) {
  return (
    <div className="space-y-5">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label className="text-xs text-muted-foreground">Simple Task Threshold</Label>
          <span className="text-xs font-mono font-semibold tabular-nums bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-md border border-emerald-500/20">
            {value.simple_threshold.toFixed(2)}
          </span>
        </div>
        <Slider
          value={[value.simple_threshold]}
          onValueChange={([v]) => onChange({ ...value, simple_threshold: v })}
          min={0}
          max={1}
          step={0.05}
        />
        <p className="text-[11px] text-muted-foreground/60">
          Tasks below this complexity score use <span className="text-emerald-400/80 font-medium">{value.simple_model}</span>
        </p>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label className="text-xs text-muted-foreground">Complex Task Threshold</Label>
          <span className="text-xs font-mono font-semibold tabular-nums bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded-md border border-blue-500/20">
            {value.complex_threshold.toFixed(2)}
          </span>
        </div>
        <Slider
          value={[value.complex_threshold]}
          onValueChange={([v]) => onChange({ ...value, complex_threshold: v })}
          min={0}
          max={1}
          step={0.05}
        />
        <p className="text-[11px] text-muted-foreground/60">
          Tasks above this complexity score use <span className="text-blue-400/80 font-medium">{value.complex_model}</span>
        </p>
      </div>

      {/* Visual routing tier bar */}
      <div className="rounded-xl bg-muted/20 border border-border/20 p-3.5 space-y-2.5">
        <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Routing Tiers</p>
        <div className="flex h-8 rounded-xl overflow-hidden border border-border/20">
          <div
            className="flex items-center justify-center text-[10px] font-semibold text-white transition-all"
            style={{
              width: `${Math.max(value.simple_threshold * 100, 5)}%`,
              background: 'linear-gradient(90deg, #10b98180, #10b981b0)',
            }}
          >
            {value.simple_threshold > 0.12 && (
              <span className="truncate px-1">{value.simple_model}</span>
            )}
          </div>
          <div
            className="flex items-center justify-center text-[10px] font-semibold text-white transition-all"
            style={{
              width: `${Math.max((value.complex_threshold - value.simple_threshold) * 100, 5)}%`,
              background: 'linear-gradient(90deg, #eab30880, #eab308b0)',
            }}
          >
            {value.complex_threshold - value.simple_threshold > 0.12 && (
              <span className="truncate px-1">medium</span>
            )}
          </div>
          <div
            className="flex items-center justify-center text-[10px] font-semibold text-white transition-all"
            style={{
              width: `${Math.max((1 - value.complex_threshold) * 100, 5)}%`,
              background: 'linear-gradient(90deg, #3b82f680, #3b82f6b0)',
            }}
          >
            {1 - value.complex_threshold > 0.12 && (
              <span className="truncate px-1">{value.complex_model}</span>
            )}
          </div>
        </div>
        <div className="flex justify-between text-[10px] text-muted-foreground/50 px-0.5">
          <span>0.0 — Simple</span>
          <span>Complexity Score</span>
          <span>Complex — 1.0</span>
        </div>
      </div>
    </div>
  )
}
