'use client'

import { Suspense, useEffect, useRef } from 'react'
import { useSearchParams } from 'next/navigation'
import { ChatInput } from '@/components/chat/ChatInput'
import { TaskStream } from '@/components/chat/TaskStream'
import { Button } from '@/components/ui/button'
import { useTask } from '@/hooks/useTask'
import { RotateCcw, GitBranch } from 'lucide-react'

function ChatPageInner() {
  const searchParams = useSearchParams()
  const initialPrompt = searchParams.get('prompt') || undefined
  const consumedRef = useRef(false)

  const {
    submitTask, cancelTask, approveTask, submitAnswers, skipQuestions,
    isLoading, error, events, taskDetail, reset,
    awaitingApproval, awaitingAnswers, planData,
    researchFindings, questions,
  } = useTask()

  // Auto-submit if navigated with ?prompt= from history re-run
  useEffect(() => {
    if (initialPrompt && !consumedRef.current) {
      consumedRef.current = true
      submitTask(initialPrompt)
      window.history.replaceState({}, '', '/')
    }
  }, [initialPrompt, submitTask])

  // After task completes, typing in the input refines the previous code
  const completedCode = taskDetail?.final_code || null
  const canRefine = !isLoading && !!completedCode

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-background to-background/95">
      <div className="flex-1 overflow-auto">
        <TaskStream
          events={events}
          isLoading={isLoading}
          taskDetail={taskDetail}
          awaitingApproval={awaitingApproval}
          awaitingAnswers={awaitingAnswers}
          planData={planData}
          researchFindings={researchFindings}
          questions={questions}
          onApprove={approveTask}
          onReject={cancelTask}
          onHintClick={submitTask}
          onSubmitAnswers={submitAnswers}
          onSkipQuestions={skipQuestions}
        />
      </div>
      {error && (
        <div className="mx-6 mb-3 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3 backdrop-blur-sm">
          <p className="text-sm text-red-400 font-mono">{error}</p>
        </div>
      )}
      {taskDetail && !isLoading && (
        <div className="flex items-center justify-center gap-3 py-2">
          {canRefine && (
            <span className="text-[10px] text-muted-foreground/60 flex items-center gap-1">
              <GitBranch className="w-3 h-3" />
              Type below to refine, or
            </span>
          )}
          <Button variant="outline" size="sm" onClick={reset} className="gap-2 rounded-xl">
            <RotateCcw className="w-3.5 h-3.5" />
            New Task
          </Button>
        </div>
      )}
      <ChatInput
        onSubmit={submitTask}
        onCancel={cancelTask}
        disabled={isLoading && !awaitingApproval && !awaitingAnswers}
        showCancel={isLoading && !awaitingApproval && !awaitingAnswers}
        contextCode={canRefine ? completedCode : null}
      />
    </div>
  )
}

export default function ChatPage() {
  return (
    <Suspense>
      <ChatPageInner />
    </Suspense>
  )
}
