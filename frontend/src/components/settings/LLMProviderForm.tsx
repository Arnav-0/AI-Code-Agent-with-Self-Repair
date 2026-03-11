'use client'

import { useState } from 'react'
import { Check, X, Loader2, Key, Globe, Cpu } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { testConnection } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { LLMProviderSettings } from '@/lib/types'

type TestStatus = 'idle' | 'loading' | 'success' | 'error'

interface ProviderSectionProps {
  name: string
  provider: 'openai' | 'anthropic' | 'ollama'
  description: string
  icon: React.ReactNode
  gradient: string
  apiKey?: string | null
  endpoint?: string
  onKeyChange: (v: string) => void
  onEndpointChange?: (v: string) => void
}

function ProviderSection({
  name,
  provider,
  description,
  icon,
  gradient,
  apiKey,
  endpoint,
  onKeyChange,
  onEndpointChange,
}: ProviderSectionProps) {
  const [status, setStatus] = useState<TestStatus>('idle')
  const [message, setMessage] = useState('')

  const handleTest = async () => {
    setStatus('loading')
    try {
      const res = await testConnection(provider, apiKey ?? undefined, endpoint)
      setStatus(res.success ? 'success' : 'error')
      setMessage(res.message)
    } catch (e) {
      setStatus('error')
      setMessage(String(e))
    }
  }

  const hasKey = !!apiKey && apiKey.length > 0
  const hasEndpoint = !!endpoint && endpoint.length > 0

  return (
    <div className={cn(
      'rounded-xl border p-4 space-y-3 transition-all',
      status === 'success' ? 'border-emerald-500/30 bg-emerald-500/[0.03]' :
      status === 'error' ? 'border-red-500/30 bg-red-500/[0.03]' :
      'border-border/30 bg-background/30 hover:border-border/50'
    )}>
      <div className="flex items-center gap-3">
        <div className={cn('flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br shadow-sm', gradient)}>
          {icon}
        </div>
        <div className="flex-1">
          <h4 className="text-sm font-semibold">{name}</h4>
          <p className="text-[11px] text-muted-foreground">{description}</p>
        </div>
        {(hasKey || (provider === 'ollama' && hasEndpoint)) && (
          <div className={cn(
            'text-[10px] font-medium px-2 py-0.5 rounded-md border',
            status === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
            'bg-primary/10 border-primary/20 text-primary'
          )}>
            {status === 'success' ? 'Connected' : 'Configured'}
          </div>
        )}
      </div>

      {provider !== 'ollama' && (
        <div className="space-y-1.5">
          <Label className="text-xs text-muted-foreground flex items-center gap-1.5">
            <Key className="w-3 h-3" />
            API Key
          </Label>
          <Input
            type="password"
            value={apiKey ?? ''}
            onChange={(e) => onKeyChange(e.target.value)}
            placeholder={provider === 'openai' ? 'sk-...' : 'sk-ant-...'}
            className="h-9 text-sm font-mono bg-background/50 border-border/30"
          />
        </div>
      )}

      {onEndpointChange && (
        <div className="space-y-1.5">
          <Label className="text-xs text-muted-foreground flex items-center gap-1.5">
            <Globe className="w-3 h-3" />
            Endpoint URL
          </Label>
          <Input
            value={endpoint ?? ''}
            onChange={(e) => onEndpointChange(e.target.value)}
            placeholder="http://localhost:11434"
            className="h-9 text-sm font-mono bg-background/50 border-border/30"
          />
        </div>
      )}

      <div className="flex items-center gap-2 pt-1">
        <Button
          variant="outline"
          size="sm"
          onClick={handleTest}
          disabled={status === 'loading'}
          className="h-8 text-xs rounded-lg gap-1.5"
        >
          {status === 'loading' && <Loader2 className="h-3 w-3 animate-spin" />}
          Test Connection
        </Button>
        {status === 'success' && <Check className="h-4 w-4 text-emerald-400" />}
        {status === 'error' && <X className="h-4 w-4 text-red-400" />}
        {message && (
          <span className={cn(
            'text-[11px] truncate max-w-[250px]',
            status === 'success' ? 'text-emerald-400/80' : 'text-red-400/80'
          )}>
            {message}
          </span>
        )}
      </div>
    </div>
  )
}

interface LLMProviderFormProps {
  value: LLMProviderSettings
  onChange: (v: LLMProviderSettings) => void
}

export function LLMProviderForm({ value, onChange }: LLMProviderFormProps) {
  return (
    <div className="space-y-3">
      <ProviderSection
        name="OpenAI"
        provider="openai"
        description="GPT-4o, GPT-4o-mini, and other OpenAI models"
        icon={<Cpu className="w-4 h-4 text-white" />}
        gradient="from-emerald-500 to-teal-400"
        apiKey={value.openai_api_key}
        onKeyChange={(v) => onChange({ ...value, openai_api_key: v })}
      />
      <ProviderSection
        name="Anthropic"
        provider="anthropic"
        description="Claude Opus, Sonnet, and Haiku models"
        icon={<Cpu className="w-4 h-4 text-white" />}
        gradient="from-orange-500 to-amber-400"
        apiKey={value.anthropic_api_key}
        onKeyChange={(v) => onChange({ ...value, anthropic_api_key: v })}
      />
      <ProviderSection
        name="Ollama (Local)"
        provider="ollama"
        description="Self-hosted open-source models via Ollama"
        icon={<Cpu className="w-4 h-4 text-white" />}
        gradient="from-purple-500 to-indigo-400"
        endpoint={value.ollama_endpoint}
        onKeyChange={() => {}}
        onEndpointChange={(v) => onChange({ ...value, ollama_endpoint: v })}
      />
    </div>
  )
}
