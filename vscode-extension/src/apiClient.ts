/**
 * HTTP client for the KeepContext AI backend API.
 *
 * All methods throw {@link ApiClientError} on failure.
 */

import * as vscode from 'vscode';
import type {
    AgentPlanRequest,
    AgentResponse,
    AgentRunRequest,
    AskRequest,
    AskResponse,
    ContextQueryRequest,
    ContextResult,
    HealthResponse,
    MemoryCreateRequest,
    MemoryEntry,
    MemoryListResponse,
} from './types';

// ---------------------------------------------------------------------------
// Error
// ---------------------------------------------------------------------------

export class ApiClientError extends Error {
    constructor(
        message: string,
        public readonly statusCode: number = 0,
        public readonly code: string = 'client_error',
    ) {
        super(message);
        this.name = 'ApiClientError';
    }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

export class ApiClient {
    private get baseUrl(): string {
        return vscode.workspace
            .getConfiguration('keepcontext')
            .get<string>('apiUrl', 'http://localhost:8003');
    }

    // -- helpers --

    private async request<T>(
        method: string,
        path: string,
        body?: unknown,
    ): Promise<T> {
        const url = `${this.baseUrl}${path}`;

        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        };

        const options: RequestInit = { method, headers };
        if (body !== undefined) {
            options.body = JSON.stringify(body);
        }

        let response: Response;
        try {
            response = await fetch(url, options);
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : String(err);
            throw new ApiClientError(
                `Cannot reach KeepContext AI at ${this.baseUrl}: ${msg}`,
            );
        }

        if (!response.ok) {
            let detail = response.statusText;
            try {
                const errBody = (await response.json()) as { error?: { message?: string } };
                detail = errBody?.error?.message ?? detail;
            } catch {
                // ignore parse failures
            }
            throw new ApiClientError(detail, response.status);
        }

        return (await response.json()) as T;
    }

    // -- health --

    async health(): Promise<HealthResponse> {
        return this.request<HealthResponse>('GET', '/health');
    }

    // -- memory --

    async storeMemory(req: MemoryCreateRequest): Promise<MemoryEntry> {
        const res = await this.request<{ data: MemoryEntry }>(
            'POST',
            '/api/v1/memory',
            req,
        );
        return res.data;
    }

    async listMemories(
        page: number = 1,
        perPage: number = 20,
        memoryType?: string,
    ): Promise<MemoryListResponse> {
        let path = `/api/v1/memory?page=${page}&per_page=${perPage}`;
        if (memoryType) {
            path += `&memory_type=${memoryType}`;
        }
        return this.request<MemoryListResponse>('GET', path);
    }

    async getMemory(id: string): Promise<MemoryEntry> {
        const res = await this.request<{ data: MemoryEntry }>(
            'GET',
            `/api/v1/memory/${id}`,
        );
        return res.data;
    }

    async deleteMemory(id: string): Promise<void> {
        await this.request<unknown>('DELETE', `/api/v1/memory/${id}`);
    }

    // -- context --

    async queryContext(req: ContextQueryRequest): Promise<ContextResult[]> {
        const res = await this.request<{ data: ContextResult[] }>(
            'POST',
            '/api/v1/context/query',
            req,
        );
        return res.data;
    }

    // -- ask --

    async ask(req: AskRequest): Promise<AskResponse> {
        const res = await this.request<{ data: AskResponse }>('POST', '/api/v1/ask', req);
        return res.data;
    }

    // -- agents --

    async runAgent(req: AgentRunRequest): Promise<AgentResponse> {
        return this.request<AgentResponse>('POST', '/api/v1/agents/run', req);
    }

    async planOnly(req: AgentPlanRequest): Promise<{ goal: string; plan: unknown; context_used: number }> {
        return this.request('POST', '/api/v1/agents/plan', req);
    }

    async reviewCode(
        goal: string,
        codeOutputs: Array<Record<string, unknown>>,
    ): Promise<{ goal: string; review: unknown }> {
        return this.request('POST', '/api/v1/agents/review', {
            goal,
            code_outputs: codeOutputs,
        });
    }
}
