/**
 * Status bar item showing KeepContext AI connection status.
 */

import * as vscode from 'vscode';
import { ApiClient, ApiClientError } from './apiClient';

export class StatusBar {
    private readonly item: vscode.StatusBarItem;
    private timer: NodeJS.Timeout | undefined;

    constructor(private readonly client: ApiClient) {
        this.item = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            100,
        );
        this.item.command = 'keepcontext.queryContext';
        this.item.show();
    }

    /** Start periodic health checks. */
    startPolling(intervalMs: number = 30_000): void {
        this.check(); // immediate first check
        this.timer = setInterval(() => this.check(), intervalMs);
    }

    /** Stop polling and dispose the status bar item. */
    dispose(): void {
        if (this.timer) {
            clearInterval(this.timer);
        }
        this.item.dispose();
    }

    private async check(): Promise<void> {
        try {
            const health = await this.client.health();
            this.item.text = `$(check) KeepContext AI`;
            this.item.tooltip = `Connected — v${health.version} • ChromaDB: ${health.chromadb}`;
            this.item.backgroundColor = undefined;
        } catch (err) {
            this.item.text = `$(warning) KeepContext AI`;
            this.item.tooltip =
                err instanceof ApiClientError
                    ? `Disconnected: ${err.message}`
                    : 'Disconnected';
            this.item.backgroundColor = new vscode.ThemeColor(
                'statusBarItem.warningBackground',
            );
        }
    }
}
