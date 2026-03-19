/**
 * TreeView provider for browsing stored memories in the sidebar.
 */

import * as vscode from 'vscode';
import { ApiClient, ApiClientError } from './apiClient';
import type { MemoryEntry } from './types';

// ---------------------------------------------------------------------------
// Tree item
// ---------------------------------------------------------------------------

export class MemoryTreeItem extends vscode.TreeItem {
    constructor(public readonly memory: MemoryEntry) {
        super(
            MemoryTreeItem.label(memory),
            vscode.TreeItemCollapsibleState.None,
        );

        this.id = memory.id;
        this.description = memory.memory_type;
        this.tooltip = new vscode.MarkdownString(
            `**${memory.memory_type}** — ${memory.created_at}\n\n${memory.content}`,
        );
        this.contextValue = 'memoryItem';

        this.iconPath = MemoryTreeItem.icon(memory.memory_type);

        this.command = {
            command: 'keepcontext.showMemoryDetail',
            title: 'Show Memory',
            arguments: [memory],
        };
    }

    private static label(m: MemoryEntry): string {
        const max = 60;
        const text = m.content.replace(/\n/g, ' ').trim();
        return text.length > max ? text.substring(0, max) + '…' : text;
    }

    private static icon(type: string): vscode.ThemeIcon {
        switch (type) {
            case 'decision':
                return new vscode.ThemeIcon('law');
            case 'code':
                return new vscode.ThemeIcon('code');
            case 'documentation':
                return new vscode.ThemeIcon('book');
            case 'conversation':
                return new vscode.ThemeIcon('comment-discussion');
            default:
                return new vscode.ThemeIcon('note');
        }
    }
}

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export class MemoryTreeProvider
    implements vscode.TreeDataProvider<MemoryTreeItem>
{
    private _onDidChange = new vscode.EventEmitter<
        MemoryTreeItem | undefined | void
    >();
    readonly onDidChangeTreeData = this._onDidChange.event;

    private memories: MemoryEntry[] = [];

    constructor(private readonly client: ApiClient) {}

    refresh(): void {
        this._onDidChange.fire();
    }

    getTreeItem(element: MemoryTreeItem): vscode.TreeItem {
        return element;
    }

    async getChildren(): Promise<MemoryTreeItem[]> {
        try {
            const res = await this.client.listMemories(1, 50);
            this.memories = res.data;
            return this.memories.map((m) => new MemoryTreeItem(m));
        } catch (err) {
            if (err instanceof ApiClientError) {
                vscode.window.showWarningMessage(
                    `KeepContext: ${err.message}`,
                );
            }
            return [];
        }
    }
}
