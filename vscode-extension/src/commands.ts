/**
 * Command implementations for KeepContext AI extension.
 */

import * as vscode from 'vscode';
import { ApiClient, ApiClientError } from './apiClient';
import type { MemoryEntry, MemoryType } from './types';
import { MemoryTreeProvider } from './memoryTreeProvider';

// ---------------------------------------------------------------------------
// Store memory (manual input)
// ---------------------------------------------------------------------------

export async function storeMemory(
    client: ApiClient,
    treeProvider: MemoryTreeProvider,
): Promise<void> {
    const content = await vscode.window.showInputBox({
        prompt: 'Enter the memory content to store',
        placeHolder: 'e.g. Auth uses JWT with RS256 signing',
        ignoreFocusOut: true,
    });
    if (!content) {
        return;
    }

    const memoryType = await vscode.window.showQuickPick(
        ['code', 'decision', 'documentation', 'conversation'],
        { placeHolder: 'Select memory type' },
    );
    if (!memoryType) {
        return;
    }

    try {
        await client.storeMemory({
            content,
            memory_type: memoryType as MemoryType,
        });
        vscode.window.showInformationMessage('✅ Memory stored successfully');
        treeProvider.refresh();
    } catch (err) {
        showError('storing memory', err);
    }
}

// ---------------------------------------------------------------------------
// Store selection as memory
// ---------------------------------------------------------------------------

export async function storeSelection(
    client: ApiClient,
    treeProvider: MemoryTreeProvider,
): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('No active editor');
        return;
    }

    const selection = editor.document.getText(editor.selection);
    if (!selection.trim()) {
        vscode.window.showWarningMessage('No text selected');
        return;
    }

    const memoryType = await vscode.window.showQuickPick(
        ['code', 'decision', 'documentation', 'conversation'],
        { placeHolder: 'Select memory type for this selection' },
    );
    if (!memoryType) {
        return;
    }

    try {
        const fileName = editor.document.fileName;
        await client.storeMemory({
            content: selection,
            memory_type: memoryType as MemoryType,
            metadata: { source_file: fileName },
        });
        vscode.window.showInformationMessage('✅ Selection stored as memory');
        treeProvider.refresh();
    } catch (err) {
        showError('storing selection', err);
    }
}

// ---------------------------------------------------------------------------
// Query context
// ---------------------------------------------------------------------------

export async function queryContext(client: ApiClient): Promise<void> {
    const query = await vscode.window.showInputBox({
        prompt: 'Enter your context query',
        placeHolder: 'e.g. How does authentication work?',
        ignoreFocusOut: true,
    });
    if (!query) {
        return;
    }

    try {
        const results = await client.queryContext({ query, top_k: 10 });

        if (results.length === 0) {
            vscode.window.showInformationMessage('No relevant context found');
            return;
        }

        const items = results.map((r) => ({
            label: r.entry.content.substring(0, 80),
            description: `${r.entry.memory_type} • score: ${r.score.toFixed(2)}`,
            detail: r.entry.content,
        }));

        await vscode.window.showQuickPick(items, {
            placeHolder: `${results.length} results found`,
            matchOnDetail: true,
        });
    } catch (err) {
        showError('querying context', err);
    }
}

// ---------------------------------------------------------------------------
// Ask question (enriched context + LLM)
// ---------------------------------------------------------------------------

export async function askQuestion(client: ApiClient): Promise<void> {
    const query = await vscode.window.showInputBox({
        prompt: 'Ask a question about your project',
        placeHolder: 'e.g. What architecture patterns do we use?',
        ignoreFocusOut: true,
    });
    if (!query) {
        return;
    }

    await vscode.window.withProgress(
        {
            location: vscode.ProgressLocation.Notification,
            title: 'KeepContext: Thinking…',
            cancellable: false,
        },
        async () => {
            try {
                const result = await client.ask({ query, use_llm: true });

                const doc = await vscode.workspace.openTextDocument({
                    language: 'markdown',
                    content: formatAskResponse(query, result),
                });
                await vscode.window.showTextDocument(doc, { preview: true });
            } catch (err) {
                showError('asking question', err);
            }
        },
    );
}

function formatAskResponse(
    query: string,
    result: { llm_response: string | null; memory_results: Array<{ entry: { content: string }; score: number }> },
): string {
    const parts: string[] = [`# 💡 KeepContext AI Answer\n`, `**Question:** ${query}\n`];

    if (result.llm_response) {
        parts.push(`## Answer\n\n${result.llm_response}\n`);
    }

    if (result.memory_results.length > 0) {
        parts.push(`## Relevant Memories (${result.memory_results.length})\n`);
        for (const r of result.memory_results) {
            parts.push(`- (${r.score.toFixed(2)}) ${r.entry.content}`);
        }
    }

    return parts.join('\n');
}

