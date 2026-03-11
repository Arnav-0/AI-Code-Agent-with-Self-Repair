'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Bot,
  MessageSquare,
  History,
  BarChart3,
  Wrench,
  Settings,
  PanelLeftClose,
  PanelLeft,
  Moon,
  Sun,
  Zap,
} from 'lucide-react'
import { useTheme } from 'next-themes'
import { cn } from '@/lib/utils'

const navItems = [
  { href: '/agent', icon: Bot, label: 'Agent', gradient: 'from-violet-500 to-indigo-400', glow: 'shadow-violet-500/20' },
  { href: '/', icon: MessageSquare, label: 'Chat', gradient: 'from-blue-500 to-cyan-400', glow: 'shadow-blue-500/20' },
  { href: '/history', icon: History, label: 'History', gradient: 'from-purple-500 to-pink-400', glow: 'shadow-purple-500/20' },
  { href: '/analytics', icon: Wrench, label: 'Self-Repair', gradient: 'from-orange-500 to-red-400', glow: 'shadow-orange-500/20' },
  { href: '/benchmarks', icon: BarChart3, label: 'Benchmarks', gradient: 'from-amber-500 to-yellow-400', glow: 'shadow-amber-500/20' },
  { href: '/settings', icon: Settings, label: 'Settings', gradient: 'from-emerald-500 to-teal-400', glow: 'shadow-emerald-500/20' },
]

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const [mounted, setMounted] = useState(false)
  const pathname = usePathname()
  const { theme, setTheme } = useTheme()

  useEffect(() => setMounted(true), [])

  return (
    <aside
      className={cn(
        'flex flex-col h-screen border-r border-border/30 transition-all duration-300 ease-in-out relative',
        'bg-gradient-to-b from-sidebar via-sidebar to-sidebar/90',
        collapsed ? 'w-[68px]' : 'w-[260px]'
      )}
    >
      {/* Ambient sidebar edge glow */}
      <div className="absolute top-0 right-0 w-px h-full bg-gradient-to-b from-primary/20 via-purple-500/10 to-transparent" />

      {/* Logo */}
      <div className={cn(
        'flex items-center gap-3 px-5 h-16 border-b border-border/30',
        collapsed && 'justify-center px-0'
      )}>
        <div className="relative flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-primary via-purple-500 to-cyan-400 shadow-lg shadow-primary/30">
          <Zap className="w-4.5 h-4.5 text-white" />
          <div className="absolute -inset-1 bg-gradient-to-br from-primary/20 to-cyan-400/20 rounded-2xl blur-md -z-10 breathe" />
        </div>
        {!collapsed && (
          <div className="flex flex-col">
            <span className="font-bold text-base tracking-tight leading-none gradient-text">CodeForge</span>
            <span className="text-[10px] text-muted-foreground/60 leading-none mt-1 font-mono tracking-wider">AI CODE AGENT</span>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        {!collapsed && (
          <span className="text-[9px] font-bold uppercase tracking-[0.2em] text-muted-foreground/40 px-3 mb-2.5 block font-mono">
            Navigation
          </span>
        )}
        {navItems.map(({ href, icon: Icon, label, gradient, glow }) => {
          const isActive = pathname === href
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                'group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 relative',
                isActive
                  ? 'bg-primary/[0.08] text-primary'
                  : 'text-muted-foreground hover:text-foreground holo-hover',
                collapsed && 'justify-center px-0'
              )}
              title={collapsed ? label : undefined}
            >
              {/* Active indicator bar */}
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full bg-gradient-to-b from-primary to-cyan-400" />
              )}

              <div className={cn(
                'flex items-center justify-center w-8 h-8 rounded-lg transition-all duration-200',
                isActive
                  ? `bg-gradient-to-br ${gradient} shadow-md ${glow}`
                  : 'bg-transparent group-hover:bg-muted/50'
              )}>
                <Icon className={cn(
                  'w-4 h-4 transition-colors',
                  isActive ? 'text-white' : 'text-current'
                )} />
              </div>
              {!collapsed && <span className={cn(isActive && 'font-semibold')}>{label}</span>}
              {!collapsed && isActive && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-primary shadow-sm shadow-primary/50" />
              )}
            </Link>
          )
        })}
      </nav>

      {/* Bottom controls */}
      <div className="p-3 border-t border-border/30 space-y-1">
        {mounted && (
          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className={cn(
              'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-muted-foreground',
              'hover:text-foreground holo-hover transition-all duration-200 w-full',
              collapsed && 'justify-center px-0'
            )}
            title="Toggle theme"
          >
            <div className="flex items-center justify-center w-8 h-8 rounded-lg">
              {theme === 'dark' ? (
                <Sun className="w-4 h-4" />
              ) : (
                <Moon className="w-4 h-4" />
              )}
            </div>
            {!collapsed && <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>}
          </button>
        )}

        <button
          onClick={() => setCollapsed(!collapsed)}
          className={cn(
            'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-muted-foreground',
            'hover:text-foreground holo-hover transition-all duration-200 w-full',
            collapsed && 'justify-center px-0'
          )}
          title={collapsed ? 'Expand' : 'Collapse'}
        >
          <div className="flex items-center justify-center w-8 h-8 rounded-lg">
            {collapsed ? <PanelLeft className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
          </div>
          {!collapsed && <span>Collapse</span>}
        </button>
      </div>
    </aside>
  )
}
