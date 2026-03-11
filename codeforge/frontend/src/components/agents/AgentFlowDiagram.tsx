'use client'

import { useCallback, useMemo } from 'react'
import ReactFlow, {
  type Node,
  type Edge,
  Background,
  MarkerType,
  type NodeTypes,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { cn } from '@/lib/utils'

interface FlowNodeData {
  label: string
  nodeType: 'start' | 'agent' | 'success' | 'failed'
  active?: boolean
  completed?: boolean
  error?: boolean
}

function FlowNode({ data }: { data: FlowNodeData }) {
  return (
    <div
      className={cn(
        'px-4 py-2 rounded-xl border text-[11px] font-semibold transition-all min-w-[84px] text-center shadow-sm',
        data.nodeType === 'start' && 'rounded-full bg-sky-500/15 border-sky-500/30 text-sky-300',
        data.nodeType === 'agent' && 'bg-card/80 border-border/60 text-foreground',
        data.nodeType === 'success' && 'rounded-full bg-emerald-500/15 border-emerald-500/30 text-emerald-300',
        data.nodeType === 'failed' && 'rounded-full bg-red-500/15 border-red-500/30 text-red-300',
        data.active && 'border-primary shadow-[0_0_16px_rgba(99,102,241,0.4)] ring-1 ring-primary/30 animate-pulse scale-110',
        data.completed && 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300',
        data.error && 'border-red-500/40 bg-red-500/10 text-red-300',
      )}
    >
      {data.active && (
        <div className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-primary animate-ping" />
      )}
      {data.completed && (
        <div className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-emerald-400" />
      )}
      {data.label}
    </div>
  )
}

const nodeTypes: NodeTypes = { custom: FlowNode }

const INITIAL_NODES: Node<FlowNodeData>[] = [
  { id: 'classify', type: 'custom', position: { x: 160, y: 15 }, data: { label: 'Classify', nodeType: 'start' } },
  { id: 'researcher', type: 'custom', position: { x: 160, y: 75 }, data: { label: 'Research', nodeType: 'agent' } },
  { id: 'questioner', type: 'custom', position: { x: 160, y: 135 }, data: { label: 'Q&A', nodeType: 'agent' } },
  { id: 'planner', type: 'custom', position: { x: 160, y: 195 }, data: { label: 'Planner', nodeType: 'agent' } },
  { id: 'coder', type: 'custom', position: { x: 160, y: 255 }, data: { label: 'Coder', nodeType: 'agent' } },
  { id: 'executor', type: 'custom', position: { x: 160, y: 315 }, data: { label: 'Executor', nodeType: 'agent' } },
  { id: 'complete', type: 'custom', position: { x: 30, y: 395 }, data: { label: 'Complete', nodeType: 'success' } },
  { id: 'reviewer', type: 'custom', position: { x: 300, y: 395 }, data: { label: 'Reviewer', nodeType: 'agent' } },
  { id: 'failed', type: 'custom', position: { x: 420, y: 315 }, data: { label: 'Failed', nodeType: 'failed' } },
]

const INITIAL_EDGES: Edge[] = [
  { id: 'e0', source: 'classify', target: 'researcher', markerEnd: { type: MarkerType.ArrowClosed }, animated: false },
  { id: 'e0b', source: 'researcher', target: 'questioner', markerEnd: { type: MarkerType.ArrowClosed }, animated: false },
  { id: 'e1', source: 'questioner', target: 'planner', markerEnd: { type: MarkerType.ArrowClosed }, animated: false },
  { id: 'e2', source: 'planner', target: 'coder', markerEnd: { type: MarkerType.ArrowClosed }, animated: false },
  { id: 'e3', source: 'coder', target: 'executor', markerEnd: { type: MarkerType.ArrowClosed }, animated: false },
  { id: 'e4', source: 'executor', target: 'complete', label: 'pass', style: { stroke: '#4ade80' }, markerEnd: { type: MarkerType.ArrowClosed, color: '#4ade80' } },
  { id: 'e5', source: 'executor', target: 'reviewer', label: 'fail', style: { stroke: '#f87171' }, markerEnd: { type: MarkerType.ArrowClosed, color: '#f87171' } },
  { id: 'e6', source: 'reviewer', target: 'coder', label: 'retry', style: { stroke: '#fb923c', strokeDasharray: '4' }, markerEnd: { type: MarkerType.ArrowClosed, color: '#fb923c' } },
  { id: 'e7', source: 'reviewer', target: 'failed', label: 'max retries', style: { stroke: '#f87171', strokeDasharray: '4' }, markerEnd: { type: MarkerType.ArrowClosed, color: '#f87171' } },
]

// Order of nodes in the pipeline for "completed" state tracking
const NODE_ORDER = ['classify', 'researcher', 'questioner', 'planner', 'coder', 'executor', 'reviewer']

interface AgentFlowDiagramProps {
  activeAgent?: string | null
  status?: string
  retryCount?: number
}

export function AgentFlowDiagram({ activeAgent, status, retryCount }: AgentFlowDiagramProps) {
  const getNodeData = useCallback(
    (baseData: FlowNodeData, nodeId: string): FlowNodeData => {
      const isActive = activeAgent === nodeId
      const isCompleted = status === 'completed' && baseData.nodeType === 'success'
      const isFailed = status === 'failed' && baseData.nodeType === 'failed'

      // Mark nodes before the active one as completed (already passed through)
      const activeIdx = NODE_ORDER.indexOf(activeAgent || '')
      const nodeIdx = NODE_ORDER.indexOf(nodeId)
      const isPast = activeIdx > -1 && nodeIdx > -1 && nodeIdx < activeIdx

      // If task completed, mark all pipeline nodes as completed
      const allDone = status === 'completed' && nodeIdx > -1

      return {
        ...baseData,
        active: isActive,
        completed: isCompleted || isPast || allDone,
        error: isFailed,
      }
    },
    [activeAgent, status]
  )

  const nodes = useMemo(
    () => INITIAL_NODES.map((n) => ({
      ...n,
      data: getNodeData(n.data, n.id),
    })),
    [getNodeData]
  )

  // Animate edges leading to the active node
  const edges = useMemo(() => {
    const activeIdx = NODE_ORDER.indexOf(activeAgent || '')
    return INITIAL_EDGES.map((e) => {
      const sourceIdx = NODE_ORDER.indexOf(e.source)
      const targetIdx = NODE_ORDER.indexOf(e.target)
      // Animate the edge into the currently active node
      const shouldAnimate = activeIdx > -1 && targetIdx === activeIdx && sourceIdx === activeIdx - 1
      // Highlight edges for completed path
      const isCompletedEdge = activeIdx > -1 && sourceIdx > -1 && targetIdx > -1 && targetIdx <= activeIdx && sourceIdx < targetIdx
      const allDone = status === 'completed'
      return {
        ...e,
        animated: shouldAnimate,
        style: isCompletedEdge || allDone
          ? { ...e.style, stroke: e.style?.stroke || '#4ade80', strokeWidth: 2 }
          : e.style,
      }
    })
  }, [activeAgent, status])

  return (
    <div className="w-full h-[420px] rounded-2xl border border-border/20 overflow-hidden bg-[#060a10] relative shadow-xl shadow-black/10">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        panOnDrag={false}
        zoomOnScroll={false}
        zoomOnPinch={false}
        zoomOnDoubleClick={false}
        style={{ background: 'transparent' }}
        defaultEdgeOptions={{
          style: { stroke: '#3f3f46', strokeWidth: 1.5 },
          markerEnd: { type: MarkerType.ArrowClosed, color: '#3f3f46' },
        }}
      >
        <Background color="#1a1a2e" gap={20} size={0.5} />
      </ReactFlow>

      {/* Legend */}
      <div className="absolute bottom-2 left-2 flex items-center gap-3 text-[10px] text-muted-foreground bg-card/80 backdrop-blur-sm rounded-lg px-2.5 py-1 border border-border/30">
        <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" /> Active</span>
        <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Done</span>
        <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-red-400" /> Failed</span>
        {retryCount !== undefined && retryCount > 0 && (
          <span className="text-orange-400 font-medium">
            {retryCount} {retryCount === 1 ? 'retry' : 'retries'}
          </span>
        )}
      </div>

      {/* Title */}
      <div className="absolute top-2 left-3 text-[10px] font-semibold text-muted-foreground/60 uppercase tracking-wider">
        Agent Pipeline
      </div>
    </div>
  )
}