// ---------------------------------------------------------------------------
// Run agent workflow
// ---------------------------------------------------------------------------

export async function runAgent(client: ApiClient): Promise<void> {
    const goal = await vscode.window.showInputBox({
        prompt: 'Describe what you want to build or accomplish',
        placeHolder: 'e.g. Add a caching layer with Redis for the memory service',
        ignoreFocusOut: true,
    });
    if (!goal) {
        return;
    }

    const config = vscode.workspace.getConfiguration('keepcontext');
    const maxIterations = config.get<number>('agentMaxIterations', 3);

    await vscode.window.withProgress(
        {
            location: vscode.ProgressLocation.Notification,
            title: 'KeepContext Agent: Working…',
            cancellable: false,
        },
        async () => {
            try {
                const result = await client.runAgent({
                    goal,
                    max_iterations: maxIterations,
                });

                const doc = await vscode.workspace.openTextDocument({
                    language: 'markdown',
                    content: formatAgentResponse(result),
                });
                await vscode.window.showTextDocument(doc, { preview: true });
            } catch (err) {
                showError('running agent', err);
            }
        },
    );
}

function formatAgentResponse(result: {
    goal: string;
    plan: { goal: string; steps: Array<{ step_number: number; description: string }>; architecture_notes: string } | null;
    code_outputs: Array<{ filename: string; language: string; code: string; explanation: string }>;
    review: { approved: boolean; issues: Array<{ severity: string; description: string }>; summary: string } | null;
    final_response: string;
    iterations_used: number;
}): string {
    const parts: string[] = [
        `# 🤖 KeepContext Agent Result\n`,
        `**Goal:** ${result.goal}`,
        `**Iterations:** ${result.iterations_used}\n`,
    ];

    if (result.plan) {
        parts.push(`## 📋 Plan\n`);
        for (const step of result.plan.steps) {
            parts.push(`${step.step_number}. ${step.description}`);
        }
        if (result.plan.architecture_notes) {
            parts.push(`\n> ${result.plan.architecture_notes}`);
        }
        parts.push('');
    }

    if (result.code_outputs.length > 0) {
        parts.push(`## 💻 Generated Code\n`);
        for (const output of result.code_outputs) {
            parts.push(`### ${output.filename}\n`);
            parts.push(`\`\`\`${output.language}`);
            parts.push(output.code);
            parts.push('```\n');
            if (output.explanation) {
                parts.push(`> ${output.explanation}\n`);
            }
        }
    }

    if (result.review) {
        const status = result.review.approved ? '✅ Approved' : '❌ Needs Revision';
        parts.push(`## 🔍 Review: ${status}\n`);
        parts.push(result.review.summary);
        for (const issue of result.review.issues) {
            parts.push(`- **[${issue.severity}]** ${issue.description}`);
        }
        parts.push('');
    }

    return parts.join('\n');
}

// ---------------------------------------------------------------------------
// Delete memory
// ---------------------------------------------------------------------------

export async function deleteMemory(
    client: ApiClient,
    treeProvider: MemoryTreeProvider,
    memory: MemoryEntry,
): Promise<void> {
    const confirm = await vscode.window.showWarningMessage(
        `Delete memory "${memory.content.substring(0, 50)}…"?`,
        { modal: true },
        'Delete',
    );
    if (confirm !== 'Delete') {
        return;
    }

    try {
        await client.deleteMemory(memory.id);
        vscode.window.showInformationMessage('Memory deleted');
        treeProvider.refresh();
    } catch (err) {
        showError('deleting memory', err);
    }
}

// ---------------------------------------------------------------------------
// Show memory detail (click from tree)
// ---------------------------------------------------------------------------

export async function showMemoryDetail(memory: MemoryEntry): Promise<void> {
    const content = [
        `# Memory: ${memory.id}\n`,
        `**Type:** ${memory.memory_type}`,
        `**Created:** ${memory.created_at}\n`,
        `## Content\n`,
        memory.content,
        `\n## Metadata\n`,
        '```json',
        JSON.stringify(memory.metadata, null, 2),
        '```',
    ].join('\n');

    const doc = await vscode.workspace.openTextDocument({
        language: 'markdown',
        content,
    });
    await vscode.window.showTextDocument(doc, { preview: true });
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function showError(action: string, err: unknown): void {
    const msg =
        err instanceof ApiClientError
            ? err.message
            : err instanceof Error
              ? err.message
              : String(err);
    vscode.window.showErrorMessage(`KeepContext: Error ${action} — ${msg}`);
}
