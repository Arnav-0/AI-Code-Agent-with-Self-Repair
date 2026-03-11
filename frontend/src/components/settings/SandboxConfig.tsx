'use client'

import { Slider } from '@/components/ui/slider'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Clock, HardDrive, RotateCcw, ShieldCheck } from 'lucide-react'
import type { SandboxSettings } from '@/lib/types'

interface SandboxConfigProps {
  value: SandboxSettings
  onChange: (v: SandboxSettings) => void
}

function SettingRow({
  icon,
  label,
  description,
  valueDisplay,
  children,
}: {
  icon: React.ReactNode
  label: string
  description: string
  valueDisplay: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <div className="space-y-3 rounded-xl bg-background/30 border border-border/20 p-3.5">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-2.5">
          <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-muted/50 border border-border/20 mt-0.5">
            {icon}
          </div>
          <div>
            <Label className="text-xs font-semibold">{label}</Label>
            <p className="text-[11px] text-muted-foreground/60 mt-0.5">{description}</p>
          </div>
        </div>
        <span className="text-xs font-mono font-semibold tabular-nums bg-muted/50 px-2 py-0.5 rounded-md border border-border/20 shrink-0">
          {valueDisplay}
        </span>
      </div>
      {children}
    </div>
  )
}

export function SandboxConfig({ value, onChange }: SandboxConfigProps) {
  return (
    <div className="space-y-3">
      <SettingRow
        icon={<Clock className="w-3.5 h-3.5 text-yellow-400" />}
        label="Execution Timeout"
        description="Max time allowed for code execution before termination"
        valueDisplay={`${value.timeout_seconds}s`}
      >
        <Slider
          value={[value.timeout_seconds]}
          onValueChange={([v]) => onChange({ ...value, timeout_seconds: v })}
          min={5}
          max={120}
          step={5}
        />
      </SettingRow>

      <SettingRow
        icon={<HardDrive className="w-3.5 h-3.5 text-blue-400" />}
        label="Memory Limit"
        description="Maximum memory allocation for sandbox container"
        valueDisplay={`${value.memory_limit_mb} MB`}
      >
        <Slider
          value={[value.memory_limit_mb]}
          onValueChange={([v]) => onChange({ ...value, memory_limit_mb: v })}
          min={128}
          max={2048}
          step={128}
        />
      </SettingRow>

      <SettingRow
        icon={<RotateCcw className="w-3.5 h-3.5 text-orange-400" />}
        label="Max Self-Repair Retries"
        description="Number of times the AI can attempt to fix failing code"
        valueDisplay={value.max_retries}
      >
        <Slider
          value={[value.max_retries]}
          onValueChange={([v]) => onChange({ ...value, max_retries: v })}
          min={0}
          max={10}
          step={1}
        />
      </SettingRow>

      <div className="flex items-center justify-between rounded-xl bg-background/30 border border-border/20 p-3.5">
        <div className="flex items-start gap-2.5">
          <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/20 mt-0.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div>
            <Label className="text-xs font-semibold">Network Isolation</Label>
            <p className="text-[11px] text-muted-foreground/60 mt-0.5">
              Block all network access in the sandbox — always enabled for safety
            </p>
          </div>
        </div>
        <Switch
          checked={true}
          onCheckedChange={() => {}}
          disabled
        />
      </div>
    </div>
  )
}
