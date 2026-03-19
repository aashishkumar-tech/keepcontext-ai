/**
 * KeepContext AI — VS Code extension entry point.
 *
 * Registers commands, tree views, status bar, and webview panels.
 */

import * as vscode from 'vscode';
import { ApiClient } from './apiClient';
import { registerChatParticipant } from './chatParticipant';
import {
    askQuestion,
    deleteMemory,
    queryContext,
    runAgent,
    showMemoryDetail,
    storeMemory,
    storeSelection,
} from './commands';
import { MemoryTreeProvider, MemoryTreeItem } from './memoryTreeProvider';
import { StatusBar } from './statusBar';

// ---------------------------------------------------------------------------
// Activate
// ---------------------------------------------------------------------------

export function activate(context: vscode.ExtensionContext): void {
    const client = new ApiClient();

    // -- Tree views --
    const memoryTree = new MemoryTreeProvider(client);
    vscode.window.registerTreeDataProvider('keepcontext.memories', memoryTree);

    // -- Status bar --
    const statusBar = new StatusBar(client);
    statusBar.startPolling(30_000);
    context.subscriptions.push({ dispose: () => statusBar.dispose() });

    // -- Register commands --
    const commands: Array<[string, (...args: unknown[]) => Promise<void> | void]> = [
        ['keepcontext.storeMemory', () => storeMemory(client, memoryTree)],
        ['keepcontext.storeSelection', () => storeSelection(client, memoryTree)],
        ['keepcontext.queryContext', () => queryContext(client)],
        ['keepcontext.askQuestion', () => askQuestion(client)],
        ['keepcontext.runAgent', () => runAgent(client)],
        ['keepcontext.refreshMemories', () => memoryTree.refresh()],
        [
            'keepcontext.deleteMemory',
            (item: unknown) => {
                if (item instanceof MemoryTreeItem) {
                    return deleteMemory(client, memoryTree, item.memory);
                }
            },
        ],
        [
            'keepcontext.showMemoryDetail',
            (memory: unknown) => {
                if (memory && typeof memory === 'object' && 'id' in memory) {
                    return showMemoryDetail(memory as import('./types').MemoryEntry);
                }
            },
        ],
    ];

    for (const [id, handler] of commands) {
        context.subscriptions.push(
            vscode.commands.registerCommand(id, handler),
        );
    }

    // -- Copilot Chat Participant (@keepcontext) --
    registerChatParticipant(context, client);

    // -- Initial output --
    const outputChannel = vscode.window.createOutputChannel('KeepContext AI');
    outputChannel.appendLine('KeepContext AI extension activated');
    context.subscriptions.push(outputChannel);
}

// ---------------------------------------------------------------------------
// Deactivate
// ---------------------------------------------------------------------------

export function deactivate(): void {
    // cleanup handled by disposables
}
