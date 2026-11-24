// Mirrors docs/CONTRACTS.md (backend API + investigation report).
export type FindingStatus = 'confirmed' | 'likely' | 'hypothesis' | 'unknown'
export type InvStatus = 'queued' | 'investigating' | 'partial' | 'awaiting_approval' | 'completed' | 'failed' | 'cancelled'

export interface Evidence {
  evidence_id: string
  claim: string
  status: FindingStatus
  source_system: 'orders' | 'inventory'
  source_tool: string
  source_endpoint: string
  entity_ids: string[]
  observed_at: string
  data: Record<string, unknown>
}

export interface Finding {
  finding_id: string
  title: string
  summary: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  status: FindingStatus
  evidence_ids: string[]
  confidence_explanation: string
  impact_metrics: Record<string, number>
}

export interface Action {
  action_id: string
  action_type: string
  description: string
  inputs: Record<string, unknown>
  affected_entities: string[]
  risk_level: 'high' | 'medium' | 'low'
  evidence_ids: string[]
  expected_outcome: string
  requires_approval: boolean
  approval_status: 'pending' | 'approved' | 'rejected' | 'not_required'
}

export interface ToolEvent { seq: number; server: string; tool: string; args: Record<string, unknown>; ok: boolean; ms: number; summary: string }
export interface Metric { value: number; definition: string }

export interface Priority {
  rank: number; order_id: string; customer_id: string; customer_name: string; tier: string; score: number
  reasons: string[]; has_open_complaint: boolean; quantity: number; total_amount: number
  sla_breached: boolean; recoverable_by_transfer: boolean
}

export interface Report {
  request: string
  status: InvStatus
  as_of: string
  findings: Finding[]
  evidence: Evidence[]
  impact: Record<string, Metric> | null
  priorities: Priority[] | null
  transfer: { recovered_order_ids: string[]; unrecovered_order_ids: string[]; units_allocated: number; units_unused: number } | null
  transfer_plan: { product_id: string; source: string; destination: string; units: number } | null
  actions: Action[]
  gaps: string[]
  trace: ToolEvent[]
  prioritization_weights: Record<string, number>
  narrative: { text: string | null; source: 'llm' | 'template' | 'pending'; model: string | null; error: string | null }
}

export interface StreamEvent { type: string; at: string; [k: string]: unknown }

export interface InvestigationSummary {
  id: string; request: string; status: InvStatus; created_at: string; completed_at: string | null
  headline?: string | null; pending_actions?: number
}
export interface Investigation extends InvestigationSummary { report: Report | null; events: StreamEvent[] }

export interface Overview {
  orders: { total_orders: number; by_status: Record<string, number>; delayed_orders: number; delayed_customers: number
    delayed_by_reason: Record<string, number>; sla_breached_orders: number; at_risk_orders: number
    delayed_order_value: number; open_tickets: number; open_delay_tickets: number; as_of: string } | null
  stock: { low_stock_positions: number; out_of_stock_positions: number; failed_syncs: number
    products_affected_by_sync_failures: string[]; warehouses_by_status: Record<string, number> } | null
  sync: { sync_id: string; source: string; warehouse_id: string; status: string; failing_since: string | null
    last_success: string; error_code: string | null; error_message: string | null; affected_products: string[]; severity: string }[] | null
  low_stock: { product_id: string; warehouse_id: string; available_quantity: number; reorder_threshold: number; shortfall: number }[] | null
  errors: string[]
  latest_investigation: (InvestigationSummary & { impact: Record<string, Metric> | null }) | null
}

export interface SystemInfo {
  name: string; repo: string; server_id: string; base_url: string
  api: { healthy: boolean; endpoint_count: number | null; error: string | null }
  mcp: { connected: boolean; tool_count: number; tools: { name: string; description: string; new: boolean; params: string[] }[]
    error: string | null; connect_ms: number | null }
  last_discovery: string | null
}
