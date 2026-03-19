/**
 * GitHub Copilot Chat Participant for KeepContext AI.
 *
 * Registers `@keepcontext` in Copilot Chat so any chat session can
 * retrieve stored project context and persist new memories.
 *
 * Slash commands:
 *   /recall  <query>   — Search stored memories (default)
 *   /remember <text>   — Store a new memory
 *   /ask     <query>   — Ask with LLM + memory context
 */

import * as vscode from 'vscode';
import { ApiClient } from './apiClient';

const PARTICIPANT_ID = 'keepcontext-ai.context';

// ---------------------------------------------------------------------------
// Handler
// ---------------------------------------------------------------------------

export function registerChatParticipant(
    context: vscode.ExtensionContext,
    client: ApiClient,
): void {
    const handler: vscode.ChatRequestHandler = async (
        request: vscode.ChatRequest,
        chatContext: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken,
    ): Promise<vscode.ChatResult> => {
        const command = request.command ?? '';
        const prompt = request.prompt.trim();

        try {
            if (command === 'remember') {
                return await handleRemember(client, prompt, stream);
            }

            if (command === 'ask') {
                return await handleAsk(client, prompt, chatContext, stream, token);
            }

            // Default: /recall or no command — retrieve context
            return await handleRecall(client, prompt, chatContext, stream, token);
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : String(err);
            stream.markdown(
                `**KeepContext AI Error:** ${msg}\n\nMake sure the backend is running.`,
            );
            return { metadata: { command } };
        }
    };

    const participant = vscode.chat.createChatParticipant(PARTICIPANT_ID, handler);
    participant.iconPath = vscode.Uri.joinPath(context.extensionUri, 'media', 'icon.png');

    context.subscriptions.push(participant);
}

// ---------------------------------------------------------------------------
// /recall — Retrieve relevant memories
// ---------------------------------------------------------------------------

async function handleRecall(
    client: ApiClient,
    prompt: string,
    chatContext: vscode.ChatContext,
    stream: vscode.ChatResponseStream,
    _token: vscode.CancellationToken,
): Promise<vscode.ChatResult> {
    const query = prompt || buildQueryFromHistory(chatContext);

    if (!query) {
        stream.markdown(
            'Please provide a query. Example:\n\n' +
            '`@keepcontext what is the authentication flow?`',
        );
        return { metadata: { command: 'recall' } };
    }

    stream.progress('Searching project memories...');

    const results = await client.queryContext({ query, top_k: 5 });

    if (results.length === 0) {
        stream.markdown('No matching memories found. Store some context first!');
        return { metadata: { command: 'recall' } };
    }

    stream.markdown('## Relevant Project Context\n\n');

    for (const result of results) {
        const entry = result.entry;
        const score = (result.score * 100).toFixed(0);
        const typeLabel = entry.memory_type.charAt(0).toUpperCase() + entry.memory_type.slice(1);
        const date = new Date(entry.created_at).toLocaleDateString();

        stream.markdown(
            `### ${typeLabel} — ${score}% match\n` +
            `*Stored ${date}*\n\n` +
            `${entry.content}\n\n---\n\n`,
        );
    }

    stream.markdown(
        `*${results.length} memories retrieved. ` +
        `Use \`@keepcontext /remember <text>\` to store new context.*`,
    );

    return { metadata: { command: 'recall' } };
}

// ---------------------------------------------------------------------------
// /remember — Store a new memory
// ---------------------------------------------------------------------------

async function handleRemember(
    client: ApiClient,
    prompt: string,
    stream: vscode.ChatResponseStream,
): Promise<vscode.ChatResult> {
    if (!prompt) {
        stream.markdown(
            'Please provide text to remember. Example:\n\n' +
            '`@keepcontext /remember We use JWT tokens for auth with 1h expiry`',
        );
        return { metadata: { command: 'remember' } };
    }

    stream.progress('Storing memory...');

    const entry = await client.storeMemory({
        content: prompt,
        memory_type: 'documentation',
        metadata: { source: 'copilot-chat' },
    });

    stream.markdown(
        `**Memory stored** (ID: \`${entry.id}\`)\n\n` +
        `> ${prompt}\n\n` +
        `This context is now available across all chat sessions.`,
    );

    return { metadata: { command: 'remember' } };
}

// ---------------------------------------------------------------------------
// /ask — Ask with LLM + memory context
// ---------------------------------------------------------------------------

async function handleAsk(
    client: ApiClient,
    prompt: string,
    chatContext: vscode.ChatContext,
    stream: vscode.ChatResponseStream,
    _token: vscode.CancellationToken,
): Promise<vscode.ChatResult> {
    const query = prompt || buildQueryFromHistory(chatContext);

    if (!query) {
        stream.markdown(
            'Please provide a question. Example:\n\n' +
            '`@keepcontext /ask how does the memory service work?`',
        );
        return { metadata: { command: 'ask' } };
    }

    stream.progress('Thinking with project context...');

    const response = await client.ask({ query, top_k: 5, use_llm: true });

    if (response.llm_response) {
        stream.markdown(response.llm_response);

        if (response.memory_results.length > 0) {
            stream.markdown('\n\n---\n\n*Sources used:*\n');
            for (const r of response.memory_results) {
                const preview = r.entry.content.substring(0, 80).replace(/\n/g, ' ');
                stream.markdown(`- ${preview}...\n`);
            }
        }
    } else {
        // No LLM response, fall back to showing raw context
        stream.markdown('*LLM unavailable — showing raw context:*\n\n');
        for (const r of response.memory_results) {
            stream.markdown(`${r.entry.content}\n\n---\n\n`);
        }
    }

    return { metadata: { command: 'ask' } };
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Build a query string from the last user turn in chat history. */
function buildQueryFromHistory(chatContext: vscode.ChatContext): string {
    const turns = chatContext.history;
    for (let i = turns.length - 1; i >= 0; i--) {
        const turn = turns[i];
        if (turn instanceof vscode.ChatRequestTurn) {
            return turn.prompt;
        }
    }
    return '';
}
