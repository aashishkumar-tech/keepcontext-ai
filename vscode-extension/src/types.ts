/**
 * Type definitions for KeepContext AI API responses.
 */

// ---------------------------------------------------------------------------
// Memory
// ---------------------------------------------------------------------------

export type MemoryType = 'conversation' | 'code' | 'decision' | 'documentation';

export interface MemoryEntry {
    id: string;
    content: string;
    memory_type: MemoryType;
    metadata: Record<string, unknown>;
    created_at: string;
}

export interface MemoryCreateRequest {
    content: string;
    memory_type: MemoryType;
    metadata?: Record<string, unknown>;
}

export interface MemoryListResponse {
    data: MemoryEntry[];
    meta: {
        total: number;
        page: number;
        per_page: number;
    };
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

export interface ContextQueryRequest {
    query: string;
    top_k?: number;
    memory_type?: MemoryType;
}

export interface ContextResult {
    entry: MemoryEntry;
    score: number;
}

export interface ContextQueryResponse {
    data: ContextResult[];
}

// ---------------------------------------------------------------------------
// Ask
// ---------------------------------------------------------------------------

export interface AskRequest {
    query: string;
    top_k?: number;
    entity_name?: string;
    use_llm?: boolean;
}

export interface AskResponse {
    memory_results: ContextResult[];
    graph_context: {
        entities: unknown[];
        relationships: unknown[];
    };
    llm_response: string | null;
}

// ---------------------------------------------------------------------------
// Agents
// ---------------------------------------------------------------------------

export interface AgentRunRequest {
    goal: string;
    max_iterations?: number;
}

export interface AgentPlanRequest {
    goal: string;
    entity_name?: string;
}

export interface CodeOutput {
    filename: string;
    language: string;
    code: string;
    explanation: string;
}

export interface ReviewIssue {
    severity: 'critical' | 'warning' | 'suggestion';
    description: string;
    suggestion: string;
}

export interface ReviewResult {
    approved: boolean;
    issues: ReviewIssue[];
    summary: string;
}

export interface TaskStep {
    step_number: number;
    description: string;
    details: string;
}

export interface TaskPlan {
    goal: string;
    steps: TaskStep[];
    architecture_notes: string;
}

export interface AgentResponse {
    goal: string;
    plan: TaskPlan | null;
    code_outputs: CodeOutput[];
    review: ReviewResult | null;
    final_response: string;
    iterations_used: number;
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

export interface HealthResponse {
    status: string;
    version: string;
    chromadb: string;
}

// ---------------------------------------------------------------------------
// Error
// ---------------------------------------------------------------------------

export interface ApiError {
    error: {
        code: string;
        message: string;
    };
}
