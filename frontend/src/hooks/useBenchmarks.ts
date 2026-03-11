'use client'

import { useCallback, useEffect, useState } from 'react'
import { getBenchmarkRun, getBenchmarkRuns, triggerBenchmark } from '@/lib/api'
import type { BenchmarkRun, BenchmarkRunDetail } from '@/lib/types'

interface UseBenchmarksReturn {
  runs: BenchmarkRun[]
  currentRun: BenchmarkRunDetail | null
  isLoading: boolean
  error: string | null
  triggerRun: (type: string, withRepair?: boolean) => Promise<void>
  selectRun: (runId: string) => Promise<void>
  refresh: () => Promise<void>
}

export function useBenchmarks(): UseBenchmarksReturn {
  const [runs, setRuns] = useState<BenchmarkRun[]>([])
  const [currentRun, setCurrentRun] = useState<BenchmarkRunDetail | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      const data = await getBenchmarkRuns()
      setRuns(data)
    } catch (err) {
      setError(String(err))
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const triggerRun = useCallback(
    async (type: string, withRepair = true) => {
      setIsLoading(true)
      setError(null)
      try {
        const run = await triggerBenchmark(type, withRepair)
        setRuns((prev) => [run, ...prev])
      } catch (err) {
        setError(String(err))
      } finally {
        setIsLoading(false)
      }
    },
    [],
  )

  const selectRun = useCallback(async (runId: string) => {
    setIsLoading(true)
    try {
      const detail = await getBenchmarkRun(runId)
      setCurrentRun(detail)
    } catch (err) {
      setError(String(err))
    } finally {
      setIsLoading(false)
    }
  }, [])

  return { runs, currentRun, isLoading, error, triggerRun, selectRun, refresh }
}
