'use client'

import { useEffect, useState } from 'react'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { checkHealth } from '@/lib/api'
import { Wifi, WifiOff, Radio } from 'lucide-react'

const pageTitles: Record<string, { title: string; subtitle: string }> = {
  '/': { title: 'Chat', subtitle: 'Generate and execute code with AI' },
  '/history': { title: 'History', subtitle: 'Browse past tasks and results' },
  '/benchmarks': { title: 'Benchmarks', subtitle: 'Evaluate model performance' },
  '/settings': { title: 'Settings', subtitle: 'Configure providers and sandbox' },
  '/analytics': { title: 'Self-Repair Analytics', subtitle: 'How effectively the AI debugs its own code failures' },
}

function ConnectionStatus({ connected }: { connected: boolean }) {
  return (
    <div className={cn(
      'flex items-center gap-2 px-3 py-1.5 rounded-full text-[11px] font-semibold transition-all font-mono tracking-wide',
      connected
        ? 'bg-emerald-500/[0.08] text-emerald-400 border border-emerald-500/20 shadow-sm shadow-emerald-500/10'
        : 'bg-red-500/[0.08] text-red-400 border border-red-500/20'
    )}>
      {connected ? (
        <>
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-40" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
          </span>
          <span>ONLINE</span>
        </>
      ) : (
        <>
          <WifiOff className="w-3 h-3" />
          <span>OFFLINE</span>
        </>
      )}
    </div>
  )
}

export function Header() {
  const pathname = usePathname()
  const page = pageTitles[pathname] ?? { title: 'CodeForge', subtitle: '' }
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    checkHealth().then(setConnected)
    const interval = setInterval(() => {
      checkHealth().then(setConnected)
    }, 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <header className="h-14 flex items-center justify-between px-6 glass flex-shrink-0 relative border-b border-border/30">
      {/* Gradient bottom border accent */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/20 to-transparent" />

      <div className="flex flex-col">
        <h1 className="font-semibold text-sm leading-none tracking-tight">{page.title}</h1>
        {page.subtitle && (
          <p className="text-[11px] text-muted-foreground/60 mt-1 leading-none font-mono">{page.subtitle}</p>
        )}
      </div>
      <ConnectionStatus connected={connected} />
    </header>
  )
}
