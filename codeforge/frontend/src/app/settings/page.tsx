'use client'

import { useCallback, useEffect, useState } from 'react'
import { toast } from 'sonner'
import { getSettings, updateSettings } from '@/lib/api'
import { LLMProviderForm } from '@/components/settings/LLMProviderForm'
import { RoutingConfig } from '@/components/settings/RoutingConfig'
import { SandboxConfig } from '@/components/settings/SandboxConfig'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import {
  Settings, Cpu, Route, Shield, Save, Loader2, CheckCircle2, RotateCcw,
} from 'lucide-react'
import type { AppSettings } from '@/lib/types'

const DEFAULT_SETTINGS: AppSettings = {
  llm: { openai_api_key: null, anthropic_api_key: null, ollama_endpoint: 'http://localhost:11434' },
  routing: { simple_threshold: 0.3, complex_threshold: 0.7, simple_model: 'llama3:8b', complex_model: 'gpt-4' },
  sandbox: { timeout_seconds: 30, memory_limit_mb: 512, max_retries: 3 },
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings>(DEFAULT_SETTINGS)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [loading, setLoading] = useState(true)
  const [dirty, setDirty] = useState(false)

  useEffect(() => {
    getSettings()
      .then((s) => { setSettings(s); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const updateField = useCallback(<K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    setSettings((s) => ({ ...s, [key]: value }))
    setDirty(true)
    setSaved(false)
  }, [])

  const handleSave = useCallback(async () => {
    setSaving(true)
    try {
      const updated = await updateSettings(settings)
      setSettings(updated)
      setDirty(false)
      setSaved(true)
      toast.success('Settings saved successfully')
      setTimeout(() => setSaved(false), 3000)
    } catch (e) {
      toast.error(`Failed to save: ${e}`)
    } finally {
      setSaving(false)
    }
  }, [settings])

  const handleReset = useCallback(() => {
    setSettings(DEFAULT_SETTINGS)
    setDirty(true)
    setSaved(false)
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full gap-3">
        <Loader2 className="w-5 h-5 animate-spin text-primary" />
        <span className="text-sm text-muted-foreground">Loading settings...</span>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-400 shadow-lg shadow-emerald-500/20">
            <Settings className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">Settings</h1>
            <p className="text-xs text-muted-foreground">
              Configure LLM providers, routing, and sandbox execution
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleReset}
            className="gap-1.5 rounded-xl text-xs"
          >
            <RotateCcw className="w-3 h-3" />
            Reset
          </Button>
          <Button
            size="sm"
            onClick={handleSave}
            disabled={saving || !dirty}
            className="gap-1.5 rounded-xl text-xs min-w-[120px]"
          >
            {saving ? (
              <>
                <Loader2 className="w-3 h-3 animate-spin" />
                Saving...
              </>
            ) : saved ? (
              <>
                <CheckCircle2 className="w-3 h-3 text-emerald-300" />
                Saved
              </>
            ) : (
              <>
                <Save className="w-3 h-3" />
                Save Settings
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Unsaved changes indicator */}
      {dirty && (
        <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-2.5 flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
          <p className="text-xs text-amber-400/80">You have unsaved changes</p>
        </div>
      )}

      {/* Tabs */}
      <Tabs defaultValue="llm" className="space-y-4">
        <TabsList className="bg-muted/30 border border-border/30 rounded-xl p-1 h-auto">
          <TabsTrigger
            value="llm"
            className="gap-2 rounded-lg text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm px-4 py-2.5"
          >
            <Cpu className="w-3.5 h-3.5" />
            LLM Providers
          </TabsTrigger>
          <TabsTrigger
            value="routing"
            className="gap-2 rounded-lg text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm px-4 py-2.5"
          >
            <Route className="w-3.5 h-3.5" />
            Routing
          </TabsTrigger>
          <TabsTrigger
            value="sandbox"
            className="gap-2 rounded-lg text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm px-4 py-2.5"
          >
            <Shield className="w-3.5 h-3.5" />
            Sandbox
          </TabsTrigger>
        </TabsList>

        <TabsContent value="llm">
          <div className="rounded-2xl border border-border/20 bg-card/30 backdrop-blur-md p-5 card-futuristic space-y-4">
            <div>
              <h3 className="text-sm font-semibold mb-1">LLM Provider Configuration</h3>
              <p className="text-xs text-muted-foreground">
                Add API keys for cloud providers or configure a local Ollama endpoint. At least one provider is required.
              </p>
            </div>
            <LLMProviderForm
              value={settings.llm}
              onChange={(llm) => updateField('llm', llm)}
            />
          </div>
        </TabsContent>

        <TabsContent value="routing">
          <div className="rounded-2xl border border-border/20 bg-card/30 backdrop-blur-md p-5 card-futuristic space-y-4">
            <div>
              <h3 className="text-sm font-semibold mb-1">Model Routing</h3>
              <p className="text-xs text-muted-foreground">
                Control how tasks are routed to models based on complexity. Simple tasks use cheaper models, complex tasks escalate to more capable ones.
              </p>
            </div>
            <RoutingConfig
              value={settings.routing}
              onChange={(routing) => updateField('routing', routing)}
            />
          </div>
        </TabsContent>

        <TabsContent value="sandbox">
          <div className="rounded-2xl border border-border/20 bg-card/30 backdrop-blur-md p-5 card-futuristic space-y-4">
            <div>
              <h3 className="text-sm font-semibold mb-1">Sandbox Execution</h3>
              <p className="text-xs text-muted-foreground">
                Configure the isolated sandbox where generated code is executed. Controls timeout limits, memory allocation, and retry behavior.
              </p>
            </div>
            <SandboxConfig
              value={settings.sandbox}
              onChange={(sandbox) => updateField('sandbox', sandbox)}
            />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
